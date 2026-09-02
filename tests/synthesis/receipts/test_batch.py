"""Unit tests for the resumable receipt batch runner (FDD #28 v0.4).

Covers the four properties the runner exists to guarantee:

  * a batch of N writes N distinct sample ids and N manifest lines,
  * a restart resumes — completed work is skipped, the manifest is not
    duplicated, and a torn final line does not crash the read,
  * one worker exception is collected, not fatal to the batch,
  * the plan is a pure function of ``(n, seed)``.

The WeasyPrint render is stubbed in most tests: it costs ~0.4s per sample and
none of the properties above depend on what the pixels look like. One test
deliberately does *not* stub it, because the spawn-context process pool can only
be verified against real, picklable work.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from document_simulator.synthesis.receipts import batch as batch_module
from document_simulator.synthesis.receipts.batch import (
    BatchProgress,
    SynthesisOutcome,
    plan_batch,
    read_manifest,
    run_batch,
)
from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    ImageGroundTruth,
    LineItem,
    Receipt,
    TokenGroundTruth,
)

# ---------------------------------------------------------------------------
# Stub pipeline
# ---------------------------------------------------------------------------


def _fake_outcome(seed: int, sample_id: str) -> SynthesisOutcome:
    """A minimal but schema-valid stand-in for a real render."""
    image = Image.new("RGB", (24, 32), color=(255, 255, 255))
    receipt = Receipt(
        merchant="STUB MART",
        address="1 Test Way, Springfield",
        items=[LineItem(sku="STUB-1", qty=1, unit_price=1.00)],
        tax_rate=0.05,
        payment_last4="0000",
    )
    gt = ImageGroundTruth(
        image_id=sample_id,
        image_path=Path(f"images/{sample_id}.png"),
        image_size=image.size,
        tokens=[
            TokenGroundTruth(
                token_id="merchant",
                text="STUB MART",
                coords=[CoordSnapshot(stage="raster", polygon=[(0, 0), (10, 0), (10, 5), (0, 5)])],
            )
        ],
        receipt=receipt,
        seed=seed,
        pipeline_version="test",
    )
    return SynthesisOutcome(image=image, ground_truth=gt, stages=(), stage_images={"raster": image})


@pytest.fixture
def stub_pipeline(monkeypatch):
    """Replace ``synthesize_one`` with a cheap stub; yields a call recorder.

    ``_run_task`` looks the function up on the module at call time, so patching
    the module attribute is enough. This only works in the in-process
    (``workers=1``) path — a spawned worker re-imports the module and would see
    the real function — which is why the pool test below uses real renders.
    """
    calls: list[str] = []
    fail_indices: set[int] = set()

    def _fake_synthesize_one(
        seed, *, spec=None, template=None, augraphy_preset=None, sample_id=None
    ):
        calls.append(sample_id)
        index = int(sample_id.split("-")[1])
        if index in fail_indices:
            raise RuntimeError(f"boom on sample {index}")
        return _fake_outcome(seed, sample_id)

    monkeypatch.setattr(batch_module, "synthesize_one", _fake_synthesize_one)
    _fake_synthesize_one.calls = calls  # type: ignore[attr-defined]
    _fake_synthesize_one.fail_indices = fail_indices  # type: ignore[attr-defined]
    return _fake_synthesize_one


def _manifest_lines(out_dir: Path) -> list[str]:
    """Raw non-empty manifest lines, so duplicates are visible."""
    path = out_dir / "manifest.jsonl"
    if not path.is_file():
        return []
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# N samples -> N ids, N manifest lines
# ---------------------------------------------------------------------------


def test_batch_writes_n_distinct_samples(tmp_path, stub_pipeline) -> None:
    """A batch of N produces N distinct ids, N images, N GT files, N manifest lines."""
    result = run_batch(3, seed=7, out_dir=tmp_path, workers=1)

    assert result.n_written == 3, f"expected 3 written, got {result.n_written}"
    assert result.n_failed == 0, f"unexpected failures: {result.failures}"
    assert len(set(result.image_ids)) == 3, f"sample ids not distinct: {result.image_ids}"

    assert len(_manifest_lines(tmp_path)) == 3, "manifest must have exactly one line per sample"
    assert sorted(p.name for p in (tmp_path / "images").iterdir()) == sorted(
        f"{sid}.png" for sid in result.image_ids
    )
    assert len(list((tmp_path / "ground_truth").iterdir())) == 3

    # Every manifest line points at a file that is really there.
    for entry in read_manifest(tmp_path):
        assert (tmp_path / entry["image_path"]).is_file(), f"missing image for {entry['image_id']}"
        assert (tmp_path / entry["gt_path"]).is_file(), f"missing GT for {entry['image_id']}"


def test_progress_callback_reports_every_sample(tmp_path, stub_pipeline) -> None:
    """The progress hook fires once per sample and finishes at 1.0."""
    seen: list[BatchProgress] = []
    run_batch(3, seed=7, out_dir=tmp_path, workers=1, progress=seen.append)

    assert len(seen) == 3, f"expected 3 progress callbacks, got {len(seen)}"
    assert [p.done for p in seen] == [1, 2, 3], f"progress not monotonic: {[p.done for p in seen]}"
    assert seen[-1].fraction == 1.0


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------


def test_resume_skips_completed_work_without_duplicating_manifest(tmp_path, stub_pipeline) -> None:
    """After a partial run, a rerun regenerates only the missing samples."""
    # First attempt: samples 2 and 3 blow up, so only 0 and 1 land on disk.
    stub_pipeline.fail_indices.update({2, 3})
    first = run_batch(4, seed=42, out_dir=tmp_path, workers=1)
    assert first.n_written == 2 and first.n_failed == 2, f"setup wrong: {first}"
    assert len(_manifest_lines(tmp_path)) == 2

    # Second attempt: the fault is fixed, the run is restarted identically.
    stub_pipeline.fail_indices.clear()
    stub_pipeline.calls.clear()
    second = run_batch(4, seed=42, out_dir=tmp_path, workers=1)

    assert second.n_skipped == 2, f"expected 2 resumed samples, got {second.n_skipped}"
    assert second.n_written == 2, f"expected 2 newly written, got {second.n_written}"
    assert second.n_failed == 0, f"unexpected failures: {second.failures}"

    # The completed samples were not re-rendered...
    assert set(stub_pipeline.calls) == set(second.image_ids), (
        "resume re-rendered work that was already on disk: "
        f"called {stub_pipeline.calls}, expected only {second.image_ids}"
    )
    # ...and the manifest has exactly one line per sample, not five or six.
    lines = _manifest_lines(tmp_path)
    ids = [json.loads(ln)["image_id"] for ln in lines]
    assert len(lines) == 4, f"expected 4 manifest lines after resume, got {len(lines)}"
    assert len(set(ids)) == 4, f"duplicate manifest entries: {ids}"


def test_resume_tolerates_torn_final_manifest_line(tmp_path, stub_pipeline) -> None:
    """A half-written last line (SIGKILL mid-append) must not break the resume."""
    run_batch(2, seed=3, out_dir=tmp_path, workers=1)
    manifest = tmp_path / "manifest.jsonl"

    # Simulate the process dying part-way through appending a third entry.
    with manifest.open("a", encoding="utf-8") as fh:
        fh.write('{"image_id": "00000003-000002-abc", "image_pa')

    entries = read_manifest(tmp_path)
    assert len(entries) == 2, f"torn line should be dropped, got {len(entries)} entries"

    # And the batch that owns that torn sample regenerates it rather than
    # trusting the partial record.
    stub_pipeline.calls.clear()
    result = run_batch(3, seed=3, out_dir=tmp_path, workers=1)
    assert result.n_skipped == 2, f"expected the 2 intact samples to resume, got {result.n_skipped}"
    assert result.n_written == 1, f"expected the torn sample to be regenerated, got {result}"


def test_resume_regenerates_when_image_file_is_missing(tmp_path, stub_pipeline) -> None:
    """A manifest line whose image was deleted does not count as completed."""
    first = run_batch(2, seed=5, out_dir=tmp_path, workers=1)
    (tmp_path / "images" / f"{first.image_ids[0]}.png").unlink()

    second = run_batch(2, seed=5, out_dir=tmp_path, workers=1)
    assert second.n_written == 1, f"deleted sample should be regenerated: {second}"
    assert second.n_skipped == 1


def test_resume_disabled_regenerates_everything(tmp_path, stub_pipeline) -> None:
    """``resume=False`` is an explicit full redo."""
    run_batch(2, seed=9, out_dir=tmp_path, workers=1)
    again = run_batch(2, seed=9, out_dir=tmp_path, workers=1, resume=False)

    assert again.n_written == 2 and again.n_skipped == 0, f"resume=False did not redo: {again}"


# ---------------------------------------------------------------------------
# Failure isolation
# ---------------------------------------------------------------------------


def test_worker_exception_is_collected_not_fatal(tmp_path, stub_pipeline) -> None:
    """One bad sample is reported; the other three still make it to disk."""
    stub_pipeline.fail_indices.add(1)
    result = run_batch(4, seed=13, out_dir=tmp_path, workers=1)

    assert result.n_written == 3, f"a single failure aborted the batch: {result}"
    assert result.n_failed == 1, f"expected exactly 1 failure, got {result.n_failed}"
    assert result.ok is False

    failure = result.failures[0]
    assert failure.index == 1, f"wrong sample blamed: {failure}"
    assert "boom on sample 1" in failure.error, f"error message lost: {failure.error}"
    assert "RuntimeError" in failure.traceback, "traceback not captured for diagnosis"

    # The failed sample left no manifest line behind.
    assert len(_manifest_lines(tmp_path)) == 3
    assert failure.sample_id not in {e["image_id"] for e in read_manifest(tmp_path)}


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_plan_is_deterministic_for_same_n_and_seed(tmp_path) -> None:
    """Same (n, seed) -> same spec_ids, sample_ids, seeds and templates."""
    a = plan_batch(4, 21, tmp_path)
    b = plan_batch(4, 21, tmp_path)

    assert [t.spec.spec_id for t in a] == [t.spec.spec_id for t in b]
    assert [t.sample_id for t in a] == [t.sample_id for t in b]
    assert [t.seed for t in a] == [t.seed for t in b]
    assert [t.template for t in a] == [t.template for t in b]


def test_plan_differs_across_seeds(tmp_path) -> None:
    """A different batch seed must not replay the same layouts."""
    a = plan_batch(4, 21, tmp_path)
    b = plan_batch(4, 22, tmp_path)

    assert [t.spec.spec_id for t in a] != [t.spec.spec_id for t in b], (
        "different seeds produced identical layout specs — the batch seed is not "
        "reaching the sampler"
    )
    assert [t.seed for t in a] != [t.seed for t in b]


def test_plan_rejects_unknown_template(tmp_path) -> None:
    """An unknown template id fails at plan time, not N renders later."""
    with pytest.raises(ValueError, match="Unknown template"):
        plan_batch(2, 0, tmp_path, template="NOT_A_TEMPLATE")


def test_zero_and_negative_n_are_no_ops(tmp_path, stub_pipeline) -> None:
    """``n <= 0`` produces an empty plan rather than an error or a stray file."""
    assert plan_batch(0, 1, tmp_path) == []
    result = run_batch(0, seed=1, out_dir=tmp_path, workers=1)
    assert result.n_requested == 0 and result.n_written == 0
    assert _manifest_lines(tmp_path) == []


# ---------------------------------------------------------------------------
# Process pool (real renders — the only way to exercise spawn + pickling)
# ---------------------------------------------------------------------------


def test_process_pool_path_persists_samples(tmp_path) -> None:
    """``workers>1`` really runs through a spawn-context pool and writes samples.

    Not stubbed on purpose: a spawned worker re-imports the module, so a
    monkeypatched stub would be invisible and this test would prove nothing
    about the thing most likely to break — whether ``SampleTask`` and
    ``_run_task`` survive pickling into a fresh interpreter.
    """
    result = run_batch(2, seed=101, out_dir=tmp_path, workers=2, max_tasks_per_child=1)

    assert result.n_failed == 0, f"pool run failed: {[f.error for f in result.failures]}"
    assert result.n_written == 2
    assert len(_manifest_lines(tmp_path)) == 2
    for sample_id in result.image_ids:
        assert (tmp_path / "images" / f"{sample_id}.png").is_file()


def test_pool_and_serial_paths_agree(tmp_path) -> None:
    """The same (n, seed) yields the same sample ids however it is executed."""
    serial = run_batch(2, seed=101, out_dir=tmp_path / "serial", workers=1)
    pooled = run_batch(2, seed=101, out_dir=tmp_path / "pooled", workers=2)

    assert sorted(serial.image_ids) == sorted(
        pooled.image_ids
    ), "worker count changed the sample plan — batch output must depend only on (n, seed)"
