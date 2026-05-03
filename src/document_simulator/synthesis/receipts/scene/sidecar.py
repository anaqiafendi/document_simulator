"""bpy worker sidecar (FDD #29 v0.3 §AC-sidecar — deferred from v0.3a).

Why a sidecar?
    bpy is a single-process global mutable state machine. It can segfault
    under load (concurrent operators, repeated factory-reset, GPU resource
    exhaustion). When that happens inside the FastAPI process, the whole
    server dies. A sidecar process isolates the blast radius — a worker
    crash returns an error to the client, the next request recycles the
    worker, and FastAPI keeps serving.

Architecture
    BpySidecar is a thin wrapper around a single ``multiprocessing.Process``
    plus a request queue and a result queue. The worker target (``_worker_main``)
    consumes (job_id, payload) tuples, runs build_scene -> deform_paper ->
    render_eevee, and ships the result back as (job_id, ok, payload).

    Pillow images cross the process boundary as ``(bytes, size, mode)`` tuples
    since the ``Image`` object itself isn't picklable across the spawn boundary
    cleanly on macOS (forking bpy is unsupported).

Recycle on crash
    Each ``render()`` call checks ``self._process.is_alive()`` and respawns
    a fresh worker if it died. This keeps the public API simple ("just call
    render again") at the cost of a per-call alive check, which is microsecond
    cheap.

Hard timeout
    ``render(..., timeout=...)`` uses ``Queue.get(timeout=...)`` so a wedged
    worker doesn't deadlock the caller. On timeout the worker is killed and
    the next call respawns it.
"""

from __future__ import annotations

import io
import multiprocessing as mp
import queue
import uuid
from typing import Any

from loguru import logger
from PIL import Image

# Use spawn so the worker doesn't inherit a half-initialized bpy from the
# parent (forking bpy after it has been imported is unsupported and segfaults
# on macOS).
_MP_CONTEXT = mp.get_context("spawn")


class BpySidecar:
    """Single-worker bpy process pool with crash recycling.

    Public API:
        sidecar = BpySidecar()
        sidecar.start()
        try:
            img = sidecar.render(seed=42, hdri_id=None, curl_strength=0.1,
                                 fold_count=0, resolution=(1024, 1024),
                                 timeout=60.0)
        finally:
            sidecar.stop()

    Thread-safety: not safe for concurrent calls from multiple threads in
    the parent process — wrap in a lock if needed. (FastAPI's per-request
    handlers are independent, so the typical async flow is fine.)
    """

    def __init__(self) -> None:
        self._process: mp.process.BaseProcess | None = None
        self._req_q: mp.Queue | None = None
        self._res_q: mp.Queue | None = None

    # ---------------------------------------------------------------- lifecycle
    def start(self) -> None:
        """Spawn the worker process. Idempotent — calling on a live worker is
        a no-op."""
        if self._process is not None and self._process.is_alive():
            return
        self._spawn_worker()

    def stop(self) -> None:
        """Terminate the worker and tear down queues."""
        if self._process is None:
            return
        try:
            if self._req_q is not None:
                self._req_q.put(("__STOP__", None))
            self._process.join(timeout=5.0)
        except Exception:  # noqa: BLE001
            pass
        if self._process is not None and self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=5.0)
            if self._process.is_alive():
                self._process.kill()
        self._process = None
        self._req_q = None
        self._res_q = None

    # ----------------------------------------------------------------- internals
    def _spawn_worker(self) -> None:
        """Create new queues + process and start it."""
        self._req_q = _MP_CONTEXT.Queue()
        self._res_q = _MP_CONTEXT.Queue()
        self._process = _MP_CONTEXT.Process(
            target=_worker_main,
            args=(self._req_q, self._res_q),
            daemon=True,
        )
        self._process.start()
        logger.debug("BpySidecar spawned worker pid={}", self._process.pid)

    def _ensure_alive(self) -> None:
        """Recycle the worker if it died since the last call."""
        if self._process is None or not self._process.is_alive():
            if self._process is not None:
                logger.warning(
                    "BpySidecar worker pid={} died (exit={}); respawning",
                    self._process.pid,
                    self._process.exitcode,
                )
            self._spawn_worker()

    # -------------------------------------------------------------------- render
    def render(
        self,
        *,
        seed: int,
        hdri_id: str | None,
        curl_strength: float,
        fold_count: int,
        resolution: tuple[int, int],
        timeout: float = 60.0,
    ) -> Image.Image:
        """Submit a render job to the worker; block until result or timeout.

        Args:
            seed: Reproducibility seed for build_scene + deform_paper.
            hdri_id: HDRI filename stem, or None to fall back to the first
                bundled HDRI.
            curl_strength: deform_paper curl_strength.
            fold_count: deform_paper fold_count.
            resolution: ``(W, H)`` Eevee render resolution.
            timeout: Maximum seconds to wait for the worker to return.

        Returns:
            The rendered RGB ``PIL.Image``.

        Raises:
            RuntimeError: If the worker died, returned an error, or timed out.
        """
        self._ensure_alive()
        assert self._req_q is not None and self._res_q is not None

        job_id = uuid.uuid4().hex
        payload = {
            "seed": seed,
            "hdri_id": hdri_id,
            "curl_strength": curl_strength,
            "fold_count": fold_count,
            "resolution": resolution,
        }
        self._req_q.put((job_id, payload))

        try:
            res_job_id, ok, result = self._res_q.get(timeout=timeout)
        except queue.Empty as exc:
            # Worker is wedged — kill so the next call respawns it cleanly.
            logger.error("BpySidecar timeout after {}s; killing worker", timeout)
            if self._process is not None:
                self._process.terminate()
                self._process.join(timeout=5.0)
            raise RuntimeError(f"BpySidecar render timed out after {timeout}s") from exc

        if res_job_id != job_id:
            raise RuntimeError(
                f"BpySidecar response job_id mismatch: " f"sent {job_id} got {res_job_id}"
            )
        if not ok:
            raise RuntimeError(f"BpySidecar worker error: {result}")
        # result is (image_bytes, size, mode)
        img_bytes, size, mode = result
        return Image.frombytes(mode, size, img_bytes)


