"""Pure helper functions for the Synthetic Generator zones tab.

Extracted into a separate importable module so unit tests can import them
without pulling in the Streamlit runtime (00_synthetic_generator.py cannot
be imported via normal means due to its numeric prefix and top-level main()
call).

All functions here are pure Python — no Streamlit dependency.
"""

from __future__ import annotations

import hashlib
import json

import pandas as pd


def _stable_zones_hash(zones: list[dict], respondents: list[dict]) -> str:
    """Deterministic MD5 hash of the zone+respondent config for cache-key use."""
    payload = json.dumps({"zones": zones, "respondents": respondents}, sort_keys=True)
    return hashlib.md5(payload.encode()).hexdigest()


def _zones_to_dataframe(
    zones: list[dict],
    resp_id_to_name: dict[str, str],
) -> pd.DataFrame:
    """Convert a list of zone dicts to a pandas DataFrame for st.data_editor."""
    rows = []
    for z in zones:
        box = z["box"]
        rows.append(
            {
                "label": z["label"],
                "respondent": resp_id_to_name.get(z["respondent_id"], z["respondent_id"]),
                "field_type": z.get("field_type_id", "standard"),
                "data_source": z.get("faker_provider", "name"),
                "x1": int(box[0][0]),
                "y1": int(box[0][1]),
                "x2": int(box[2][0]),
                "y2": int(box[2][1]),
            }
        )
    return pd.DataFrame(
        rows,
        columns=["label", "respondent", "field_type", "data_source", "x1", "y1", "x2", "y2"],
    )


def _dataframe_to_zones(
    df: pd.DataFrame,
    original_zones: list[dict],
    resp_name_to_id: dict[str, str],
) -> list[dict]:
    """Write edited DataFrame rows back to zone dicts, preserving non-editable fields."""
    updated = []
    for i, row in enumerate(df.itertuples(index=False)):
        orig = original_zones[i] if i < len(original_zones) else {}
        resp_id = resp_name_to_id.get(row.respondent, orig.get("respondent_id", ""))
        x1, y1, x2, y2 = float(row.x1), float(row.y1), float(row.x2), float(row.y2)
        updated.append(
            {
                **orig,
                "zone_id": orig.get("zone_id", f"z_{i + 1}"),
                "label": row.label,
                "respondent_id": resp_id,
                "field_type_id": row.field_type,
                "faker_provider": row.data_source,
                "box": [[x1, y1], [x2, y1], [x2, y2], [x1, y2]],
                "custom_values": orig.get("custom_values", []),
                "alignment": orig.get("alignment", "left"),
            }
        )
    return updated
