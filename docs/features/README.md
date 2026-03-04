# Feature Index

This directory documents every implemented feature in the **document_simulator** project using Feature-Driven Development (FDD).

Each file follows [`feature_template.md`](feature_template.md) and links to the GitHub issue that drove it.

---

## Core Backend

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #1 | [Augmentation Presets](feature_augmentation_presets.md) | `augmentation.presets` | complete |
| #2 | [Document Augmenter](feature_document_augmenter.md) | `augmentation.augmenter` | complete |
| #3 | [Batch Processing](feature_batch_processing.md) | `augmentation.batch` | complete |
| #4 | [OCR Engine](feature_ocr_engine.md) | `ocr.engine` | complete |
| #5 | [OCR Metrics](feature_ocr_metrics.md) | `ocr.metrics` | complete |
| #6 | [Image I/O](feature_image_io.md) | `utils.image_io` | complete |
| #7 | [Ground Truth Loading](feature_ground_truth.md) | `data.ground_truth` | complete |
| #8 | [Document Dataset](feature_document_dataset.md) | `data.datasets` | complete |
| #9 | [RL Environment](feature_rl_environment.md) | `rl.environment` | complete |
| #10 | [RL Trainer](feature_rl_trainer.md) | `rl.trainer` | complete |
| #11 | [Evaluation Framework](feature_evaluation.md) | `evaluation.evaluator` | complete |
| #12 | [CLI](feature_cli.md) | `cli` + `__main__` | complete |

## UI

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #13 | [UI Shared Components](feature_ui_components.md) | `ui.components.*` + `ui.state` | complete |
| #14 | [Augmentation Lab](feature_ui_augmentation_lab.md) | `ui.pages.01_augmentation_lab` | complete |
| #15 | [OCR Engine Page](feature_ui_ocr_engine.md) | `ui.pages.02_ocr_engine` | complete |
| #16 | [Batch Processing Page](feature_ui_batch_processing.md) | `ui.pages.03_batch_processing` | complete |
| #17 | [Evaluation Dashboard](feature_ui_evaluation_dashboard.md) | `ui.pages.04_evaluation` | complete |
| #18 | [RL Training Page](feature_ui_rl_training.md) | `ui.pages.05_rl_training` | complete |

---

## Template

New features should be documented using [`feature_template.md`](feature_template.md).
