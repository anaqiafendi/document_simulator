"""Sutherland-Hodgman clipping + final_crop tests (FDD #29 v0.3c AC-3c).

Tested behaviors:
    - sutherland_hodgman_clip with subject fully inside clip -> unchanged
    - sutherland_hodgman_clip with partially overlapping subject -> clipped
      polygon strictly contained within the clip polygon
    - sutherland_hodgman_clip with subject fully outside -> empty list
    - apply_final_crop on an off-frame token -> token.visible False, no
      ``final_crop`` snapshot appended
    - apply_final_crop honours ``crop_origin`` by subtracting it from each
      polygon vertex BEFORE clipping against the output image bounds
"""

from __future__ import annotations

import pytest

from document_simulator.synthesis.receipts.bbox_projector.clip import (
    apply_final_crop,
    sutherland_hodgman_clip,
)
from document_simulator.synthesis.receipts.schema import (
    CoordSnapshot,
    TokenGroundTruth,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Standard CCW image-bound clip polygon for the 100x100 tests below.
_IMG_BOUNDS_100 = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]


def _make_token_with_camera_2d(
    polygon: list[tuple[float, float]],
    *,
    token_id: str = "tok",
) -> TokenGroundTruth:
    """Token with raster + uv + world + camera_2d snapshots (camera_fx is what
    apply_final_crop reads off the chain). For these unit tests the only thing
    that matters is the *last* snapshot's polygon.
    """
    return TokenGroundTruth(
        token_id=token_id,
        text="x",
        coords=[
            CoordSnapshot(stage="raster", polygon=polygon),
            CoordSnapshot(stage="camera_2d", polygon=polygon),
            CoordSnapshot(stage="camera_fx", polygon=polygon),
        ],
    )


# ---------------------------------------------------------------------------
# Sutherland-Hodgman: pure geometry
# ---------------------------------------------------------------------------


def test_sutherland_hodgman_polygon_fully_inside_unchanged() -> None:
    """A subject polygon entirely inside the clip is returned with the same
    vertices (within float tolerance).
    """
    subject = [(10.0, 10.0), (50.0, 10.0), (50.0, 50.0), (10.0, 50.0)]
    clipped = sutherland_hodgman_clip(subject, _IMG_BOUNDS_100)

    assert len(clipped) == 4
    for (sx, sy), (cx, cy) in zip(subject, clipped, strict=True):
        assert abs(sx - cx) < 1e-6 and abs(sy - cy) < 1e-6


def test_sutherland_hodgman_polygon_partially_clipped_returns_clipped() -> None:
    """A half-in / half-out subject polygon is clipped to a quad contained
    entirely within the clip polygon.
    """
    # Subject straddles the right edge: x goes from 50 to 150, clip stops at 100.
    subject = [(50.0, 25.0), (150.0, 25.0), (150.0, 75.0), (50.0, 75.0)]
    clipped = sutherland_hodgman_clip(subject, _IMG_BOUNDS_100)

    assert len(clipped) >= 3, "clipped polygon must remain a polygon"
    for x, y in clipped:
        assert -1e-6 <= x <= 100.0 + 1e-6
        assert -1e-6 <= y <= 100.0 + 1e-6
    # Right edge of the result should sit on the clip's right edge (x = 100).
    assert any(abs(x - 100.0) < 1e-6 for x, _ in clipped), (
        f"expected clipped polygon to touch right clip edge, got {clipped}"
    )


def test_sutherland_hodgman_polygon_fully_outside_returns_empty() -> None:
    """A subject polygon entirely outside the clip returns an empty list."""
    subject = [(200.0, 200.0), (300.0, 200.0), (300.0, 300.0), (200.0, 300.0)]
    clipped = sutherland_hodgman_clip(subject, _IMG_BOUNDS_100)
    assert clipped == []


# ---------------------------------------------------------------------------
# apply_final_crop: token-mutation contract
# ---------------------------------------------------------------------------


def test_apply_final_crop_off_frame_marks_not_visible() -> None:
    """A token whose camera_fx polygon is entirely off-frame ends up with
    ``visible=False`` and NO ``final_crop`` snapshot appended.
    """
    off_frame_polygon = [(200.0, 200.0), (250.0, 200.0), (250.0, 250.0), (200.0, 250.0)]
    token = _make_token_with_camera_2d(off_frame_polygon)
    assert token.visible is True  # default

    apply_final_crop(token, output_size=(100, 100))

    assert token.visible is False
    assert all(c.stage != "final_crop" for c in token.coords), (
        f"expected NO final_crop snapshot on off-frame token, got stages "
        f"{[c.stage for c in token.coords]}"
    )


def test_apply_final_crop_handles_crop_origin() -> None:
    """``crop_origin=(50, 50)`` subtracted from every vertex BEFORE clipping
    against (0,0)-(50,50) bounds yields a clipped polygon at (10,10)-(50,50).
    """
    # Polygon at (60,60)-(100,100) in pre-crop pixel space.
    pre_crop = [(60.0, 60.0), (100.0, 60.0), (100.0, 100.0), (60.0, 100.0)]
    token = _make_token_with_camera_2d(pre_crop)

    apply_final_crop(token, output_size=(50, 50), crop_origin=(50.0, 50.0))

    final_snap = next((c for c in token.coords if c.stage == "final_crop"), None)
    assert final_snap is not None, (
        f"expected final_crop snapshot, got stages "
        f"{[c.stage for c in token.coords]}"
    )

    # Expected: (10,10), (50,10), (50,50), (10,50) — the input shifted by
    # (-50, -50) is fully inside the (0,0)-(50,50) image bounds, so no
    # additional clipping is required.
    expected = [(10.0, 10.0), (50.0, 10.0), (50.0, 50.0), (10.0, 50.0)]
    assert len(final_snap.polygon) == 4
    for (ex, ey), (ax, ay) in zip(expected, final_snap.polygon, strict=True):
        assert abs(ex - ax) < 1e-6 and abs(ey - ay) < 1e-6, (
            f"expected {expected}, got {final_snap.polygon}"
        )
    # And the token should remain visible — it's well within the cropped image.
    assert token.visible is True


def test_apply_final_crop_keeps_in_bounds_polygon_unchanged() -> None:
    """Sanity: a polygon already in bounds is appended verbatim with no clip
    artifacts (no spurious extra vertices).
    """
    in_bounds = [(10.0, 10.0), (50.0, 10.0), (50.0, 50.0), (10.0, 50.0)]
    token = _make_token_with_camera_2d(in_bounds)
    apply_final_crop(token, output_size=(100, 100))

    final_snap = next((c for c in token.coords if c.stage == "final_crop"), None)
    assert final_snap is not None
    assert len(final_snap.polygon) == 4
    for (ex, ey), (ax, ay) in zip(in_bounds, final_snap.polygon, strict=True):
        assert abs(ex - ax) < 1e-6 and abs(ey - ay) < 1e-6


def test_apply_final_crop_requires_prior_snapshot() -> None:
    """A token with no prior coord snapshot cannot be cropped — raises."""
    token = TokenGroundTruth(token_id="empty", text="x", coords=[])
    with pytest.raises((ValueError, IndexError)):
        apply_final_crop(token, output_size=(100, 100))
