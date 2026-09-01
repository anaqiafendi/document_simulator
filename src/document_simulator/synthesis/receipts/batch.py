"""Resumable batch runner for the photoreal receipt pipeline (FDD #28, v0.4).

This module owns the *only* orchestration of the receipt pipeline. Both the
batch runner and ``api/routers/receipt_synthesis.py`` call
:func:`synthesize_one`, so the single-sample path exercised by the API is
byte-for-byte the path a 10k-sample dataset run takes.

Pipeline per sample::

    layout (LayoutSpec) -> content (Faker) -> raster (WeasyPrint) -> augraphy?

Design notes
------------
*Process pool.* WeasyPrint (Pango/Cairo) and, later, Blender leak native memory
per render, so workers are recycled via ``max_tasks_per_child``. The pool uses
an explicit ``spawn`` context: ``fork`` is unsafe with the native graphics
stack, and on macOS the default ``spawn`` behaviour must not be left implicit
because it changes what the worker inherits.

*Environment.* WeasyPrint needs ``DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib``
on macOS. ``spawn`` re-executes the interpreter but inherits ``os.environ``, so
setting it for the parent is sufficient.

*Resume.* Sample ids are derived deterministically from ``(seed, index)``, so a
restarted run computes the same plan and can subtract the ids already recorded
in ``manifest.jsonl``. The manifest reader tolerates a torn final line, which is
exactly what a ``SIGKILL`` mid-append leaves behind.

*Failure isolation.* A worker exception is captured into
:class:`SampleFailure` and reported in :class:`BatchResult`; it never aborts the
batch. A worker that dies outright (segfault, OOM) breaks the pool, and every
outstanding future is recorded as a failure rather than propagating.

CLI::

    python -m document_simulator.synthesis.receipts.batch \\
        --n 200 --seed 0 --out data/synthetic/receipts_v0_4 --workers 8
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import sys
import time
import traceback
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from loguru import logger
from PIL import Image

from document_simulator.synthesis.receipts import content as content_module
from document_simulator.synthesis.receipts import render as render_module
from document_simulator.synthesis.receipts.layout.sampler import stratified_specs
from document_simulator.synthesis.receipts.layout.spec import LayoutSpec
from document_simulator.synthesis.receipts.persist import persist_sample
from document_simulator.synthesis.receipts.schema import ImageGroundTruth

BATCH_VERSION = "0.4.0"

#: Recycle a worker after this many renders. WeasyPrint's native allocations are
#: not fully returned to the OS; a fresh interpreter is cheaper than the drift.
DEFAULT_MAX_TASKS_PER_CHILD = 32

#: Upper bound on default worker count — beyond this the WeasyPrint renders
#: contend on memory bandwidth rather than CPU.
_MAX_DEFAULT_WORKERS = 8

MANIFEST_NAME = "manifest.jsonl"


# ---------------------------------------------------------------------------
# Template registry
#
# TODO(integration): the content agent is exporting a single registry from
# ``content.py``. Once it lands, delete the ``_FALLBACK_*`` block below and make
# this an unconditional::
#
#     from document_simulator.synthesis.receipts.content import (
#         TEMPLATE_IDS, template_file_for,
#     )
#
# The router imports these two names from here so there is exactly one registry
# in the process; after integration both callers should import from content.py
# directly and this re-export can go away.
# ---------------------------------------------------------------------------

_FALLBACK_TEMPLATE_FILES: dict[str, str] = {
    "thermal_minimal": "thermal_minimal.html.j2",
    "restaurant_tip": "restaurant_tip.html.j2",
    "retail_multicol": "retail_multicol.html.j2",
    "a4_invoice": "a4_invoice.html.j2",
    "taxi_stub": "taxi_stub.html.j2",
}


def _fallback_template_file_for(template_id: str) -> str:
    """Map a template id to its Jinja2 filename (pre-integration fallback)."""
    try:
        return _FALLBACK_TEMPLATE_FILES[template_id]
    except KeyError:
        valid = ", ".join(sorted(_FALLBACK_TEMPLATE_FILES))
        raise ValueError(f"Unknown template {template_id!r}. Valid templates: {valid}") from None


TEMPLATE_IDS: tuple[str, ...] = tuple(
    getattr(content_module, "TEMPLATE_IDS", tuple(_FALLBACK_TEMPLATE_FILES))
)
template_file_for: Callable[[str], str] = getattr(
    content_module, "template_file_for", _fallback_template_file_for
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StageTiming:
    """One pipeline stage's wall time plus the parameters it was driven by."""

    stage: str
    elapsed_ms: int
    parameters: dict[str, Any]


