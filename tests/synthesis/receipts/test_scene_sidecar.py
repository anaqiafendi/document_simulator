"""Unit tests for ``synthesis.receipts.scene.sidecar`` (FDD #29 v0.3 §AC-sidecar).

The sidecar is a ``multiprocessing.Process``-based bpy worker that isolates
bpy's segfault risk from the FastAPI process. The worker accepts render
requests via a ``multiprocessing.Queue`` and returns results on a paired
results queue. If the worker crashes, the next request triggers a recycle.

These tests run on Python 3.11 (where bpy is installed); skipped otherwise.
"""

from __future__ import annotations

import pytest
from PIL import Image

bpy = pytest.importorskip("bpy")  # noqa: F811

from document_simulator.synthesis.receipts.scene.sidecar import BpySidecar  # noqa: E402


def test_sidecar_renders_one_image() -> None:
    """AC-sidecar: submit a render job, get back the rendered RGB image.

    The sidecar runs ``build_scene + render_eevee`` inside the worker
    process and ships back the resulting PIL image (serialized as bytes
    + size for picklability).
    """
    sidecar = BpySidecar()
    sidecar.start()
    try:
        result = sidecar.render(
            seed=42,
            hdri_id=None,
            curl_strength=0.0,
            fold_count=0,
            resolution=(64, 64),  # tiny for test speed
            timeout=60.0,
        )
        assert isinstance(result, Image.Image)
        assert result.size == (64, 64)
    finally:
        sidecar.stop()


def test_sidecar_survives_worker_crash() -> None:
    """AC-sidecar: kill the worker mid-test; the next render still succeeds.

    The sidecar should detect a dead worker (process.is_alive() == False)
    on the next .render() call, recycle the worker process, and serve the
    request transparently.
    """
    sidecar = BpySidecar()
    sidecar.start()
    try:
        # First render — primes the worker.
        result_1 = sidecar.render(
            seed=42,
            hdri_id=None,
            curl_strength=0.0,
            fold_count=0,
            resolution=(64, 64),
            timeout=60.0,
        )
        assert isinstance(result_1, Image.Image)

        # Murder the worker.
        worker_pid = sidecar._process.pid  # type: ignore[union-attr]
        sidecar._process.terminate()  # type: ignore[union-attr]
        sidecar._process.join(timeout=5.0)  # type: ignore[union-attr]

        # Now request another render. The sidecar must recycle the worker
        # transparently rather than raising.
        result_2 = sidecar.render(
            seed=43,
            hdri_id=None,
            curl_strength=0.0,
            fold_count=0,
            resolution=(64, 64),
            timeout=60.0,
        )
        assert isinstance(result_2, Image.Image)
        # And the worker pid must have changed (proving recycle happened).
        new_pid = sidecar._process.pid  # type: ignore[union-attr]
        assert new_pid != worker_pid, "worker should have been recycled to a new PID"
    finally:
        sidecar.stop()
