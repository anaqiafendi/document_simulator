"""camera_fx stage — identity in v0.3, real FX in v1.0 (FDD #29 v0.3c AC-2c).

In v0.3 the ``camera_fx`` stage is a pure pass-through: the polygon from the
prior ``camera_2d`` snapshot is copied verbatim into a new ``camera_fx``
snapshot. The stage exists in the schema so v1.0 can swap in real camera
post-processing (lens distortion, motion blur, depth-of-field) without
touching downstream consumers.

Per the coordinate-tracking design doc §5, the v1.0 expansion will look like:

    distorted = cv2.projectPoints(
        polygon_3d_at_z1, rvec=I, tvec=0,
        cameraMatrix=K, distCoeffs=D,
    )

— but that requires camera intrinsics (K) and distortion coeffs (D) that the
v0.3 procedural scene doesn't carry. Until those land, identity is the
correct, schema-honest behavior.
"""

from __future__ import annotations

from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    TokenGroundTruth,
)


def apply_identity(token: TokenGroundTruth) -> None:
    """Append a ``camera_fx`` snapshot copying the most recent polygon.

    Args:
        token: Token with at least one prior CoordSnapshot (typically
            ``camera_2d`` from the v0.3b orchestrator). Mutated in place: a
            new ``camera_fx`` CoordSnapshot is appended whose ``polygon``
            field equals ``token.coords[-1].polygon``.

    Raises:
        IndexError: If ``token.coords`` is empty.

    TODO(v1.0): Replace the pass-through with real camera FX:
        - lens distortion via ``cv2.projectPoints`` with calibrated
          intrinsics K and distortion coefficients D
        - motion blur and depth-of-field do not shift coords (image-space
          only) so they don't change this snapshot
        - JPEG compression similarly does not move coords
    """
    if not token.coords:
        raise IndexError(
            f"token {token.token_id!r} has no CoordSnapshots to copy from"
        )

    prior_polygon = token.coords[-1].polygon
    token.coords.append(CoordSnapshot(stage="camera_fx", polygon=list(prior_polygon)))