@dataclass(frozen=True)
class SynthesisOutcome:
    """A single rendered sample, before persistence."""

    image: Image.Image
    ground_truth: ImageGroundTruth
    stages: tuple[StageTiming, ...]
    #: Image as it stood at the end of each pixel-producing stage, keyed by
    #: stage name. The API returns these per stage; the batch runner ignores
    #: everything but ``image`` and drops the dict with the outcome.
    stage_images: dict[str, Image.Image] = field(default_factory=dict)


@dataclass(frozen=True)
class SampleTask:
    """The deterministic plan for one sample. Must stay picklable for ``spawn``."""

    index: int
    sample_id: str
    seed: int
    spec: LayoutSpec
    template: str
    out_dir: Path
    augraphy_preset: str | None


@dataclass(frozen=True)
class SampleFailure:
    """A sample that did not make it to disk, and why."""

    index: int
    sample_id: str
    seed: int
    spec_id: str
    error: str
    traceback: str = ""


@dataclass(frozen=True)
class SampleSuccess:
    """A sample that was written to disk."""

    index: int
    sample_id: str
    seed: int
    spec_id: str
    elapsed_ms: int


@dataclass(frozen=True)
class BatchProgress:
    """Snapshot handed to the optional ``progress`` callback after each sample."""

    done: int
    total: int
    n_written: int
    n_failed: int

    @property
    def fraction(self) -> float:
        """Completed fraction in ``[0.0, 1.0]``; 1.0 when there is nothing to do."""
        return 1.0 if self.total == 0 else self.done / self.total


@dataclass
class BatchResult:
    """Outcome of one :func:`run_batch` call."""

    n_requested: int
    n_written: int
    n_skipped: int
    n_failed: int
    out_dir: Path
    seed: int
    elapsed_s: float
    written: list[SampleSuccess] = field(default_factory=list)
    skipped_ids: list[str] = field(default_factory=list)
    failures: list[SampleFailure] = field(default_factory=list)
    batch_version: str = BATCH_VERSION

    @property
    def image_ids(self) -> list[str]:
        """Sample ids written by *this* run, in completion order."""
        return [s.sample_id for s in self.written]

    @property
    def ok(self) -> bool:
        """True when every planned sample either was written or already existed."""
        return self.n_failed == 0


# ---------------------------------------------------------------------------
# Deterministic planning
# ---------------------------------------------------------------------------