# ---------------------------------------------------------------------------
# Worker target — runs in a separate process. Imports bpy here so the parent
# process never imports bpy.
# ---------------------------------------------------------------------------


def _worker_main(req_q: Any, res_q: Any) -> None:
    """Run the worker loop: receive job, render, ship result. Loops forever
    until a ``("__STOP__", None)`` sentinel is received."""
    # Strip any ``bpy/4.2/scripts/{startup,modules}`` paths the parent prepended
    # at its first ``import bpy``. Those paths shadow the real ``bpy/__init__.so``
    # under site-packages with a python ``__init__.py`` that does
    # ``from _bpy import ...`` — but ``_bpy`` is only registered when the .so
    # initializes, leading to the cryptic ``ModuleNotFoundError: No module
    # named '_bpy'`` when the spawn child re-imports bpy through the python
    # entrypoint.
    import sys

    sys.path[:] = [p for p in sys.path if "bpy/4.2/scripts" not in p]
    # Drop any pre-cached bpy entry too, just in case spawn pickled it.
    for mod_name in [m for m in list(sys.modules) if m == "bpy" or m.startswith("bpy.")]:
        sys.modules.pop(mod_name, None)

    # Import bpy / scene helpers inside the worker only — keeps the parent
    # process bpy-free (which is the whole point of the sidecar).
    from document_simulator.synthesis.receipts.scene import (
        build_scene,
        deform_paper,
        render_eevee,
    )

    while True:
        try:
            job_id, payload = req_q.get()
        except (EOFError, OSError):
            break
        if job_id == "__STOP__":
            break

        try:
            scene = build_scene(seed=payload["seed"], hdri_id=payload["hdri_id"])
            mesh = scene.objects["receipt"].data
            deform_paper(
                mesh,
                curl_strength=payload["curl_strength"],
                fold_count=payload["fold_count"],
                seed=payload["seed"],
            )
            rgb, _uv_pass, _depth_pass = render_eevee(scene, resolution=payload["resolution"])
            # Serialize the PIL image into a tuple that survives the spawn
            # IPC boundary cleanly.
            buf = io.BytesIO()
            rgb.save(buf, format="PNG")
            buf.seek(0)
            # Re-decode so we ship raw RGB bytes (smaller pickle than PNG-in-bytes
            # on the wire? PNG is fine, decompresses cheaply on the parent.).
            img = Image.open(buf).convert("RGB").copy()
            res_q.put((job_id, True, (img.tobytes(), img.size, img.mode)))
        except Exception as exc:  # noqa: BLE001
            res_q.put((job_id, False, repr(exc)))
