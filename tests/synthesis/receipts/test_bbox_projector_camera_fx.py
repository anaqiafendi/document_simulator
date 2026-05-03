"""camera_fx identity stage tests (FDD #29 v0.3c AC-2c).

In v0.3 the ``camera_fx`` stage is a verbatim copy of ``camera_2d`` —
non-trivial FX (lens distortion, motion blur, DoF) defer to v1.0. The stage
is appended for schema consistency so v1.0 only needs to swap the
implementation, not change consumers.
"""

from __future__ import annotations

import pytest

from document_simulator.synthesis.receipts.bbox_projector.camera_fx import (
    apply_identity,
)
from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    TokenGroundTruth,
)


def test_apply_identity_copies_camera_2d_polygon() -> None:
    """After apply_identity the token has a camera_fx CoordSnapshot whose
    polygon equals the prior camera_2d polygon.
    """
    camera_2d_polygon = [
        (10.0, 20.0),
        (30.0, 20.0),
        (30.0, 40.0),
        (10.0, 40.0),
    ]
    token = TokenGroundTruth(
        token_id="t1",
        text="x",
        coords=[
            CoordSnapshot(stage="raster", polygon=[(0.0, 0.0)]),
            CoordSnapshot(stage="uv", polygon=[(0.0, 0.0)]),
            CoordSnapshot(
                stage="world",
                polygon=[(0.0, 0.0)],
                polygon_3d=[(0.0, 0.0, 0.0)],
            ),
            CoordSnapshot(stage="camera_2d", polygon=camera_2d_polygon),
        ],
    )

    apply_identity(token)

    fx_snap = next((c for c in token.coords if c.stage == "camera_fx"), None)
    assert fx_snap is not None, (
        f"expected camera_fx snapshot appended, got stages "
        f"{[c.stage for c in token.coords]}"
    )
    assert fx_snap.polygon == camera_2d_polygon


def test_apply_identity_requires_prior_snapshot() -> None:
    """A token with no prior CoordSnapshot can't have an identity copy taken.
    """
    token = TokenGroundTruth(token_id="empty", text="x", coords=[])
    with pytest.raises((ValueError, IndexError)):
        apply_identity(token)