def derive_sample_seed(seed: int, index: int) -> int:
    """Derive a per-sample content seed from the batch seed and sample index.

    Hashed rather than ``seed + index`` so that two batches with nearby seeds do
    not produce overlapping content, and stable across processes and runs
    (unlike ``hash()``, which is salted).
    """
    digest = hashlib.sha256(f"{seed}:{index}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def sample_id_for(seed: int, index: int, spec: LayoutSpec) -> str:
    """Build the stable on-disk id for one planned sample.

    Encodes the batch seed and index (so resume can recompute it without reading
    anything) and the ``spec_id`` (so a directory listing is greppable by
    layout). Unique within a batch because ``index`` is.
    """
    return f"{seed:08d}-{index:06d}-{spec.spec_id}"


def plan_batch(
    n: int,
    seed: int,
    out_dir: Path,
    *,
    template: str | None = None,
    augraphy_preset: str | None = None,
) -> list[SampleTask]:
    """Compute the full, deterministic task list for a batch.

    Pure: no I/O beyond loading the layout prior. ``plan_batch(n, seed, ...)``
    returns the same ``sample_id`` / ``spec_id`` sequence on every call and in
    every process, which is what makes resume and reproducibility work.

    Args:
        n: Number of samples.
        seed: Batch seed.
        out_dir: Dataset root each task will persist into.
        template: Pin every sample to one template id. When ``None``, a template
            is drawn deterministically per sample from :data:`TEMPLATE_IDS`.
        augraphy_preset: Preset applied after raster, or ``None`` to skip.

    Returns:
        Exactly ``max(n, 0)`` tasks.
    """
    if n <= 0:
        return []
    if template is not None and template not in TEMPLATE_IDS:
        raise ValueError(f"Unknown template {template!r}. Valid: {sorted(TEMPLATE_IDS)}")

    specs = stratified_specs(n, seed)
    tasks: list[SampleTask] = []
    for index, spec in enumerate(specs):
        sample_seed = derive_sample_seed(seed, index)
        chosen = template or TEMPLATE_IDS[sample_seed % len(TEMPLATE_IDS)]
        tasks.append(
            SampleTask(
                index=index,
                sample_id=sample_id_for(seed, index, spec),
                seed=sample_seed,
                spec=spec,
                template=chosen,
                out_dir=Path(out_dir),
                augraphy_preset=augraphy_preset,
            )
        )
    return tasks


# ---------------------------------------------------------------------------
# Manifest / resume
# ---------------------------------------------------------------------------


def read_manifest(out_dir: Path | str) -> list[dict[str, Any]]:
    """Read ``manifest.jsonl``, tolerating a torn final line.

    A run killed mid-append leaves a line without its trailing newline (and
    possibly truncated JSON). That line's sample is *not* trustworthy — its
    image and GT may also be partial — so it is dropped with a warning and the
    sample gets regenerated on resume, overwriting the partial artifacts.

    Returns:
        Parsed manifest entries in file order. Empty when the manifest is absent.
    """
    manifest_path = Path(out_dir) / MANIFEST_NAME
    if not manifest_path.is_file():
        return []

    entries: list[dict[str, Any]] = []
    with manifest_path.open("r", encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            if not raw.endswith("\n"):
                # No terminator => the process died mid-write. Always the last line.
                logger.warning(
                    f"{manifest_path}: line {lineno} has no trailing newline "
                    f"(interrupted run); ignoring it so the sample is regenerated"
                )
                continue
            line = raw.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning(f"{manifest_path}: line {lineno} is not valid JSON ({exc}); skipped")
                continue
            if isinstance(entry, dict) and isinstance(entry.get("image_id"), str):
                entries.append(entry)
            else:
                logger.warning(f"{manifest_path}: line {lineno} has no string image_id; skipped")
    return entries


def completed_sample_ids(out_dir: Path | str) -> set[str]:
    """Sample ids that are fully on disk (manifest line *and* image file).

    ``persist_sample`` appends the manifest line last, so a line implies the
    image and GT were written. The extra ``is_file`` check additionally catches
    a dataset whose images were deleted or partially copied.
    """
    root = Path(out_dir)
    done: set[str] = set()
    for entry in read_manifest(root):
        image_id = entry["image_id"]
        rel = entry.get("image_path") or f"images/{image_id}.png"
        if (root / rel).is_file():
            done.add(image_id)
        else:
            logger.warning(
                f"manifest lists {image_id} but {root / rel} is missing; will regenerate"
            )
    return done


# ---------------------------------------------------------------------------
# Single-sample orchestration (shared with the API router)
# ---------------------------------------------------------------------------


def _accepts(func: Any, name: str) -> bool:
    """True when ``func`` declares a parameter called ``name``.

    TODO(integration): this shim lets Stage 6 land while ``content.make_receipt``
    and ``render.render_receipt`` are still being converted to spec-driven
    signatures by sibling agents. Once both accept ``spec=``, delete
    ``_accepts`` and call them directly.
    """
    try:
        return name in inspect.signature(func).parameters
    except (TypeError, ValueError):  # builtins / C callables
        return False


def _elapsed_ms(start: float) -> int:
    """Milliseconds since a ``perf_counter`` timestamp."""
    return int((time.perf_counter() - start) * 1000)


def synthesize_one(
    seed: int,
    *,
    spec: LayoutSpec | None = None,
    template: str | None = None,
    augraphy_preset: str | None = None,
    sample_id: str | None = None,
) -> SynthesisOutcome:
    """Run layout -> content -> raster -> augraphy for one sample.

    The single orchestration point for the receipt pipeline: the ``/render``
    endpoint and the batch worker both go through here, so an API preview and a
    dataset sample generated from the same ``(seed, spec, template)`` are
    identical.

    Args:
        seed: Content seed. Same seed + spec + template -> same sample.
        spec: Layout to render. When ``None`` one is drawn deterministically
            from ``seed`` via ``stratified_specs(1, seed)``.
        template: Template id. Defaults to a deterministic draw from
            :data:`TEMPLATE_IDS`.
        augraphy_preset: Preset applied after raster; ``None`` skips the stage.
        sample_id: Override the ground truth's ``image_id`` / ``image_path``.
            The batch runner passes its deterministic id so resume can match.

    Returns:
        A :class:`SynthesisOutcome` carrying the final image, the ground truth
        and one :class:`StageTiming` per executed stage.
    """
    stages: list[StageTiming] = []
    stage_images: dict[str, Image.Image] = {}

    # --- layout -------------------------------------------------------------
    t_layout = time.perf_counter()
    if spec is None:
        spec = stratified_specs(1, seed)[0]
    if template is None:
        template = TEMPLATE_IDS[seed % len(TEMPLATE_IDS)]
    stages.append(
        StageTiming(
            stage="layout",
            elapsed_ms=_elapsed_ms(t_layout),
            parameters={
                "spec_id": spec.spec_id,
                "blocks": [b.value for b in spec.blocks],
                "money_rows": [r.value for r in spec.money_rows],
                "perturbed": list(spec.perturbed),
            },
        )
    )

    # --- content ------------------------------------------------------------
    t_content = time.perf_counter()
    # Deliberately Any: the signature is the thing `_accepts` probes, so a
    # static check against whichever variant currently sits in content.py would
    # flag the branch that is not taken. Remove with the shim.
    make_receipt: Any = content_module.make_receipt
    if _accepts(make_receipt, "spec"):
        receipt = make_receipt(seed=seed, template=template, spec=spec)
    else:
        receipt = make_receipt(seed=seed, template=template)
    stages.append(
        StageTiming(
            stage="content",
            elapsed_ms=_elapsed_ms(t_content),
            parameters={
                "template": template,
                "seed": seed,
                "n_items": len(receipt.items),
                "tax_rate": receipt.tax_rate,
            },
        )
    )

    # --- raster -------------------------------------------------------------
    t_raster = time.perf_counter()
    template_file = template_file_for(template)
    render_receipt: Any = render_module.render_receipt
    render_kwargs: dict[str, Any] = {"seed": seed, "template_name": template_file}
    if _accepts(render_receipt, "spec"):
        render_kwargs["spec"] = spec
    image, ground_truth = render_receipt(receipt, **render_kwargs)
    stage_images["raster"] = image
    stages.append(
        StageTiming(
            stage="raster",
            elapsed_ms=_elapsed_ms(t_raster),
            parameters={
                "template_file": template_file,
                "image_size": list(image.size),
                "n_tokens": len(ground_truth.tokens),
            },
        )
    )

    # --- augraphy (optional) ------------------------------------------------
    if augraphy_preset is not None:
        # Imported lazily: pulls in augraphy + OpenCV, which costs ~1s and is
        # pure waste for the (common) no-degradation path.
        from document_simulator.synthesis.receipts.augraphy_pretreat import apply_post_render

        t_aug = time.perf_counter()
        image = apply_post_render(image, preset=augraphy_preset, seed=seed)
        stage_images["augraphy"] = image
        stages.append(
            StageTiming(
                stage="augraphy",
                elapsed_ms=_elapsed_ms(t_aug),
                parameters={"preset": augraphy_preset, "seed": seed},
            )
        )

    if sample_id is not None:
        ground_truth = ground_truth.model_copy(
            update={"image_id": sample_id, "image_path": Path(f"images/{sample_id}.png")}
        )

    return SynthesisOutcome(
        image=image,
        ground_truth=ground_truth,
        stages=tuple(stages),
        stage_images=stage_images,
    )


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


def _run_task(task: SampleTask) -> SampleSuccess | SampleFailure:
    """Render and persist one sample. Never raises — the pool must survive it.

    Top-level (not a closure) so ``spawn`` can pickle it by qualified name.
    """
    started = time.perf_counter()
    try:
        outcome = synthesize_one(
            task.seed,
            spec=task.spec,
            template=task.template,
            augraphy_preset=task.augraphy_preset,
            sample_id=task.sample_id,
        )
        persist_sample(outcome.image, outcome.ground_truth, task.out_dir)
    except Exception as exc:  # noqa: BLE001 — deliberate: isolate worker failures
        logger.error(f"sample {task.sample_id} failed: {type(exc).__name__}: {exc}")
        return SampleFailure(
            index=task.index,
            sample_id=task.sample_id,
            seed=task.seed,
            spec_id=task.spec.spec_id,
            error=f"{type(exc).__name__}: {exc}",
            traceback=traceback.format_exc(),
        )
    return SampleSuccess(
        index=task.index,
        sample_id=task.sample_id,
        seed=task.seed,
        spec_id=task.spec.spec_id,
        elapsed_ms=int((time.perf_counter() - started) * 1000),
    )


def default_workers() -> int:
    """Worker count to use when the caller does not pick one."""
    return max(1, min(os.cpu_count() or 1, _MAX_DEFAULT_WORKERS))


# ---------------------------------------------------------------------------
# Batch driver
# ---------------------------------------------------------------------------


def run_batch(
    n: int,
    seed: int,
    out_dir: Path | str,
    *,
    workers: int | None = None,
    augraphy_preset: str | None = None,
    template: str | None = None,
    resume: bool = True,
    max_tasks_per_child: int = DEFAULT_MAX_TASKS_PER_CHILD,
    progress: Callable[[BatchProgress], None] | None = None,
) -> BatchResult:
    """Generate ``n`` receipt samples into ``out_dir``, resumably.

    Args:
        n: Number of samples in the batch. The plan is a function of
            ``(n, seed)`` only, so re-running with the same pair resumes the
            same batch rather than appending a different one.
        seed: Batch seed.
        out_dir: Dataset root. ``images/``, ``ground_truth/`` and
            ``manifest.jsonl`` are created under it.
        workers: Process count. ``None`` -> :func:`default_workers`. ``1`` runs
            in-process (no pool), which is both faster for tiny batches and the
            only mode in which monkeypatched stubs are visible to the worker.
        augraphy_preset: Applied to every sample after raster, or ``None``.
        template: Pin all samples to one template id; ``None`` spreads them
            deterministically across :data:`TEMPLATE_IDS`.
        resume: When True (default), samples already recorded in the manifest
            are skipped. Set False to force a full regeneration.
        max_tasks_per_child: Renders per worker process before it is replaced.
            Bounds the native memory WeasyPrint does not give back.
        progress: Optional callback invoked with a :class:`BatchProgress` after
            each sample completes. Runs in the parent process.

    Returns:
        A :class:`BatchResult`. Worker failures are collected there, not raised
        — inspect ``result.failures`` (or ``result.ok``) to react to them.
    """
    started = time.perf_counter()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks = plan_batch(n, seed, out_dir, template=template, augraphy_preset=augraphy_preset)

    already_done = completed_sample_ids(out_dir) if resume else set()
    skipped = [t.sample_id for t in tasks if t.sample_id in already_done]
    pending = [t for t in tasks if t.sample_id not in already_done]

    n_workers = default_workers() if workers is None else max(1, workers)
    logger.info(
        f"run_batch: n={n} seed={seed} out={out_dir} workers={n_workers} "
        f"preset={augraphy_preset!r} template={template!r} "
        f"pending={len(pending)} resumed={len(skipped)}"
    )

    written: list[SampleSuccess] = []
    failures: list[SampleFailure] = []

    def _record(outcome: SampleSuccess | SampleFailure) -> None:
        if isinstance(outcome, SampleSuccess):
            written.append(outcome)
        else:
            failures.append(outcome)
        if progress is not None:
            progress(
                BatchProgress(
                    done=len(written) + len(failures),
                    total=len(pending),
                    n_written=len(written),
                    n_failed=len(failures),
                )
            )

    if pending:
        if n_workers == 1:
            for task in pending:
                _record(_run_task(task))
        else:
            _record_pool(pending, n_workers, max_tasks_per_child, _record)

    result = BatchResult(
        n_requested=len(tasks),
        n_written=len(written),
        n_skipped=len(skipped),
        n_failed=len(failures),
        out_dir=out_dir,
        seed=seed,
        elapsed_s=round(time.perf_counter() - started, 3),
        written=sorted(written, key=lambda s: s.index),
        skipped_ids=skipped,
        failures=sorted(failures, key=lambda f: f.index),
    )
    logger.info(
        f"run_batch done: written={result.n_written} skipped={result.n_skipped} "
        f"failed={result.n_failed} in {result.elapsed_s}s"
    )
    if failures:
        for failure in result.failures[:10]:
            logger.warning(f"  sample {failure.sample_id}: {failure.error}")
        if len(failures) > 10:
            logger.warning(f"  ... and {len(failures) - 10} more failures")
    return result


def _record_pool(
    pending: list[SampleTask],
    n_workers: int,
    max_tasks_per_child: int,
    record: Callable[[SampleSuccess | SampleFailure], None],
) -> None:
    """Fan ``pending`` out over a spawn-context process pool, recording outcomes.

    ``_run_task`` already swallows per-sample exceptions, so a future only
    raises when the worker process itself dies (segfault, OOM kill) — which
    breaks the whole pool. Those futures are turned into failures so the caller
    still gets a report instead of a traceback.
    """
    pool_kwargs: dict[str, Any] = {"max_workers": n_workers, "mp_context": get_context("spawn")}
    if sys.version_info >= (3, 11):
        pool_kwargs["max_tasks_per_child"] = max_tasks_per_child
    else:
        # Without worker recycling a long batch will grow until the OS complains.
        logger.warning(
            "max_tasks_per_child needs Python 3.11+; workers will not be recycled and "
            "WeasyPrint's native allocations will accumulate over a long batch"
        )

    with ProcessPoolExecutor(**pool_kwargs) as pool:
        futures = {pool.submit(_run_task, task): task for task in pending}
        for future in as_completed(futures):
            task = futures[future]
            try:
                record(future.result())
            except Exception as exc:  # noqa: BLE001 — worker process died
                logger.error(f"worker died on sample {task.sample_id}: {exc}")
                record(
                    SampleFailure(
                        index=task.index,
                        sample_id=task.sample_id,
                        seed=task.seed,
                        spec_id=task.spec.spec_id,
                        error=f"worker process failed: {type(exc).__name__}: {exc}",
                        traceback=traceback.format_exc(),
                    )
                )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli_main(argv: list[str] | None = None) -> int:
    """CLI entry: ``python -m document_simulator.synthesis.receipts.batch``."""
    parser = argparse.ArgumentParser(
        prog="document_simulator.synthesis.receipts.batch",
        description="Generate a resumable batch of synthetic receipt samples.",
    )
    parser.add_argument("--n", type=int, required=True, help="Number of samples to generate")
    parser.add_argument("--seed", type=int, default=0, help="Batch seed (default: 0)")
    parser.add_argument("--out", type=Path, required=True, help="Dataset root directory")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Worker processes (default: min(cpu_count, {_MAX_DEFAULT_WORKERS}); 1 = in-process)",
    )
    parser.add_argument(
        "--augraphy-preset",
        default=None,
        help="Augraphy preset applied to every sample (default: none)",
    )
    parser.add_argument(
        "--template",
        default=None,
        help=f"Pin all samples to one template id. One of: {', '.join(sorted(TEMPLATE_IDS))}",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Regenerate samples already present in the manifest",
    )
    parser.add_argument(
        "--max-tasks-per-child",
        type=int,
        default=DEFAULT_MAX_TASKS_PER_CHILD,
        help=f"Renders per worker before recycling (default: {DEFAULT_MAX_TASKS_PER_CHILD})",
    )
    args = parser.parse_args(argv)

    result = run_batch(
        args.n,
        args.seed,
        args.out,
        workers=args.workers,
        augraphy_preset=args.augraphy_preset,
        template=args.template,
        resume=not args.no_resume,
        max_tasks_per_child=args.max_tasks_per_child,
    )

    print(
        f"batch seed={result.seed} -> {result.out_dir}\n"
        f"  written={result.n_written} skipped={result.n_skipped} "
        f"failed={result.n_failed} in {result.elapsed_s}s"
    )
    for failure in result.failures:
        print(f"  FAILED {failure.sample_id}: {failure.error}")
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli_main())
