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

    v0.3d adds two extensions to the worker payload:

        * ``texture_png_bytes``: optional bytes of a PNG to attach as the
          receipt mesh's albedo texture. PIL convention (top-left origin)
          is V-flipped before saving so it matches Blender's bottom-left
          UV-space sampler. Without a texture, the receipt renders as a
          plain white plane.
        * ``return_passes``: when True the worker also ships back the UV
          and depth passes from ``render_eevee``. Needed by the v0.3d API
          router so it can run ``project_token_full`` to populate the GT
          coord trail through ``visibility -> camera_fx -> final_crop``.

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
        texture_png_bytes: bytes | None = None,
        tokens_json: list[dict] | None = None,
        raster_size: tuple[int, int] | None = None,
    ) -> Image.Image | tuple[Image.Image, list[dict]]:
        """Submit a render job to the worker; block until result or timeout.

        Args:
            seed: Reproducibility seed for build_scene + deform_paper.
            hdri_id: HDRI filename stem, or None to fall back to the first
                bundled HDRI.
            curl_strength: deform_paper curl_strength.
            fold_count: deform_paper fold_count.
            resolution: ``(W, H)`` Eevee render resolution.
            timeout: Maximum seconds to wait for the worker to return.
            texture_png_bytes: Optional PNG bytes (already V-flipped to
                Blender's bottom-left UV convention) to attach as the
                receipt's albedo texture. None -> plain-white receipt
                (legacy v0.3a/b behavior).
            tokens_json: Optional list of ``TokenGroundTruth.model_dump()``
                dicts. When provided (along with ``raster_size``), the worker
                also runs ``project_token_full`` against the just-rendered
                scene's UV/depth passes and returns the projected tokens —
                keeps bpy entirely out of the parent process.
            raster_size: ``(W, H)`` of the raster-stage source image. Required
                when ``tokens_json`` is supplied (the projector needs it to
                map raster-px to UV).

        Returns:
            ``PIL.Image`` of the rendered RGB when ``tokens_json`` is None
            (preserves the v0.3 sidecar contract used by existing tests).
            When ``tokens_json`` is supplied, returns ``(image, projected_tokens)``
            where ``projected_tokens`` is the input list with
            ``uv/world/camera_2d/camera_fx/final_crop`` snapshots appended
            and ``visible/occlusion_ratio`` populated.

        Raises:
            RuntimeError: If the worker died, returned an error, or timed out.
            ValueError: If ``tokens_json`` is supplied without ``raster_size``.
        """
        if tokens_json is not None and raster_size is None:
            raise ValueError("raster_size is required when tokens_json is supplied")

        self._ensure_alive()
        assert self._req_q is not None and self._res_q is not None

        job_id = uuid.uuid4().hex
        payload = {
            "seed": seed,
            "hdri_id": hdri_id,
            "curl_strength": curl_strength,
            "fold_count": fold_count,
            "resolution": resolution,
            "texture_png_bytes": texture_png_bytes,
            "tokens_json": tokens_json,
            "raster_size": raster_size,
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

        if tokens_json is not None:
            # result is (image_bytes, size, mode, projected_tokens_list)
            img_bytes, size, mode, projected = result
            img = Image.frombytes(mode, size, img_bytes)
            return img, projected

        # result is (image_bytes, size, mode) — legacy contract.
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
            receipt_obj = scene.objects["receipt"]
            mesh = receipt_obj.data
            deform_paper(
                mesh,
                curl_strength=payload["curl_strength"],
                fold_count=payload["fold_count"],
                seed=payload["seed"],
            )

            # v0.3d: optionally attach a texture (e.g. the augraphy'd receipt
            # raster) as the receipt mesh's albedo.
            tex_bytes = payload.get("texture_png_bytes")
            if tex_bytes:
                _attach_texture_from_png_bytes(receipt_obj, tex_bytes)

            rgb, uv_pass, depth_pass = render_eevee(scene, resolution=payload["resolution"])

            # Serialize the PIL image into a tuple that survives the spawn
            # IPC boundary cleanly.
            buf = io.BytesIO()
            rgb.save(buf, format="PNG")
            buf.seek(0)
            img = Image.open(buf).convert("RGB").copy()

            tokens_json = payload.get("tokens_json")
            if tokens_json:
                # v0.3d full-chain: project tokens here in the worker so the
                # parent process never has to import bpy. Round-trip the GT
                # via Pydantic JSON dicts since live bpy.types.Mesh objects
                # are not picklable.
                projected = _project_tokens_in_worker(
                    tokens_json=tokens_json,
                    mesh=mesh,
                    scene=scene,
                    uv_pass=uv_pass,
                    depth_pass=depth_pass,
                    render_size=tuple(payload["resolution"]),
                    raster_size=tuple(payload["raster_size"]),
                )
                res_q.put(
                    (
                        job_id,
                        True,
                        (img.tobytes(), img.size, img.mode, projected),
                    )
                )
            else:
                res_q.put((job_id, True, (img.tobytes(), img.size, img.mode)))
        except Exception as exc:  # noqa: BLE001
            res_q.put((job_id, False, repr(exc)))


def _project_tokens_in_worker(
    *,
    tokens_json: list[dict],
    mesh,
    scene,
    uv_pass,  # numpy.ndarray; not annotated to avoid eager-importing numpy
    depth_pass,
    render_size: tuple[int, int],
    raster_size: tuple[int, int],
) -> list[dict]:
    """Run ``project_token_full`` for every token; return updated dicts.

    Tokens are deserialized via ``TokenGroundTruth.model_validate``, mutated
    in place, then serialized back via ``model_dump``. This keeps the
    parent process bpy-free — it only ever sees JSON-friendly dicts.

    A single ``UVSpatialHash`` is built and reused across all tokens (per
    the FDD-projector amortization note).
    """
    from document_simulator.synthesis.receipts.bbox_projector import (
        UVSpatialHash,
        project_token_full,
    )
    from document_simulator.synthesis.receipts.schema import TokenGroundTruth

    spatial_hash = UVSpatialHash(mesh)
    projected: list[dict] = []
    for raw in tokens_json:
        token = TokenGroundTruth.model_validate(raw)
        try:
            project_token_full(
                token,
                mesh=mesh,
                scene=scene,
                camera=scene.camera,
                uv_pass=uv_pass,
                depth_pass=depth_pass,
                render_size=render_size,
                raster_size=raster_size,
                output_size=render_size,
                spatial_hash=spatial_hash,
            )
        except Exception as exc:  # noqa: BLE001
            # Per-token failure must not poison the whole batch — log and
            # keep the original snapshots so downstream code can detect.
            logger.warning(
                "project_token_full failed for token={!r}: {}",
                token.token_id,
                exc,
            )
        projected.append(token.model_dump(mode="json"))
    return projected


def _attach_texture_from_png_bytes(receipt_obj, png_bytes: bytes) -> None:
    """Attach a PNG texture (already V-flipped) as the receipt's albedo.

    Uses a Principled BSDF material so the rendered output respects the
    HDRI lighting and procedural curl shadows. The caller is responsible
    for V-flipping the source image (PIL top-left vs Blender bottom-left
    UV convention) — the API router does this before serializing the bytes.
    """
    import tempfile
    from pathlib import Path

    import bpy

    tmp_dir = Path(tempfile.mkdtemp(prefix="bpy_sidecar_tex_"))
    tex_path = tmp_dir / "receipt_albedo.png"
    tex_path.write_bytes(png_bytes)

    mat = bpy.data.materials.new(name="receipt_mat_albedo")
    mat.use_nodes = True
    nt = mat.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(tex_path), check_existing=True)
    tex.image.colorspace_settings.name = "sRGB"
    # Closest interpolation preserves character contrast (Linear bilinear
    # smears glyph pixels into adjacent paper, halving visible contrast).
    tex.interpolation = "Closest"

    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    receipt_obj.data.materials.clear()
    receipt_obj.data.materials.append(mat)
