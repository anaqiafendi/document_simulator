"""Unit tests for synthesis.receipts.schema (AC-4 round-trip serialization)."""

from pathlib import Path

from document_simulator.synthesis.receipts import (
    CoordSnapshot,
    ImageGroundTruth,
    LineItem,
    Receipt,
    TokenGroundTruth,
)


def _build_sample_gt() -> ImageGroundTruth:
    """Construct a minimal but realistic ImageGroundTruth for round-trip tests."""
    receipt = Receipt(
        merchant="Test Cafe",
        address="1 Test St",
        items=[
            LineItem(sku="COFFEE", qty=2, unit_price=3.50),
            LineItem(sku="MUFFIN", qty=1, unit_price=2.25),
        ],
        tax_rate=0.06,
        payment_last4="1234",
    )
    tokens = [
        TokenGroundTruth(
            token_id="merchant",
            text="Test Cafe",
            semantic_role="merchant_name",
            coords=[
                CoordSnapshot(
                    stage="raster",
                    polygon=[(10.0, 10.0), (90.0, 10.0), (90.0, 30.0), (10.0, 30.0)],
                )
            ],
        )
    ]
    return ImageGroundTruth(
        image_id="00000001",
        image_path=Path("images/00000001.png"),
        image_size=(640, 480),
        tokens=tokens,
        receipt=receipt,
        seed=42,
        pipeline_version="0.1.0",
    )


def test_image_groundtruth_round_trip():
    """AC-4: ImageGroundTruth serializes and deserializes to an equal value."""
    gt = _build_sample_gt()
    dumped = gt.model_dump_json()
    loaded = ImageGroundTruth.model_validate_json(dumped)
    assert loaded == gt


def test_coord_snapshot_polygon_serializes_as_list():
    """Polygon tuples serialize as JSON arrays of [x,y] pairs."""
    snap = CoordSnapshot(
        stage="raster",
        polygon=[(1.0, 2.0), (3.0, 4.0)],
    )
    dumped = snap.model_dump(mode="json")
    assert dumped["polygon"] == [[1.0, 2.0], [3.0, 4.0]]


def test_token_final_polygon_returns_last_coord():
    """TokenGroundTruth.final_polygon returns the polygon of the last CoordSnapshot."""
    token = TokenGroundTruth(
        token_id="t1",
        text="hello",
        coords=[
            CoordSnapshot(
                stage="raster",
                polygon=[(0.0, 0.0), (10.0, 0.0), (10.0, 5.0), (0.0, 5.0)],
            ),
            CoordSnapshot(
                stage="camera_2d",
                polygon=[(1.0, 1.0), (11.0, 1.0), (11.0, 6.0), (1.0, 6.0)],
            ),
        ],
    )
    assert token.final_polygon == [(1.0, 1.0), (11.0, 1.0), (11.0, 6.0), (1.0, 6.0)]
