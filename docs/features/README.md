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
| #21 | [Augmentation Lab Catalogue](feature_augmentation_lab_catalogue.md) | `augmentation.catalogue` + `ui.pages.01_augmentation_lab` | done |
| #22 | [Multi-Template Batch Augmentation](feature_multi_template_batch.md) | `augmentation.batch` + `ui.pages.03_batch_processing` | done |
| #23 | [Augraphy Full Catalogue (51 Classes)](feature_augraphy_full_catalogue.md) | `augmentation.catalogue` + `ui.pages.01_augmentation_lab` | done |

## Synthesis

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #19 | [Synthetic Document Generator](feature_synthetic_document_generator.md) | `synthesis.*` | planned |
| #20 | [React Zone Editor UI](feature_js_zone_editor_ui.md) | `api.*` + `webapp/` | complete |
| #25 | [Migrate Streamlit Pages to React SPA](feature_migrate_streamlit_to_react.md) | `api.routers.*` + `webapp/src/pages/*` | in-progress |

## Deployment

| # | Feature | Module | Status |
|---|---------|--------|--------|
| #24 | [Free Hosting Deployment](feature_free_hosting_deployment.md) | `Dockerfile` + `.github/workflows/` | complete |

---

## Template

New features should be documented using [`feature_template.md`](feature_template.md).
