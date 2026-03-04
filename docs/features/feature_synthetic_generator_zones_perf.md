# Feature: Synthetic Generator — Zones Tab Performance

> **GitHub Issue:** `#zones-perf`
> **Status:** `complete`
> **Module:** `document_simulator.ui.pages.00_synthetic_generator`

---

## Summary

Eliminate the three main sources of UI lag in the Zones tab of the Synthetic Document
Generator: full-page reruns on every click, redundant PIL image redraws, and O(n)
widget registration per zone.

---

## Motivation

### Problem Statement

The Zones tab is the most interactive part of the app — users click to place bounding
boxes over a document template — but every interaction is sluggish:

1. **Two full-page reruns per zone placed.** Each click calls bare `st.rerun()`, which
   re-executes the entire script including all 4 tabs, re-imports, and session state
   serialisation. Placing 10 zones = 20 full-page reruns.

2. **PIL image redrawn on every rerun.** `_draw_zones_on_image()` runs `ImageDraw` on
   the full template image (up to 2000 × 2800 px) unconditionally on every rerun,
   whether or not the zones or template have changed.

3. **O(n) widget registrations per rerun.** The zone list renders `st.selectbox` +
   `st.text_input` + `st.divider` per zone. With 20 zones that is 60+ widget
   registration calls per rerun, each causing Streamlit framework overhead.

### Value Delivered

- Zone placement feels near-instant: fragment reruns are ~10× faster than full-page
  reruns for a script of this size.
- Scrolling the zone list stops lagging as zone count grows.
- No changes to zone placement UX or data model — purely a performance refactor.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Form designer | I can click to place 20+ zones without the page freezing | I can annotate a complex form quickly |
| Developer | I can add zones and immediately see the overlay update | I get visual feedback without waiting 2+ seconds |

---

## Acceptance Criteria

- [x] AC-1: Clicking to place a zone triggers a fragment rerun, not a full-page rerun
- [x] AC-2: `_draw_zones_on_image` result is cached; PIL draw does NOT re-execute when zones and template are unchanged between reruns
- [x] AC-3: Zone list is rendered as a single `st.data_editor` call regardless of zone count
- [x] AC-4: All existing zone functionality is preserved: add, label, respondent, field type, data source, delete, clear all
- [x] AC-5: All existing UI tests pass after the refactor (124 passed)
- [x] AC-6: `st.rerun(scope="fragment")` is used for all reruns inside the zones fragment

---

## Design

### Public API

No change to the public Python API. This is a pure UI layer optimisation.

### Data Flow

**Before (per zone click):**
```
User click
    │
    ▼
st.rerun()  ← full script re-execution
    │  re-runs all 4 tabs, all imports, all widget registrations
    │  _draw_zones_on_image() runs PIL draw unconditionally
    │  60+ widget calls for zone list (regardless of changes)
    ▼
Updated UI  (~1-3 s on HF Spaces)
```

**After (per zone click):**
```
User click
    │
    ▼
st.rerun(scope="fragment")  ← only _zone_tab_fragment() re-runs
    │  other 3 tabs: frozen on frontend, not re-executed
    │  _draw_zones_on_image_cached() returns cached PIL result if zones unchanged
    │  st.data_editor: 1 component call regardless of zone count
    ▼
Updated UI  (~100-300 ms)
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `_zone_tab_fragment()` | `@st.fragment` function | Wraps entire zones tab; isolates reruns |
| `_draw_zones_on_image_cached()` | `@st.cache_data` function | Cached PIL overlay draw |
| `_stable_zones_hash()` | function | Deterministic hash of zones+respondents for cache key |
| `st.data_editor` | Streamlit component | Replaces O(n) per-zone widget rows |

### Configuration

No new settings. Uses `@st.cache_data(max_entries=8)` to cap memory for cached overlay
images. Each cached entry is ~16 MB for a 2000×2800 px RGB image, so worst-case 128 MB
across 8 cached variants.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/ui/pages/00_synthetic_generator.py` | Primary change — fragment, cache, data_editor |

### Key Architectural Decisions

1. **`@st.fragment` scope** — The entire `_tab_zones()` body is moved into a
   `@st.fragment`-decorated function `_zone_tab_fragment()`, which is called inside
   `with tab3:` in `main()`. This satisfies the Streamlit constraint that all widgets
   rendered by a fragment must be created inside the fragment body. All bare
   `st.rerun()` calls are replaced with `st.rerun(scope="fragment")`.

2. **Cache key via pre-computed hash** — `@st.cache_data` cannot hash `PIL.Image`
   objects natively. We pass `hash_funcs={Image.Image: lambda img: hashlib.md5(img.tobytes()).hexdigest()}`
   so Streamlit can construct a stable cache key. The zones list is also hashed
   separately (`_stable_zones_hash`) and passed as an explicit string argument, so the
   cache misses whenever zones or respondents change.

