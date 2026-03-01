# Research Findings: Document Simulator

## Project Overview

This project aims to build a **document simulator** that can:
1. Generate variations of scanned document images based on input samples
2. Modify specific values/fields within documents programmatically
3. Serve as a red teaming tool for testing document extraction and OCR systems
4. Generate synthetic training data for RL tuning of extraction and OCR models

The goal is to create realistic document variations to improve the robustness and accuracy of document processing models.

---

## 1. Document Image Augmentation

### Augraphy (Recommended Primary Tool)
- Python library specifically designed for document image augmentation
- 100+ augmentation effects designed for documents
- Simulates ink, paper, post-processing, and markup effects
- Pipeline-based architecture for combining effects
- Installation: `pip install augraphy`
- GitHub: https://github.com/sparkfish/augraphy

### Albumentations
- General-purpose image augmentation with document-relevant transforms
- Fast performance (uses OpenCV)
- Geometric transforms, color/brightness adjustments, noise and blur
- Installation: `pip install albumentations`
- Documentation: https://albumentations.ai/

### Document-Specific Augmentation Techniques
1. **Geometric**: Perspective distortion, rotation, skew, warping
2. **Degradation**: Paper texture/aging, ink bleeding/fading, watermarks, stains, crumpling
3. **Scanning Artifacts**: Scanner noise, shadows, lighting variations, motion blur, defocus
4. **Post-processing**: JPEG compression, resolution changes, contrast adjustments, binarization

---

## 2. OCR and Document Extraction

### OCR Engines

| Engine | Type | Languages | Best For |
|--------|------|-----------|----------|
| **PaddleOCR** | Deep learning | Multi-language | Best accuracy/speed balance |
| **EasyOCR** | Deep learning | 80+ | Complex layouts |
| **Tesseract** | Traditional + LSTM | 100+ | Baseline comparison |

### Document Understanding Models

- **LayoutLM / LayoutLMv3** (Microsoft) — Combines text, layout, and image; pre-trained on millions of documents; available via Hugging Face
- **Donut** — OCR-free document understanding; end-to-end transformer model
- **TrOCR** — Transformer-based OCR; state-of-the-art text recognition

### Cloud Services (for benchmarking)
- Google Cloud Vision API
- AWS Textract
- Azure Computer Vision / Form Recognizer

---

## 3. Reinforcement Learning for Document Processing

### RL Frameworks

| Framework | Backend | Best For |
|-----------|---------|----------|
| **Stable-Baselines3** | PyTorch | Primary RL framework (well-documented) |
| **Ray RLlib** | Multiple | Large-scale distributed training |
| **TF-Agents** | TensorFlow | TF ecosystem projects |

### RL Problem Formulation
- **State**: Document image + current extraction results
- **Action**: Select regions, adjust parameters, choose extraction methods
- **Reward**: Accuracy of extracted information vs. ground truth
- **Goal**: Learn optimal extraction strategy for various document types

### Training Considerations
- Reward shaping is critical (sparse rewards are challenging)
- May need curriculum learning (start with easy documents)
- Combination with supervised learning likely optimal
- Consider imitation learning from expert extraction rules

---

## 4. Synthetic Document Generation

### Template-Based Generation
- **ReportLab** — Programmatic PDF creation (`pip install reportlab`)
- **Pillow (PIL)** — Image creation, text rendering, format conversion
- **Faker** — Realistic fake data (names, addresses, dates, amounts) (`pip install faker`)
- **python-docx** — Word document generation (`pip install python-docx`)

### Generative AI Approaches
- **Diffusion Models / ControlNet** — Generate realistic document backgrounds/textures
- **GANs** — Learn to generate document-like images (research-level)

---

## 5. Value Modification and Field Replacement

### Approaches

#### OCR + Template Matching
1. Use OCR to locate existing values
2. Identify field types (dates, amounts, names)
3. Replace with synthetic values using similar formatting
4. Re-render with matching fonts and styling

#### Inpainting + Text Rendering
1. Use image inpainting to remove existing text (`cv2.inpaint()`)
2. Render new text with matching font/style (Pillow ImageDraw)
3. For advanced cases: LaMa, Stable Diffusion inpainting

#### PDF Layer Manipulation (for digital documents)
1. Parse PDF text layers (PyPDF2, pdfplumber)
2. Modify text content programmatically
3. Re-render to image (pdf2image)

### Font Matching
- **fontTools** (`pip install fonttools`) — Parse and extract font metrics
- **Pillow + system fonts** — Render text with specific fonts

---

## 6. Data Annotation and Ground Truth

- **Label Studio** — Open-source data labeling with OCR integration (`pip install label-studio`)
- **CVAT** — Annotation tool from Intel, good for bounding boxes
- **VGG Image Annotator (VIA)** — Lightweight browser-based annotation

---

## 7. Recommended Tech Stack

