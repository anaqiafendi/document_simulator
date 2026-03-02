# Feature: CLI

> **GitHub Issue:** `#12`
> **Status:** `complete`
> **Module:** `document_simulator.cli`

---

## Summary

An `argparse`-based command-line interface exposing three subcommands — `augment`, `ocr`, and `train` — that wrap the package's core functionality without requiring the caller to write Python. Invoked via `python -m document_simulator` using `__main__.py`.

---

## Motivation

### Problem Statement

Scripts and CI pipelines need to run augmentation and OCR without embedding Python code. A standard CLI with `--help` support and non-zero exit codes on error makes the package scriptable and easy to integrate into shell pipelines.

### Value Delivered

- Three self-documenting subcommands with `--help` output.
- Non-zero exit code and logged error on any exception — safe for shell scripting.
- `augment` uses `DocumentAugmenter.augment_file()` — a single call, no I/O boilerplate.
- `ocr` prints extracted text to stdout or saves to a file with `--output`.
- `train` passes through to the RL trainer (currently delegates to `PipelineOptimizer`).
- `--version` reports `0.1.0`.

---

## User Stories

| Role | Goal | So That |
|------|------|---------|
| Script author | I run `augment input.jpg output.jpg --pipeline heavy` | I get an augmented image without writing Python |
| Data engineer | I run `ocr document.jpg --output extracted.txt` | I get a text file of extracted content |
| CI pipeline | I check the exit code of `augment` | I detect errors without parsing log output |

---

## Acceptance Criteria

- [ ] AC-1: `python -m document_simulator --help` exits `0` and prints "document".
- [ ] AC-2: `python -m document_simulator --version` exits `0`.
- [ ] AC-3: `python -m document_simulator` (no subcommand) exits `0` and prints help.
- [ ] AC-4: `augment input.jpg output.jpg` exits `0` and creates `output.jpg`.
- [ ] AC-5: `augment input.jpg output.jpg --pipeline light` exits `0` and creates the file.
- [ ] AC-6: `augment /nonexistent/image.jpg out.jpg` exits non-zero.

---

## Design

### Public API

```bash
uv run python -m document_simulator --help
uv run python -m document_simulator --version

uv run python -m document_simulator augment input.jpg output.jpg
uv run python -m document_simulator augment input.jpg output.jpg --pipeline heavy

uv run python -m document_simulator ocr document.jpg
uv run python -m document_simulator ocr document.jpg --output result.txt --use-gpu

uv run python -m document_simulator train --data-dir ./data/train --num-steps 100000 --output-dir ./models
```

### Data Flow

```
python -m document_simulator augment input output [--pipeline PRESET]
    │
    ▼
DocumentAugmenter(pipeline=preset).augment_file(input, output)
    │
    ▼
exit(0) on success / exit(1) + logger.error on exception

python -m document_simulator ocr input [--output FILE] [--use-gpu]
    │
    ▼
OCREngine(use_gpu=use_gpu).recognize_file(input)
    │
    ├─► [--output FILE] → output_path.write_text(result["text"])
    └─► [no --output]  → print(result["text"])
```

### Key Interfaces

| Symbol | Kind | Responsibility |
|--------|------|---------------|
| `main()` | function | `argparse` setup + subcommand dispatch |
| `__main__.py` | module | Entry point for `python -m document_simulator` |

### Configuration

No `.env` settings at the CLI level — subsystems use their own settings.

---

## Implementation

### Files

| Path | Role |
|------|------|
| `src/document_simulator/cli.py` | `main()` function with argparse and subcommand dispatch |
| `src/document_simulator/__main__.py` | `from .cli import main; sys.exit(main())` |

### Key Architectural Decisions

1. **`__main__.py` required** — `python -m document_simulator` invokes `__main__.py`. Without it, the package is not directly runnable as a module. This file is a single delegation call to `main()`.

2. **Late imports inside command branches** — `DocumentAugmenter`, `OCREngine`, and `PipelineOptimizer` are imported inside each `if args.command == "..."` block, not at the top of `cli.py`. This keeps startup fast (no heavy model loading) when the user just runs `--help` or `--version`.