3. **`st.data_editor` for zone list** — Replaces per-zone `st.selectbox` +
   `st.text_input` rows with a single editable DataFrame. The table shows label,
   respondent, field type, data source, and read-only coordinate columns. Edits are
   written back to `st.session_state["synthesis_zones"]` on each commit. Row deletion
   via `num_rows="dynamic"` replaces the per-zone 🗑 button.
   Limitation: `SelectboxColumn` uses a single options list for the whole column, so
   field-type options are not filtered per respondent. A respondent-incompatible
   field-type selection is silently defaulted to the first valid type on write-back.

4. **Fragment + tabs constraint** — Streamlit docs warn that widgets in a fragment
   cannot be rendered into a container created outside the fragment. Calling
   `_zone_tab_fragment()` from inside `with tab3:` satisfies this because the
   fragment creates all its widgets in its own body scope, not in the externally
   created `tab3` container variable.

5. **Nested fragment guard** — We do NOT nest `@st.fragment` inside another. The
   zone fragment is called directly from `main()`. This avoids the known
   `StreamlitDuplicateElementId` bug (GitHub issue #10719).

### Known Edge Cases & Constraints

- `st.rerun(scope="fragment")` is only valid during a fragment-initiated rerun, not
  a full-app rerun. The current `coords is not None` guard makes this safe in practice.
- `st.data_editor` with `num_rows="dynamic"` does not support undo. Accidental row
  deletion cannot be recovered without re-clicking on the template.
- `@st.cache_data` stores a **copy** of the returned PIL Image. If the caller mutates
  the returned image (e.g. drawing the first-click marker on it), it must call
  `.copy()` first, which is already the pattern in `_draw_first_click_marker`.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/ui/integration/test_synthetic_generator.py` | integration | existing | Existing page-load and zone tests — must all still pass |
| `tests/ui/unit/test_zones_perf.py` | unit | 3 | Cache hit/miss behaviour; hash stability |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_draw_zones_cache_hit` | `test_zones_perf.py` | `_draw_zones_on_image_cached` doesn't exist |
| `test_stable_zones_hash_deterministic` | `test_zones_perf.py` | `_stable_zones_hash` doesn't exist |
| `test_draw_zones_cache_miss_on_zone_change` | `test_zones_perf.py` | cache function doesn't exist |

**Green — minimal implementation:**

Add `_stable_zones_hash()`, `_draw_zones_on_image_cached()` with `@st.cache_data`,
convert `_tab_zones()` → `_zone_tab_fragment()` with `@st.fragment`, replace zone
list with `st.data_editor`.

**Refactor:**

| What changed | Why |
|--------------|-----|
| Extracted `_zones_to_dataframe()` helper | Keeps `_zone_tab_fragment` readable |
| Extracted `_dataframe_to_zones()` helper | Write-back logic separated from render logic |

### How to Run

```bash
uv run pytest tests/ui/ tests/ui/unit/test_zones_perf.py -v --no-cov
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `streamlit>=1.37.0` | external | `@st.fragment` and `st.rerun(scope="fragment")` |
| `pandas` | external | `st.data_editor` input |
| `pillow` | external | PIL image drawing (unchanged) |

### Required By

| Consumer | How it uses this feature |
|----------|------------------------|
| HF Spaces deployment | Zones tab is the most-used interactive surface; speed directly impacts UX |

---

## Usage Examples

### Minimal — place a zone

```
1. Go to Zones tab
2. Click top-left corner of desired zone on the image
3. Click bottom-right corner
→ Zone appears in table immediately (fragment rerun only)
```

### Edit zone in table

```
1. Double-click the Respondent cell in the zone table
2. Select a different respondent from the dropdown
3. Press Enter or click away
→ Zone overlay colour updates on next interaction
```

---

## Future Work

- [ ] Switch to `st_canvas(drawing_mode="rect", update_streamlit=False)` for drag-to-draw
  (one rerun per zone instead of two), blocked by `streamlit-drawable-canvas` / Streamlit
  1.54 compatibility issue (`image_to_url` removed)
- [ ] Store template image as JPEG bytes in session state for faster cache hashing
- [ ] Pagination for zone list if zone count regularly exceeds 50
- [ ] Undo/redo stack for zone operations

---

## References

- [st.fragment — Streamlit docs](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment)
- [st.cache_data — Streamlit docs](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data)
- [st.data_editor — Streamlit docs](https://docs.streamlit.io/develop/api-reference/data/st.data_editor)
- [StreamlitDuplicateElementId — GitHub #10719](https://github.com/streamlit/streamlit/issues/10719)
