"""Unit tests for zones performance helpers (cache hit/miss, hash stability)."""

import pandas as pd
import pytest

from document_simulator.ui.pages.synthetic_generator_helpers import (
    _dataframe_to_zones,
    _stable_zones_hash,
    _zones_to_dataframe,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

RESP_A = {
    "respondent_id": "r1",
    "display_name": "Alice",
    "field_types": [{"field_type_id": "standard", "display_name": "Standard"}],
}
RESP_B = {
    "respondent_id": "r2",
    "display_name": "Bob",
    "field_types": [{"field_type_id": "signature", "display_name": "Signature"}],
}

ZONE_1 = {
    "zone_id": "z_1",
    "label": "name_field",
    "box": [[10.0, 20.0], [110.0, 20.0], [110.0, 50.0], [10.0, 50.0]],
    "respondent_id": "r1",
    "field_type_id": "standard",
    "faker_provider": "name",
    "custom_values": [],
    "alignment": "left",
}
ZONE_2 = {
    "zone_id": "z_2",
    "label": "sig_field",
    "box": [[10.0, 60.0], [110.0, 60.0], [110.0, 90.0], [10.0, 90.0]],
    "respondent_id": "r2",
    "field_type_id": "signature",
    "faker_provider": "name",
    "custom_values": [],
    "alignment": "left",
}


# ---------------------------------------------------------------------------
# _stable_zones_hash
# ---------------------------------------------------------------------------


def test_stable_zones_hash_deterministic():
    """Same zones+respondents always produce the same hash."""
    h1 = _stable_zones_hash([ZONE_1], [RESP_A])
    h2 = _stable_zones_hash([ZONE_1], [RESP_A])
    assert h1 == h2


def test_stable_zones_hash_changes_on_zone_mutation():
    """Adding a zone produces a different hash."""
    h1 = _stable_zones_hash([ZONE_1], [RESP_A])
    h2 = _stable_zones_hash([ZONE_1, ZONE_2], [RESP_A])
    assert h1 != h2


def test_stable_zones_hash_changes_on_label_change():
    """Changing a zone label produces a different hash."""
    z_modified = {**ZONE_1, "label": "different_label"}
    h1 = _stable_zones_hash([ZONE_1], [RESP_A])
    h2 = _stable_zones_hash([z_modified], [RESP_A])
    assert h1 != h2


def test_stable_zones_hash_changes_on_respondent_change():
    """Changing a zone's respondent produces a different hash.

    Regression test for the leading-underscore cache-key bug: the
    `zones_hash` argument to `_draw_zones_on_image_cached` must NOT have a
    leading underscore, otherwise Streamlit excludes it from the cache key
    and the overlay never updates when zones/respondents change.
    """
    z_resp_b = {**ZONE_1, "respondent_id": "r2"}
    h1 = _stable_zones_hash([ZONE_1], [RESP_A])
    h2 = _stable_zones_hash([z_resp_b], [RESP_A])
    assert h1 != h2


# ---------------------------------------------------------------------------
# _zones_to_dataframe / _dataframe_to_zones round-trip
# ---------------------------------------------------------------------------


def test_zones_to_dataframe_columns():
    """DataFrame has the expected columns and rows."""
    resp_id_to_name = {"r1": "Alice", "r2": "Bob"}
    df = _zones_to_dataframe([ZONE_1, ZONE_2], resp_id_to_name)
    assert list(df.columns) == [
        "label",
        "respondent",
        "field_type",
        "data_source",
        "x1",
        "y1",
        "x2",
        "y2",
    ]
    assert len(df) == 2
    assert df.iloc[0]["label"] == "name_field"
    assert df.iloc[0]["respondent"] == "Alice"


def test_dataframe_to_zones_round_trip():
    """Converting zones → DataFrame → zones preserves essential fields."""
    resp_id_to_name = {"r1": "Alice", "r2": "Bob"}
    resp_name_to_id = {"Alice": "r1", "Bob": "r2"}
    df = _zones_to_dataframe([ZONE_1, ZONE_2], resp_id_to_name)
    restored = _dataframe_to_zones(df, [ZONE_1, ZONE_2], resp_name_to_id)
    assert len(restored) == 2
    assert restored[0]["label"] == ZONE_1["label"]
    assert restored[0]["respondent_id"] == ZONE_1["respondent_id"]
    assert restored[0]["box"] == ZONE_1["box"]
    assert restored[1]["field_type_id"] == ZONE_2["field_type_id"]


def test_dataframe_to_zones_deletion():
    """Removing a row from the DataFrame drops the corresponding zone."""
    resp_id_to_name = {"r1": "Alice", "r2": "Bob"}
    resp_name_to_id = {"Alice": "r1", "Bob": "r2"}
    df = _zones_to_dataframe([ZONE_1, ZONE_2], resp_id_to_name)
    df_one_row = df.iloc[:1].reset_index(drop=True)
    restored = _dataframe_to_zones(df_one_row, [ZONE_1, ZONE_2], resp_name_to_id)
    assert len(restored) == 1
    assert restored[0]["label"] == ZONE_1["label"]


def test_dataframe_roundtrip_is_stable():
    """zones → df → zones produces no spurious differences.

    Regression test for the double-rerun blank-screen bug: if a zones →
    DataFrame → zones round-trip produces a result that != the original
    zones, the fragment incorrectly detects a "change" and calls
    st.rerun(scope="fragment") even when the user hasn't edited anything.
    Two back-to-back fragment reruns cause the tab to flash blank.

    The fix was to remove the manual st.rerun() from the data_editor block.
    This test documents the stable-roundtrip property that makes that fix safe:
    integer-valued float coordinates survive the int() cast in _zones_to_dataframe
    and float() cast in _dataframe_to_zones unchanged.
    """
    resp_id_to_name = {"r1": "Alice", "r2": "Bob"}
    resp_name_to_id = {"Alice": "r1", "Bob": "r2"}
    # Coordinates are integer-valued floats, as produced by the click handler
    # (raw_x = int(coords["x"] * scale), stored as float())
    zones = [
        {**ZONE_1, "box": [[100.0, 200.0], [300.0, 200.0], [300.0, 400.0], [100.0, 400.0]]},
        {**ZONE_2, "box": [[10.0, 60.0], [110.0, 60.0], [110.0, 90.0], [10.0, 90.0]]},
    ]
    df = _zones_to_dataframe(zones, resp_id_to_name)
    restored = _dataframe_to_zones(df, zones, resp_name_to_id)
    assert restored == zones, (
        "Round-trip changed zone data — this would trigger a spurious st.rerun() "
        "and cause the fragment to flash blank after every zone placement."
    )