### Core
| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Augmentation | Augraphy, Albumentations |
| Image Processing | Pillow, OpenCV, NumPy |
| OCR | PaddleOCR (primary), Tesseract (baseline) |
| Document Understanding | LayoutLM via Hugging Face Transformers |

### Synthetic Data
| Component | Technology |
|-----------|-----------|
| Fake Data | Faker |
| PDF Generation | ReportLab |
| DOCX Generation | python-docx |

### RL Training
| Component | Technology |
|-----------|-----------|
| RL Framework | Stable-Baselines3 |
| Deep Learning | PyTorch |
| Experiment Tracking | Weights & Biases or MLflow |

### Data Management
| Component | Technology |
|-----------|-----------|
| Annotation | Label Studio |
| Version Control | DVC |
| Metadata Storage | SQLite or PostgreSQL |

---

## 8. Proposed Pipeline

```
1. Template Creation
   - Create base document templates (ReportLab/python-docx)
   - Define field locations and types

2. Value Variation
   - Generate synthetic values (Faker)
   - Modify document fields programmatically

3. Image Augmentation
   - Apply Augraphy augmentation pipeline
   - Generate multiple variations per document
   - Simulate real-world scanning conditions

4. Ground Truth Management
   - Track original values and locations
   - Store metadata (field types, positions, values)

5. RL Training Pipeline
   - Feed augmented documents to extraction model
   - Calculate reward based on extraction accuracy
   - Update RL policy, iterate

6. Evaluation
   - Test on held-out documents
   - Measure extraction accuracy
   - Analyze failure modes
```

---

## 9. Feasibility Assessment

### Technical Feasibility: HIGH

**Strengths:**
- Mature libraries exist for all core components
- Document augmentation is a solved problem (Augraphy)
- OCR technology is production-ready
- RL frameworks are well-established

### Implementation Complexity: MEDIUM

| Component | Estimated Time |
|-----------|---------------|
| Basic augmentation pipeline | 1-2 weeks |
| OCR integration | 1 week |
| Template-based generation | 2 weeks |
| Value modification with font matching | 2-3 weeks |
| RL integration and reward design | 3-4 weeks |
| End-to-end pipeline | 2 weeks |
| **Total MVP** | **8-12 weeks** |

---

## 10. Potential Challenges & Mitigations

| Challenge | Mitigation |
|-----------|-----------|
| Font matching for realistic text replacement | Start with digital PDFs; use deep learning inpainting for complex cases |
| RL reward function design | Start with supervised baseline; use dense per-field rewards |
| Unrealistic augmentations harming training | Use Augraphy (research-validated); validate with domain experts |
| Tracking field locations through augmentations | Use coordinate-aware augmentation; store transformation matrices |
| Scalability (millions of variations) | Parallelize pipeline; use efficient OpenCV processing; cache results |

---

## 11. Alternative Approaches

| Approach | When to Use | Trade-offs |
|----------|-------------|-----------|
| Generative models (GANs/diffusion) | Need entirely novel documents | Higher compute, less controllable |
| Supervised learning (no RL) | Simpler baseline needed | Less adaptive, needs more labeled data |
| Commercial Document AI | Benchmarking only | Cost per doc, vendor lock-in, privacy concerns |
| Active learning + synthetic | Have some real documents | Better generalization, needs human annotation |

---

## 12. MVP Specification (4 Weeks)

**Input:** 10 sample document images + CSV with field values to modify
**Processing:** Generate 100 variations per document (1,000 total)
**Output:** Augmented images + ground truth JSON with field locations and values
**Evaluation:** Run OCR, measure extraction accuracy, compare with baseline

**MVP Stack:** Python 3.10+, Augraphy, Pillow, PaddleOCR, Faker, pandas, matplotlib

---

## 13. References & Resources

### Libraries
- Augraphy: https://github.com/sparkfish/augraphy
- Albumentations: https://albumentations.ai/
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- EasyOCR: https://github.com/JaidedAI/EasyOCR
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/
- Label Studio: https://labelstud.io/

### Models (Hugging Face)
- LayoutLM: https://huggingface.co/models?search=layoutlm
- Donut: https://huggingface.co/naver-clova-ix/donut-base
- TrOCR: https://huggingface.co/models?search=trocr

### Papers
- "Augraphy: A Data Augmentation Library for Document Images" (2022)
- "LayoutLMv3: Pre-training for Document AI with Unified Text and Image Masking" (2022)
- "Donut: Document Understanding Transformer without OCR" (2022)

---

## Conclusion

This project is highly feasible using existing open-source technologies. The recommended approach is:

1. **Phase 1-3**: Build solid augmentation and extraction pipeline
2. **Phase 4**: Add RL capabilities once foundation is stable
3. **Iterate** based on evaluation metrics

**Key Success Factors:**
- Leverage proven libraries (especially Augraphy)
- Start simple before adding RL complexity
- Build robust ground truth management from the beginning
- Focus on practical, incremental improvements
