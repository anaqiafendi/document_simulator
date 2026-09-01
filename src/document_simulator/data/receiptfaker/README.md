# ReceiptFaker template taxonomy

Acquires the public ReceiptFaker template catalogue and reduces every template to
a set of categorical **visual feature dimensions**, so templates can be grouped by
layout similarity and used as a stratified basis for synthetic receipt generation.

## Why this is structured data, not vision

Each `/generate/<slug>` page server-renders its template definition as JSON inside
the Next.js RSC flight stream (`self.__next_f.push([1, "<chunk>"])`). Reassembling
those chunks yields the template's **authoring model** — the same enums the site's
editor manipulates (`fontType`, `bottomDividerType`, section order, …).

That means the feature labels are *ground truth*, not inferred: no screenshots, no
headless browser, no OCR, no clustering heuristics. The discrete category set for
each dimension is exactly the site's own value space, discovered empirically.

## Usage

```bash
# 1. Scrape the catalogue (~979 templates, resumable, ~60s at concurrency 6)
python -m document_simulator.data.receiptfaker.scrape --out data/receiptfaker

# 2. Label every template and report the taxonomy
python -m document_simulator.data.receiptfaker.analyze --data data/receiptfaker
```

Outputs, all under `--data` (git-ignored, per the repo's `data/*` rule):

| File | Contents |
| --- | --- |
| `templates/<slug>.json` | Raw template definition, one file per template |
| `labels.csv` | One row per template, one column per dimension |
| `taxonomy.json` | `dimension -> {value: count}` — the discrete category set |
| `clusters.json` | Template slugs grouped by identical full label tuple |

## Dimensions

| Dimension | Meaning |
| --- | --- |
| `font_type` | Typeface family the receipt renders in |
| `merchant_block_position` | Where the merchant name/address block sits |
| `logo_placement` | Where the logo image sits (`NONE` if absent) |
| `divider_style` | Dominant separator drawn between blocks |
| `total_divider_style` | Separator drawn above the total row |
| `total_emphasis` | Size emphasis applied to the total row |
| `layout_signature` | Ordered sequence of block types — the layout itself |
| `money_row_order` | Order of semantic money rows across the whole receipt |
| `quantity_column` | Whether line items render a leading quantity column |
| `barcode_placement` | Where the barcode block sits (`NONE` if absent) |
| `number_format` | Alignment of numeric columns |
| `background_type` | Paper/background treatment |
| `header_alignment` | Text alignment of the header block |
| `section_count` | Number of stacked blocks |

`layout_signature` and `money_row_order` are *composite* dimensions: their value is
a sequence, so they have long tails (468 and 94 distinct values). Group on a subset
of dimensions when you want coarser buckets:

```python
labels.group_key(["font_type", "logo_placement", "divider_style"])
```

## Section model

Templates are a flat ordered list of typed blocks:

| Block | Carries |
| --- | --- |
| `HEADER` | Logo, merchant name/address, alignment |
| `ITEMS` | Line items (`quantity`/`description`/`total`), `totalLines`, total row |
| `PAYMENT` | Cash or card tender rows as `title`/`value` pairs |
| `CUSTOM` | Free text with its own alignment |
| `DATE` | Timestamp block |
| `BARCODE` | Barcode of a given length/size |
| `RESTAURANT` | Two-column metadata (`leftFields`/`rightFields`) |

## Notes

- Slugs are matched case-sensitively but written to disk through
  `build_filenames()`, which suffixes case-only collisions (`Hotel-Receipt` vs
  `Hotel-receipt`) so they survive case-insensitive filesystems.
- Some numeric fields arrive unquoted (`"total": 274.18`); the schema coerces them.
- Scraping is resumable — existing files are reused, so re-running only fetches gaps.