3. **Catch all exceptions and log, then return 1** — Rather than letting exceptions propagate to the shell as an uncaught traceback, the CLI catches them, logs with loguru, and returns `1`. The caller gets a clean error signal and the loguru message explains what happened.

4. **`argparse` over `click`** — `argparse` is stdlib. `click` would be cleaner but adds a dependency. For three subcommands, `argparse` is sufficient.

### Known Edge Cases & Constraints

- `train` subcommand currently routes to `PipelineOptimizer` (a stub in `rl/optimizer.py`) rather than `RLTrainer`. This is a known gap — the UI RL Training page is the primary training interface.
- `ocr --use-gpu` passes the flag to `OCREngine(use_gpu=True)` but does not validate GPU availability — that is handled by PaddleOCR internally.

---

## Tests

### Test Files

| File | Type | Count | What is covered |
|------|------|-------|-----------------|
| `tests/e2e/test_cli.py` | e2e | 6 | `--help`, `--version`, no-command, `augment` default, `augment --pipeline light`, nonexistent input |

### TDD Cycle Summary

**Red — first failing tests written:**

| Test name | File | Initial failure reason |
|-----------|------|----------------------|
| `test_cli_help` | `tests/e2e/test_cli.py` | `ModuleNotFoundError: No module named 'document_simulator.__main__'` |
| `test_cli_augment_command` | `tests/e2e/test_cli.py` | `ModuleNotFoundError: No module named 'document_simulator.__main__'` |
| `test_cli_augment_nonexistent_input` | `tests/e2e/test_cli.py` | `ModuleNotFoundError: No module named 'document_simulator.__main__'` |

**Green — minimal implementation:**

Created `__main__.py` with `from .cli import main; sys.exit(main())`. Created `cli.py` with argparse setup. Implemented `augment` branch first — the most mechanical. Added `ocr` branch. Left `train` as a stub that would raise `ImportError` on `PipelineOptimizer`. All 6 tests passed because `test_cli_augment_nonexistent_input` checks for non-zero exit code — the exception in the augment branch satisfies this.

**Refactor — improvements made after green:**

| What changed | Why |
|--------------|-----|
| Moved all domain imports inside command branches | `--help` was taking ~2s due to PaddleOCR import at module level; moved to inside `elif args.command == "ocr":` |

### How to Run

```bash
uv run pytest tests/e2e/test_cli.py -v
uv run pytest tests/e2e/test_cli.py --cov=document_simulator.cli
```

---

## Dependencies

### Requires

| Dependency | Kind | Why |
|------------|------|-----|
| `argparse` | stdlib | Subcommand parsing |
| `loguru` | external | Structured error logging |
| `augmentation/augmenter.py` | internal | `DocumentAugmenter` (late import) |
| `ocr/engine.py` | internal | `OCREngine` (late import) |

### Required By

No internal consumers — the CLI is a terminal interface, not a library.

---

## Usage Examples

### Minimal

```bash
uv run python -m document_simulator augment scan.jpg scan_degraded.jpg
```

### Typical

```bash
# Augment with heavy preset
uv run python -m document_simulator augment invoice.jpg invoice_heavy.jpg --pipeline heavy

# OCR and save to file
uv run python -m document_simulator ocr invoice.jpg --output invoice_text.txt

# RL training
uv run python -m document_simulator train \
    --data-dir ./data/train \
    --num-steps 500000 \
    --output-dir ./models
```

### Advanced / Edge Case

```bash
# Wrap in a shell script for batch processing
for f in data/raw/*.jpg; do
  out="data/aug/$(basename "$f")"
  uv run python -m document_simulator augment "$f" "$out" --pipeline medium
  if [ $? -ne 0 ]; then
    echo "Failed: $f"
  fi
done
```

---

## Future Work

- [ ] Wire `train` subcommand to `RLTrainer` instead of `PipelineOptimizer` stub.
- [ ] Add `evaluate` subcommand for dataset-level CER/WER benchmarking.
- [ ] Add `batch` subcommand wrapping `BatchAugmenter.augment_directory()`.
- [ ] Add `--lang` and `--gpu` to `ocr` subcommand (currently only `--use-gpu` flag).

---

## References

- [feature_document_augmenter.md](feature_document_augmenter.md)
- [feature_ocr_engine.md](feature_ocr_engine.md)
- [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md)
