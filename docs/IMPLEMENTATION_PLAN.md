# IMPLEMENTATION_PLAN.md - Document Simulator

## 1. Overview

### Project Goals

The Document Simulator is a comprehensive system designed to:

- **Generate augmented document images** using Augraphy's 100+ realistic transformations to simulate real-world document degradation (scanning artifacts, paper aging, ink bleeding, etc.)
- **Extract text from documents** using PaddleOCR's state-of-the-art multi-language OCR engine with text detection and recognition
- **Optimize augmentation pipelines** using reinforcement learning (Stable-Baselines3) to balance document realism with OCR accuracy
- **Create training datasets** for OCR and document extraction models by applying controlled variations to sample documents
- **Enable red-team testing** of document processing systems by generating edge cases and challenging document variations

### Use Cases

1. **OCR Model Training**: Generate diverse training data from limited document samples
2. **Model Robustness Testing**: Test OCR systems against various degradation scenarios
3. **Data Augmentation**: Expand small document datasets for machine learning
4. **RL-based Optimization**: Learn optimal augmentation parameters for specific document types
5. **Red Team Testing**: Stress-test extraction systems with challenging document variations

### Success Metrics

- **Augmentation Quality**: Generate realistic document variations indistinguishable from real scans
- **OCR Accuracy**: Maintain >85% character accuracy on heavily augmented documents
- **RL Performance**: Achieve 20%+ improvement in OCR accuracy through optimized augmentation
- **Processing Speed**: <100ms augmentation, <500ms OCR (CPU), <50ms OCR (GPU)
- **Code Coverage**: >80% test coverage across all modules

---

## 2. Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Simulator System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Document   │───▶│ Augmentation │───▶│     OCR      │       │
│  │   Loader    │    │   Pipeline   │    │    Engine    │       │
│  │  (Utils)    │    │ (Augraphy)   │    │ (PaddleOCR)  │       │
│  └─────────────┘    └──────┬───────┘    └──────────────┘       │
│                             │                     │              │
│                             │                     │              │
│                      ┌──────▼─────────────────────▼──────┐      │
│                      │      RL Optimization Layer       │      │
│                      │    (Stable-Baselines3 + Gym)     │      │
│                      │                                   │      │
│                      │  - DocumentEnv (Gym)              │      │
│                      │  - Reward Function (OCR Quality)  │      │
│                      │  - PPO/DQN Agents                 │      │
│                      │  - Parameter Optimization         │      │
│                      └───────────────────────────────────┘      │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               Data & Model Management                       │ │
│  │  - Dataset Loaders (ICDAR, SROIE, Custom)                  │ │
│  │  - Ground Truth Parsers (JSON, XML, TXT)                   │ │
│  │  - Model Checkpointing & Versioning                        │ │
│  │  - Metrics & Evaluation (CER, WER, Levenshtein)           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Infrastructure                             │ │
│  │  - CLI (augment, ocr, train, evaluate)                     │ │
│  │  - Configuration (Pydantic Settings)                       │ │
│  │  - Logging (Loguru + TensorBoard + W&B)                    │ │
│  │  - Testing Framework (Pytest + Coverage)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input Document ──┐
                 │
                 ├──▶ [1] Augmentation Pipeline (Augraphy)
                 │      ├─ Ink Phase: InkBleed, Markup, Fading
                 │      ├─ Paper Phase: Noise, Wrinkles, Watermarks
                 │      └─ Post Phase: Blur, Brightness, JPEG
                 │
                 ├──▶ [2] OCR Engine (PaddleOCR)
                 │      ├─ Text Detection (bounding boxes)
                 │      ├─ Text Recognition (characters)
                 │      └─ Quality Metrics (confidence scores)
                 │
                 └──▶ [3] RL Agent (Optional)
                        ├─ Observe: Document features
                        ├─ Action: Augmentation parameters
                        ├─ Reward: OCR accuracy vs. realism
                        └─ Learn: Optimal parameter policy
                             
Output: Augmented Images + OCR Results + Trained Models
```

### Key Design Patterns

1. **Strategy Pattern**: Multiple augmentation pipeline presets (light, medium, heavy)
2. **Factory Pattern**: Create augmentation pipelines and RL environments
3. **Observer Pattern**: Callbacks for training progress and model checkpointing
4. **Adapter Pattern**: Unified interface for different image formats (PIL, numpy, paths)
5. **Configuration Pattern**: Centralized settings via Pydantic

---

## 3. Implementation Phases

### Phase 1: Foundation & Core Augmentation (Week 1)

**Goal**: Establish robust augmentation pipeline with comprehensive testing.

#### Phase 1.1: Enhanced Augmentation Presets (Days 1-2)

**RED: Write Failing Tests**

```python
# tests/test_augmentation_presets.py

def test_light_preset_maintains_readability():
    """Light preset should maintain high OCR accuracy (>95%)."""
    # Create sample document with known text
    # Apply light augmentation
    # Run OCR and verify accuracy >95%
    assert False  # Will fail until implemented

def test_heavy_preset_realistic_degradation():
    """Heavy preset should create significant visual changes."""
    # Create pristine document
    # Apply heavy augmentation
    # Measure image similarity (SSIM < 0.8)
    assert False

def test_preset_reproducibility_with_seed():
    """Same seed should produce identical augmentations."""
    # Apply augmentation with seed=42 twice
    # Compare pixel-by-pixel equality
    assert False

def test_preset_parameter_bounds():
    """Augmentation parameters should stay within valid ranges."""
    # Test each preset's parameter values
    # Verify 0.0 <= probability <= 1.0
    assert False
```

**GREEN: Implement Minimal Code**

```python
# src/document_simulator/augmentation/presets.py

from dataclasses import dataclass
from typing import List
from augraphy.augmentations import *

@dataclass
class AugmentationPreset:
    """Defines augmentation pipeline configuration."""
    name: str
    ink_phase: List
    paper_phase: List
    post_phase: List
    
class PresetFactory:
    """Factory for creating augmentation presets."""
    
    @staticmethod
    def create_light():
        """Light degradation for clean documents."""
        return AugmentationPreset(
            name="light",
            ink_phase=[
                InkBleed(p=0.2, intensity_range=(0.1, 0.3)),
                Fading(p=0.2, fading_value_range=(0.1, 0.2))
            ],
            paper_phase=[
                NoiseTexturize(p=0.3, sigma_range=(3, 5)),
                ColorShift(p=0.2, shift_range=(5, 10))
            ],
            post_phase=[
                Brightness(p=0.3, brightness_range=(0.9, 1.1)),
                Jpeg(p=0.2, quality_range=(85, 95))
            ]
        )
    
    @staticmethod
    def create_heavy():
        """Heavy degradation for robustness testing."""
        # Implementation for heavy preset
        pass
```

**REFACTOR: Clean Up**

- Extract magic numbers to constants
- Add type hints and docstrings
- Optimize parameter ranges based on testing
- Create preset validation logic

#### Phase 1.2: Image Format Handlers (Day 3)

**RED: Write Failing Tests**

```python
# tests/test_image_handlers.py

def test_load_from_path():
    """Load image from file path."""
    assert False

def test_load_from_pil():
    """Load PIL Image object."""
    assert False

def test_load_from_numpy():
    """Load numpy array."""
    assert False

def test_load_from_bytes():
    """Load image from bytes buffer."""
    assert False

def test_batch_loading():
    """Load multiple images efficiently."""
    assert False

def test_format_preservation():
    """Output format matches input format."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/utils/image_io.py

class ImageHandler:
    """Unified interface for loading/saving images."""
    
    @staticmethod
    def load(source):
        """Load image from various sources."""
        if isinstance(source, (str, Path)):
            return Image.open(source)
        elif isinstance(source, Image.Image):
            return source
        elif isinstance(source, np.ndarray):
            return Image.fromarray(source)
        elif isinstance(source, bytes):
            return Image.open(io.BytesIO(source))
        raise TypeError(f"Unsupported image type: {type(source)}")
```

**REFACTOR**: Add error handling, validation, format conversion utilities.

#### Phase 1.3: Batch Processing & Parallelization (Days 4-5)

**RED: Write Tests**

```python
# tests/test_batch_processing.py

def test_batch_augmentation_sequential():
    """Process batch sequentially."""
    assert False

def test_batch_augmentation_parallel():
    """Process batch with multiprocessing."""
    assert False

def test_batch_performance_scaling():
    """Parallel processing should be faster for large batches."""
    # Time sequential vs parallel on 100 images
    assert parallel_time < sequential_time * 0.6

def test_batch_memory_efficiency():
    """Batch processing should not exceed memory limits."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/augmentation/batch.py

from multiprocessing import Pool
from typing import List

class BatchAugmenter:
    """Batch augmentation with parallelization."""
    
    def __init__(self, augmenter, num_workers=4):
        self.augmenter = augmenter
        self.num_workers = num_workers
    
    def augment_batch(self, images, parallel=True):
        """Augment multiple images."""
        if parallel:
            with Pool(self.num_workers) as pool:
                return pool.map(self.augmenter.augment, images)
        else:
            return [self.augmenter.augment(img) for img in images]
```

**REFACTOR**: Add progress bars, error recovery, chunking strategies.

---

### Phase 2: OCR Integration & Metrics (Week 2)

#### Phase 2.1: OCR Quality Metrics (Days 1-2)

**RED: Write Tests**

```python
# tests/test_ocr_metrics.py

def test_character_error_rate():
    """Calculate CER between predicted and ground truth."""
    predicted = "hello world"
    ground_truth = "helo world!"
    cer = calculate_cer(predicted, ground_truth)
    assert 0.0 <= cer <= 1.0
    assert False  # Will fail until implemented

def test_word_error_rate():
    """Calculate WER."""
    assert False

def test_levenshtein_distance():
    """Calculate edit distance."""
    assert False

def test_confidence_aggregation():
    """Aggregate per-character confidence scores."""
    assert False

def test_bounding_box_iou():
    """Calculate IoU for text region detection."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/ocr/metrics.py

import Levenshtein

def calculate_cer(predicted: str, ground_truth: str) -> float:
    """Character Error Rate using Levenshtein distance."""
    if len(ground_truth) == 0:
        return 0.0 if len(predicted) == 0 else 1.0
    
    distance = Levenshtein.distance(predicted, ground_truth)
    return distance / len(ground_truth)

def calculate_wer(predicted: str, ground_truth: str) -> float:
    """Word Error Rate."""
    pred_words = predicted.split()
    gt_words = ground_truth.split()
    
    if len(gt_words) == 0:
        return 0.0 if len(pred_words) == 0 else 1.0
    
    distance = Levenshtein.distance(' '.join(pred_words), ' '.join(gt_words))
    return distance / len(gt_words)
```

**REFACTOR**: Add normalization, case handling, punctuation options.

#### Phase 2.2: Ground Truth Management (Days 3-4)

**RED: Write Tests**

```python
# tests/test_ground_truth.py

def test_load_json_ground_truth():
    """Load ground truth from JSON format."""
    assert False

def test_load_xml_ground_truth():
    """Load ground truth from XML format (ICDAR style)."""
    assert False

def test_validate_ground_truth_schema():
    """Validate ground truth structure."""
    assert False

def test_ground_truth_bounding_boxes():
    """Parse bounding box coordinates."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/data/ground_truth.py

from pathlib import Path
import json
from typing import Dict, List
from pydantic import BaseModel

class TextRegion(BaseModel):
    """Represents a text region with bounding box."""
    box: List[List[float]]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    text: str
    confidence: float = 1.0

class GroundTruth(BaseModel):
    """Ground truth data for a document."""
    image_path: str
    text: str
    regions: List[TextRegion]

class GroundTruthLoader:
    """Load ground truth from various formats."""
    
    @staticmethod
    def load_json(path: Path) -> GroundTruth:
        """Load from JSON format."""
        with open(path) as f:
            data = json.load(f)
        return GroundTruth(**data)
```

**REFACTOR**: Add format auto-detection, validation, error handling.

#### Phase 2.3: Dataset Loaders (Day 5)

**RED: Write Tests**

```python
# tests/test_datasets.py

def test_load_icdar_dataset():
    """Load ICDAR format dataset."""
    assert False

def test_load_custom_dataset():
    """Load custom dataset with paired images/labels."""
    assert False

def test_dataset_iteration():
    """Iterate through dataset samples."""
    assert False

def test_dataset_train_val_split():
    """Split dataset into train/validation sets."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/data/datasets.py

from torch.utils.data import Dataset
from pathlib import Path

class DocumentDataset(Dataset):
    """PyTorch dataset for document images."""
    
    def __init__(self, data_dir: Path, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        self.samples = self._load_samples()
    
    def _load_samples(self):
        """Load image-label pairs."""
        # Implementation
        pass
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        image_path, gt_path = self.samples[idx]
        image = ImageHandler.load(image_path)
        gt = GroundTruthLoader.load_json(gt_path)
        
        if self.transform:
            image = self.transform(image)
        
        return image, gt
```

**REFACTOR**: Add caching, lazy loading, data validation.

---

### Phase 3: RL Environment & Training (Week 3)

#### Phase 3.1: DocumentEnv Implementation (Days 1-3)

**RED: Write Tests**

```python
# tests/test_rl_env.py

def test_env_initialization():
    """Environment initializes correctly."""
    env = DocumentEnv()
    assert env.action_space is not None
    assert env.observation_space is not None

def test_env_reset():
    """Reset returns valid observation."""
    env = DocumentEnv()
    obs, info = env.reset()
    assert env.observation_space.contains(obs)

def test_env_step():
    """Step returns valid transitions."""
    env = DocumentEnv()
    obs, info = env.reset()
    action = env.action_space.sample()
    next_obs, reward, terminated, truncated, info = env.step(action)
    assert env.observation_space.contains(next_obs)
    assert isinstance(reward, (int, float))

def test_reward_calculation():
    """Reward reflects OCR quality."""
    # Apply known good augmentation -> high reward
    # Apply known bad augmentation -> low reward
    assert False

def test_action_to_parameters():
    """Actions map to valid augmentation parameters."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/rl/environment.py

import gymnasium as gym
import numpy as np
from document_simulator.augmentation import DocumentAugmenter
from document_simulator.ocr import OCREngine
from document_simulator.ocr.metrics import calculate_cer

class DocumentEnv(gym.Env):
    """RL environment for document augmentation optimization."""
    
    def __init__(self, dataset_path, target_degradation="medium"):
        super().__init__()
        
        # Load dataset
        self.dataset = DocumentDataset(dataset_path)
        self.current_idx = 0
        
        # Initialize OCR engine
        self.ocr = OCREngine(use_gpu=True)
        
        # Define spaces
        # Action: [ink_bleed_p, ink_bleed_intensity, noise_p, noise_sigma, ...]
        self.action_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(12,), dtype=np.float32
        )
        
        # Observation: Flattened image features + metadata
        self.observation_space = gym.spaces.Box(
            low=0.0, high=255.0, shape=(224, 224, 3), dtype=np.float32
        )
        
        self.target_degradation = target_degradation
    
    def reset(self, seed=None, options=None):
        """Load new document and return initial observation."""
        super().reset(seed=seed)
        
        # Load random document
        self.current_idx = np.random.randint(len(self.dataset))
        self.current_image, self.ground_truth = self.dataset[self.current_idx]
        
        # Convert image to observation
        obs = self._image_to_observation(self.current_image)
        
        return obs, {}
    
    def step(self, action):
        """Apply augmentation based on action and return reward."""
        # Map action to augmentation parameters
        aug_params = self._action_to_params(action)
        
        # Create custom augmenter with these parameters
        augmenter = self._create_augmenter(aug_params)
        
        # Apply augmentation
        augmented_image = augmenter.augment(self.current_image)
        
        # Run OCR
        ocr_result = self.ocr.recognize(augmented_image)
        
        # Calculate reward
        reward = self._calculate_reward(
            ocr_result, 
            self.ground_truth,
            augmented_image,
            self.current_image
        )
        
        # Next observation
        next_obs = self._image_to_observation(augmented_image)
        
        # Episode ends after one augmentation
        terminated = True
        truncated = False
        
        info = {
            "cer": calculate_cer(ocr_result["text"], self.ground_truth.text),
            "ocr_confidence": np.mean(ocr_result["scores"]),
            "params": aug_params
        }
        
        return next_obs, reward, terminated, truncated, info
    
    def _calculate_reward(self, ocr_result, ground_truth, aug_img, orig_img):
        """Composite reward balancing OCR accuracy and realism."""
        # Character accuracy (most important)
        cer = calculate_cer(ocr_result["text"], ground_truth.text)
        car = 1.0 - cer  # Character Accuracy Rate
        
        # Confidence score
        confidence = np.mean(ocr_result["scores"]) if ocr_result["scores"] else 0.0
        
        # Realism score (structural similarity)
        from skimage.metrics import structural_similarity as ssim
        ssim_score = ssim(
            np.array(orig_img), 
            np.array(aug_img),
            channel_axis=2
        )
        
        # Composite reward
        reward = (
            0.5 * car +           # Accuracy is most important
            0.3 * confidence +    # Confidence matters
            0.2 * (1 - ssim_score)  # Encourage visible augmentation
        )
        
        return reward
    
    def _action_to_params(self, action):
        """Convert continuous action to augmentation parameters."""
        return {
            "ink_bleed_p": action[0],
            "ink_bleed_intensity": action[1],
            "noise_p": action[2],
            "noise_sigma": action[3] * 10,  # Scale to [0, 10]
            # ... map remaining actions
        }
    
    def _create_augmenter(self, params):
        """Create augmenter from parameters."""
        # Build custom Augraphy pipeline from params
        pass
    
    def _image_to_observation(self, image):
        """Convert image to observation vector."""
        import cv2
        resized = cv2.resize(np.array(image), (224, 224))
        return resized.astype(np.float32)
```

**REFACTOR**: 
- Extract reward calculation to separate class
- Add observation normalization
- Optimize image feature extraction
- Add support for different reward strategies

#### Phase 3.2: PPO Training Pipeline (Days 4-5)

**RED: Write Tests**

```python
# tests/test_rl_training.py

def test_ppo_training_runs():
    """PPO training completes without errors."""
    assert False

def test_model_checkpointing():
    """Models are saved at checkpoints."""
    assert False

def test_tensorboard_logging():
    """Metrics are logged to TensorBoard."""
    assert False

def test_training_convergence():
    """Reward improves over training."""
    assert False

def test_model_save_load():
    """Trained model can be saved and loaded."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/rl/trainer.py

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    CheckpointCallback,
    EvalCallback,
    CallbackList
)
from stable_baselines3.common.env_util import make_vec_env

class RLTrainer:
    """Manages RL training workflow."""
    
    def __init__(self, config):
        self.config = config
        
        # Create vectorized environments
        self.train_env = make_vec_env(
            lambda: DocumentEnv(config.train_data_dir),
            n_envs=config.num_envs
        )
        
        self.eval_env = make_vec_env(
            lambda: DocumentEnv(config.val_data_dir),
            n_envs=1
        )
        
        # Initialize model
        self.model = PPO(
            "CnnPolicy",
            self.train_env,
            learning_rate=config.learning_rate,
            n_steps=config.n_steps,
            batch_size=config.batch_size,
            n_epochs=config.n_epochs,
            gamma=config.gamma,
            gae_lambda=config.gae_lambda,
            clip_range=config.clip_range,
            verbose=1,
            tensorboard_log=str(config.tensorboard_dir)
        )
    
    def train(self, total_timesteps):
        """Run training loop."""
        # Setup callbacks
        checkpoint_callback = CheckpointCallback(
            save_freq=10000,
            save_path=str(self.config.checkpoint_dir),
            name_prefix="ppo_document"
        )
        
        eval_callback = EvalCallback(
            self.eval_env,
            best_model_save_path=str(self.config.models_dir),
            log_path=str(self.config.logs_dir),
            eval_freq=5000,
            deterministic=True,
            render=False
        )
        
        callbacks = CallbackList([checkpoint_callback, eval_callback])
        
        # Train
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            progress_bar=True
        )
        
        return self.model
```

**REFACTOR**: Add learning rate scheduling, early stopping, hyperparameter tuning.

---

### Phase 4: Evaluation & Benchmarking (Week 4)

#### Phase 4.1: Evaluation Framework (Days 1-2)

**RED: Write Tests**

```python
# tests/test_evaluation.py

def test_evaluate_on_test_set():
    """Evaluate model on held-out test set."""
    assert False

def test_compute_aggregate_metrics():
    """Compute mean/std of metrics across test set."""
    assert False

def test_per_document_type_evaluation():
    """Evaluate separately by document type (receipt, form, etc.)."""
    assert False

def test_augmentation_ablation():
    """Test impact of individual augmentation techniques."""
    assert False
```

**GREEN: Implement**

```python
# src/document_simulator/evaluation/evaluator.py

class Evaluator:
    """Evaluation framework for document processing."""
    
    def __init__(self, augmenter, ocr_engine):
        self.augmenter = augmenter
        self.ocr = ocr_engine
    
    def evaluate_dataset(self, dataset):
        """Evaluate on full dataset."""
        results = []
        
        for image, ground_truth in tqdm(dataset):
            # Original
            orig_result = self.ocr.recognize(image)
            
            # Augmented
            aug_image = self.augmenter.augment(image)
            aug_result = self.ocr.recognize(aug_image)
            
            # Metrics
            results.append({
                "original_cer": calculate_cer(orig_result["text"], ground_truth.text),
                "augmented_cer": calculate_cer(aug_result["text"], ground_truth.text),
                "original_confidence": np.mean(orig_result["scores"]),
                "augmented_confidence": np.mean(aug_result["scores"]),
            })
        
        return self._aggregate_results(results)
    
    def _aggregate_results(self, results):
        """Compute statistics."""
        return {
            "mean_original_cer": np.mean([r["original_cer"] for r in results]),
            "mean_augmented_cer": np.mean([r["augmented_cer"] for r in results]),
            "std_original_cer": np.std([r["original_cer"] for r in results]),
            "std_augmented_cer": np.std([r["augmented_cer"] for r in results]),
        }
```

**REFACTOR**: Add visualization, report generation, comparison tools.

#### Phase 4.2: Benchmarking & Performance Testing (Days 3-4)

**RED: Write Tests**

```python
# tests/test_performance.py

def test_augmentation_speed():
    """Augmentation should complete in <100ms."""
    assert False

def test_ocr_speed_cpu():
    """CPU OCR should complete in <500ms."""
    assert False

def test_ocr_speed_gpu():
    """GPU OCR should complete in <50ms."""
    assert False

def test_memory_usage():
    """Memory usage should not exceed 2GB for single image."""
    assert False

def test_batch_throughput():
    """Batch processing should achieve >10 images/sec."""
    assert False
```

**GREEN: Implement**

```python
# tests/benchmarks/performance_tests.py

import time
import pytest
from memory_profiler import profile

class TestPerformance:
    
    @pytest.mark.benchmark
    def test_augmentation_latency(self, benchmark, sample_image):
        """Benchmark augmentation speed."""
        augmenter = DocumentAugmenter()
        
        result = benchmark(augmenter.augment, sample_image)
        
        # Assert <100ms
        assert benchmark.stats['mean'] < 0.1
    
    @profile
    def test_memory_footprint(self, sample_image):
        """Profile memory usage."""
        augmenter = DocumentAugmenter()
        result = augmenter.augment(sample_image)
        # Memory profiling will show usage
```

**REFACTOR**: Add continuous benchmarking, performance regression tests.

#### Phase 4.3: Documentation & Examples (Day 5)

**Tasks**:
- Generate API documentation with Sphinx/MkDocs
- Create Jupyter notebook tutorials
- Write usage examples for each component
- Document RL training workflow
- Create troubleshooting guide

---

## 4. Red/Green/Refactor TDD Approach

### TDD Cycle for Each Feature

```
┌─────────────────────────────────────────────────┐
│                  RED PHASE                       │
│  1. Write failing test that defines expected    │
│     behavior                                     │
│  2. Run test and confirm it fails               │
│  3. Understand WHY it fails (no implementation)  │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│                GREEN PHASE                       │
│  1. Write minimal code to make test pass        │
│  2. Avoid premature optimization                │
│  3. Run test and confirm it passes              │
│  4. Run ALL tests to ensure no regression       │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│               REFACTOR PHASE                     │
│  1. Clean up code (DRY, SOLID principles)       │
│  2. Improve naming and structure                │
│  3. Optimize for performance if needed          │
│  4. Run tests to ensure behavior unchanged      │
│  5. Update documentation                        │
└─────────────────┬───────────────────────────────┘
                  │
                  └─────────▶ Repeat for next feature
```

### Example: Implementing Custom Augmentation Preset

**RED Phase**

```python
# tests/test_augmentation_presets.py

def test_medical_preset_preserves_small_text():
    """Medical documents need to preserve small text (prescription details)."""
    # Given: Medical document with 8pt font text
    doc = create_medical_document_sample()
    augmenter = DocumentAugmenter(preset="medical")
    
    # When: Apply augmentation
    augmented = augmenter.augment(doc)
    
    # Then: OCR should still read small text with >90% accuracy
    ocr_result = OCREngine().recognize(augmented)
    cer = calculate_cer(ocr_result["text"], doc.ground_truth)
    assert cer < 0.1, f"CER {cer} too high for medical preset"
```

Run test: `pytest tests/test_augmentation_presets.py::test_medical_preset_preserves_small_text -v`

Expected output: `FAILED - KeyError: 'medical'` (preset doesn't exist yet)

**GREEN Phase**

```python
# src/document_simulator/augmentation/presets.py

class PresetFactory:
    
    @staticmethod
    def create_medical():
        """Preset optimized for medical documents with small text."""
        return AugmentationPreset(
            name="medical",
            ink_phase=[
                # Minimal ink degradation to preserve small text
                InkBleed(p=0.1, intensity_range=(0.05, 0.15)),
            ],
            paper_phase=[
                # Light paper texture
                NoiseTexturize(p=0.2, sigma_range=(1, 3)),
            ],
            post_phase=[
                # Avoid heavy blur that destroys small text
                Brightness(p=0.3, brightness_range=(0.95, 1.05)),
                Jpeg(p=0.1, quality_range=(90, 98)),
            ]
        )
```

Run test again: `PASSED` ✓

**REFACTOR Phase**

```python
# Improvement 1: Extract configuration constants
class PresetConfig:
    MEDICAL_INK_BLEED_PROB = 0.1
    MEDICAL_INK_INTENSITY = (0.05, 0.15)
    MEDICAL_NOISE_PROB = 0.2
    MEDICAL_NOISE_SIGMA = (1, 3)
    # ...

# Improvement 2: Add validation
@staticmethod
def create_medical():
    """Preset optimized for medical documents with small text.
    
    Design rationale:
    - Minimal ink bleeding to preserve fine details
    - Light noise texture for realism without degradation
    - Avoid heavy blur/compression
    - Suitable for prescriptions, lab reports, medical forms
    """
    preset = AugmentationPreset(...)
    validate_preset(preset)  # Ensure parameters in valid ranges
    return preset

# Improvement 3: Add builder pattern for customization
class PresetBuilder:
    def __init__(self, base_preset="medical"):
        self.preset = PresetFactory.create(base_preset)
    
    def with_ink_bleed(self, probability, intensity):
        # Customize ink bleed parameters
        return self
    
    def build(self):
        return self.preset
```

Run tests: All pass ✓

---

## 5. Test Strategy

### Testing Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │ ◀── 10% (Full pipeline integration)
                    │   (5-10 tests)  │
                    └─────────────────┘
                  ┌───────────────────────┐
                  │  Integration Tests    │ ◀── 30% (Component interactions)
                  │  (30-50 tests)        │
                  └───────────────────────┘
              ┌─────────────────────────────────┐
              │      Unit Tests                  │ ◀── 60% (Individual functions)
              │      (100-200 tests)             │
              └─────────────────────────────────┘
```

### Unit Tests (60% of test suite)

**What to test:**
- Individual functions and methods
- Edge cases and boundary conditions
- Error handling and validation
- Data transformations

**Examples:**

```python
# tests/unit/test_metrics.py

def test_cer_empty_strings():
    """CER of two empty strings should be 0."""
    assert calculate_cer("", "") == 0.0

def test_cer_identical_strings():
    """CER of identical strings should be 0."""
    assert calculate_cer("hello", "hello") == 0.0

def test_cer_completely_different():
    """CER of completely different strings."""
    assert calculate_cer("abc", "xyz") == 1.0

def test_cer_case_sensitive():
    """CER should be case-sensitive by default."""
    assert calculate_cer("Hello", "hello") > 0.0

def test_wer_with_extra_words():
    """WER calculation with insertions."""
    assert calculate_wer("hello world", "hello beautiful world") > 0.0
```

```python
# tests/unit/test_image_handlers.py

def test_load_invalid_path():
    """Loading invalid path should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        ImageHandler.load("/nonexistent/image.jpg")

def test_load_corrupt_image():
    """Loading corrupt image should raise appropriate error."""
    with pytest.raises(UnidentifiedImageError):
        ImageHandler.load("corrupt.jpg")

def test_convert_rgb_to_grayscale():
    """RGB to grayscale conversion."""
    rgb_img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    gray_img = ImageHandler.to_grayscale(rgb_img)
    assert gray_img.mode == "L"
```

### Integration Tests (30% of test suite)

**What to test:**
- Component interactions
- Data flow between modules
- External dependencies (PaddleOCR, Augraphy)
- File I/O operations

**Examples:**

```python
# tests/integration/test_augmentation_ocr.py

def test_augmentation_pipeline_to_ocr():
    """Test full augmentation -> OCR pipeline."""
    # Setup
    augmenter = DocumentAugmenter(preset="light")
    ocr = OCREngine(use_gpu=False)
    image = create_test_document(text="Hello World")
    
    # Execute
    augmented = augmenter.augment(image)
    result = ocr.recognize(augmented)
    
    # Verify
    assert "Hello" in result["text"]
    assert len(result["boxes"]) > 0
    assert all(0 <= score <= 1 for score in result["scores"])

def test_batch_augmentation_with_saving():
    """Test batch augmentation with file I/O."""
    augmenter = BatchAugmenter(num_workers=2)
    input_dir = Path("tests/fixtures/images")
    output_dir = Path("tests/output/augmented")
    
    augmenter.augment_directory(input_dir, output_dir)
    
    # Verify all files were processed
    assert len(list(output_dir.glob("*.jpg"))) == len(list(input_dir.glob("*.jpg")))
```

```python
# tests/integration/test_dataset_loading.py

def test_load_icdar_dataset():
    """Test loading real ICDAR dataset."""
    dataset = DocumentDataset(
        data_dir="tests/fixtures/icdar",
        format="icdar"
    )
    
    assert len(dataset) > 0
    
    # Test iteration
    image, gt = dataset[0]
    assert isinstance(image, Image.Image)
    assert isinstance(gt, GroundTruth)
    assert len(gt.text) > 0
```

### End-to-End Tests (10% of test suite)

**What to test:**
- Complete user workflows
- CLI commands
- RL training pipeline
- Performance benchmarks

**Examples:**

```python
# tests/e2e/test_cli.py

def test_cli_augment_command(tmp_path):
    """Test CLI augment command end-to-end."""
    input_img = tmp_path / "input.jpg"
    output_img = tmp_path / "output.jpg"
    
    # Create test image
    Image.new("RGB", (100, 100)).save(input_img)
    
    # Run CLI
    result = subprocess.run(
        ["document-simulator", "augment", str(input_img), str(output_img)],
        capture_output=True
    )
    
    # Verify
    assert result.returncode == 0
    assert output_img.exists()

def test_cli_ocr_command(tmp_path):
    """Test CLI OCR command."""
    input_img = create_test_document_image(text="Test Document")
    output_txt = tmp_path / "output.txt"
    
    result = subprocess.run(
        ["document-simulator", "ocr", str(input_img), "--output", str(output_txt)],
        capture_output=True
    )
    
    assert result.returncode == 0
    assert "Test Document" in output_txt.read_text()
```

```python
# tests/e2e/test_rl_training.py

@pytest.mark.slow
def test_rl_training_workflow(tmp_path):
    """Test complete RL training workflow."""
    # Setup test dataset
    train_dir = tmp_path / "train"
    setup_test_dataset(train_dir, num_samples=10)
    
    # Create config
    config = RLConfig(
        train_data_dir=train_dir,
        total_timesteps=1000,  # Short for testing
        num_envs=1
    )
    
    # Train
    trainer = RLTrainer(config)
    model = trainer.train(total_timesteps=1000)
    
    # Verify model was saved
    assert (tmp_path / "models" / "best_model.zip").exists()
    
    # Test inference
    test_image = create_test_document()
    action = model.predict(test_image)[0]
    assert action.shape == (12,)  # Expected action dimension
```

### Test Coverage Goals

| Module | Target Coverage | Critical Paths |
|--------|----------------|----------------|
| `augmentation/` | >85% | All presets, batch processing |
| `ocr/` | >80% | Recognize, metrics calculation |
| `rl/` | >75% | Environment step/reset, reward function |
| `data/` | >85% | Dataset loading, ground truth parsing |
| `utils/` | >90% | Image I/O, validation |
| **Overall** | **>80%** | All user-facing APIs |

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=document_simulator --cov-report=html

# Run only unit tests
uv run pytest tests/unit/

# Run integration tests (slower)
uv run pytest tests/integration/

# Run E2E tests (slowest, requires data)
uv run pytest tests/e2e/ --slow

# Run specific test
uv run pytest tests/unit/test_metrics.py::test_cer_empty_strings -v

# Run with parallel execution (faster)
uv run pytest -n auto

# Run benchmarks
uv run pytest tests/benchmarks/ --benchmark-only
```

### Continuous Integration

```yaml
# .github/workflows/test.yml

name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Setup Python ${{ matrix.python-version }}
        run: uv python pin ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          uv venv
          uv sync --all-extras
      
      - name: Run tests
        run: uv run pytest --cov --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 6. Critical Path & Dependencies

### Dependency Graph

```
Phase 1: Foundation
├── 1.1: Augmentation Presets ◀── (Start here, no dependencies)
├── 1.2: Image Handlers ◀── (Independent, can parallelize)
└── 1.3: Batch Processing ◀── Depends on 1.1, 1.2

Phase 2: OCR & Data
├── 2.1: OCR Metrics ◀── (Independent)
├── 2.2: Ground Truth ◀── (Independent)
└── 2.3: Datasets ◀── Depends on 2.1, 2.2

Phase 3: RL ◀── CRITICAL PATH
├── 3.1: DocumentEnv ◀── Depends on Phase 1, Phase 2 (all previous work)
└── 3.2: PPO Training ◀── Depends on 3.1

Phase 4: Evaluation
├── 4.1: Evaluator ◀── Depends on Phase 1, 2
├── 4.2: Benchmarks ◀── Depends on 4.1
└── 4.3: Docs ◀── Can happen anytime
```

### Critical Path (Longest Dependency Chain)

```
1.1 Augmentation Presets (2 days)
  ↓
1.3 Batch Processing (2 days)
  ↓
2.1 OCR Metrics (2 days)
  ↓
2.3 Datasets (1 day)
  ↓
3.1 DocumentEnv (3 days) ◀── CRITICAL
  ↓
3.2 PPO Training (2 days) ◀── CRITICAL
  ↓
4.1 Evaluation (2 days)
  ↓
4.2 Benchmarks (2 days)

Total: 16 days (3.2 weeks)
```

### Parallelization Opportunities

**Week 1:** Run these in parallel:
- Developer A: Augmentation Presets (1.1) + Batch Processing (1.3)
- Developer B: Image Handlers (1.2) + OCR Metrics (2.1)

**Week 2:** Run these in parallel:
- Developer A: Ground Truth (2.2) + Datasets (2.3)
- Developer B: Start on DocumentEnv (3.1) using stub implementations

**Week 3:**
- All developers: Focus on RL components (critical path)

**Week 4:**
- Developer A: Evaluation framework
- Developer B: Performance benchmarks
- Developer C: Documentation and examples

---

## 7. Success Criteria

### Component-Level Metrics

#### 7.1 Augmentation Pipeline

**Functional Requirements:**
- ✓ Support 3+ preset configurations (light, medium, heavy)
- ✓ Custom preset creation via parameters
- ✓ Batch processing with multiprocessing
- ✓ Reproducibility with random seeds

**Performance Metrics:**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Single image latency | <100ms | Average over 100 images, 1024x1024 |
| Batch throughput | >10 img/sec | Batch size 32, 4 workers |
| Memory usage | <500MB | Peak memory for single image |
| Preset diversity | SSIM <0.7 | Heavy preset vs original |

**Quality Metrics:**
- Visual inspection: Augmented images look realistic (human evaluation)
- No artifacts or corruption
- Maintains document structure (layout preserved)

#### 7.2 OCR Engine

**Functional Requirements:**
- ✓ Multi-language support (EN, CH at minimum)
- ✓ Bounding box extraction
- ✓ Confidence scores per region
- ✓ Batch processing capability

**Performance Metrics:**
| Metric | Target (CPU) | Target (GPU) |
|--------|-------------|--------------|
| Single page latency | <500ms | <50ms |
| Batch throughput | >5 pages/sec | >50 pages/sec |
| Memory usage | <1GB | <2GB (includes model) |

**Accuracy Metrics:**
| Document Type | Clean CER | Augmented CER |
|---------------|-----------|---------------|
| Printed text | <5% | <15% |
| Receipts | <10% | <20% |
| Forms | <8% | <18% |
| Handwritten | <25% | <35% |

#### 7.3 RL Training

**Functional Requirements:**
- ✓ Custom Gymnasium environment
- ✓ PPO agent implementation
- ✓ Reward function balancing accuracy/realism
- ✓ Checkpoint saving and loading
- ✓ TensorBoard logging

**Training Metrics:**
| Metric | Target | Measurement |
|--------|--------|-------------|
| Convergence time | <6 hours | 1M timesteps, 4 envs, GPU |
| Final reward | >0.7 | Average over last 100 episodes |
| Stability | StdDev <0.1 | Reward std in last 1000 steps |

**Validation Metrics:**
- **Baseline OCR accuracy**: 75% (no augmentation)
- **Random augmentation**: 60% (random parameters)
- **RL-optimized augmentation**: >80% (learned policy)
- **Improvement**: ≥20% over random augmentation

#### 7.4 Dataset Management

**Functional Requirements:**
- ✓ Support ICDAR, SROIE, custom formats
- ✓ Train/val/test split utilities
- ✓ Ground truth validation
- ✓ Lazy loading for large datasets

**Quality Metrics:**
- Ground truth parsing accuracy: 100% (no corrupted data)
- Dataset iteration speed: >100 samples/sec
- Memory efficient: Load only necessary data

### System-Level Metrics

#### End-to-End Pipeline Performance

```python
# Example benchmark scenario
dataset: 1000 document images
augmentation: heavy preset
ocr: PaddleOCR (GPU)
evaluation: CER + WER + confidence

Target metrics:
- Total processing time: <5 minutes (GPU), <20 minutes (CPU)
- Mean CER: <15%
- Mean confidence: >0.75
- Throughput: >3 images/sec (GPU)
```

#### Code Quality Metrics

| Metric | Target |
|--------|--------|
| Test coverage | >80% |
| Linting (ruff) | 0 errors |
| Type coverage (mypy) | >70% |
| Documentation | All public APIs documented |
| Cyclomatic complexity | <10 per function |

#### Usability Metrics

- **CLI usability**: Users can augment/OCR images with <5 commands
- **API simplicity**: Core workflows achievable in <10 lines of code
- **Error messages**: Clear, actionable error messages (no stack traces for user errors)
- **Documentation**: Tutorial completes in <30 minutes

### Acceptance Tests

```python
# Acceptance test 1: Basic augmentation workflow
def test_acceptance_augmentation():
    """User can augment an image with 3 lines of code."""
    from document_simulator.augmentation import DocumentAugmenter
    
    augmenter = DocumentAugmenter(preset="light")
    result = augmenter.augment("input.jpg")
    result.save("output.jpg")
    
    assert Path("output.jpg").exists()

# Acceptance test 2: OCR workflow
def test_acceptance_ocr():
    """User can extract text with 3 lines of code."""
    from document_simulator.ocr import OCREngine
    
    ocr = OCREngine()
    result = ocr.recognize("document.jpg")
    
    assert len(result["text"]) > 0

# Acceptance test 3: RL training workflow
def test_acceptance_rl_training():
    """User can train an RL agent with 5 lines of code."""
    from document_simulator.rl import RLTrainer, RLConfig
    
    config = RLConfig(train_data_dir="./data/train")
    trainer = RLTrainer(config)
    model = trainer.train(total_timesteps=10000)
    
    assert model is not None
```

---

## 8. Timeline & Effort Estimation

### Phase Breakdown with Time Estimates

#### Phase 1: Foundation & Core Augmentation (Week 1)

| Task | Effort | Dependencies | Owner |
|------|--------|--------------|-------|
| 1.1: Augmentation Presets | 2 days | None | Dev A |
| 1.2: Image Handlers | 1 day | None | Dev B |
| 1.3: Batch Processing | 2 days | 1.1, 1.2 | Dev A |
| **Total** | **5 days** | | |

**Deliverables:**
- ✓ 3 working augmentation presets (light, medium, heavy)
- ✓ Image I/O utilities supporting multiple formats
- ✓ Batch processing with 4x speedup on multi-core systems
- ✓ 30+ unit tests with >85% coverage

**Risks:**
- Augraphy parameter tuning may take longer than expected
- **Mitigation**: Start with basic presets, refine based on OCR results in Phase 2

#### Phase 2: OCR Integration & Metrics (Week 2)

| Task | Effort | Dependencies | Owner |
|------|--------|--------------|-------|
| 2.1: OCR Metrics | 2 days | None | Dev B |
| 2.2: Ground Truth Management | 1 day | None | Dev A |
| 2.3: Dataset Loaders | 2 days | 2.1, 2.2 | Dev A |
| **Total** | **5 days** | | |

**Deliverables:**
- ✓ CER, WER, Levenshtein distance metrics
- ✓ Ground truth parsers for JSON, XML formats
- ✓ Dataset loaders for ICDAR, custom formats
- ✓ Integration tests with real PaddleOCR
- ✓ 40+ tests with >80% coverage

**Risks:**
- PaddleOCR model download failures
- **Mitigation**: Cache models, provide manual download instructions

#### Phase 3: RL Environment & Training (Week 3) — CRITICAL

| Task | Effort | Dependencies | Owner |
|------|--------|--------------|-------|
| 3.1: DocumentEnv Implementation | 3 days | Phase 1, 2 | All devs |
| 3.2: PPO Training Pipeline | 2 days | 3.1 | Dev A, B |
| **Total** | **5 days** | | |

**Deliverables:**
- ✓ Fully functional Gymnasium environment
- ✓ Reward function with tunable weights
- ✓ PPO training loop with checkpointing
- ✓ TensorBoard integration
- ✓ At least 1 trained model showing improvement
- ✓ 25+ tests (mostly integration tests)

**Risks:**
- **HIGH RISK**: Reward function design may require iteration
- **HIGH RISK**: Training may not converge initially
- **Mitigation**: Start with simple reward (CER only), add complexity gradually
- **Mitigation**: Use hyperparameter search (Optuna) if initial training fails

#### Phase 4: Evaluation & Benchmarking (Week 4)

| Task | Effort | Dependencies | Owner |
|------|--------|--------------|-------|
| 4.1: Evaluation Framework | 2 days | Phase 1, 2, 3 | Dev A |
| 4.2: Performance Benchmarks | 2 days | 4.1 | Dev B |
| 4.3: Documentation & Examples | 1 day | All | Dev C |
| **Total** | **5 days** | | |

**Deliverables:**
- ✓ Evaluation script for test sets
- ✓ Performance benchmarks (speed, memory)
- ✓ Comparison report: baseline vs RL-optimized
- ✓ Complete API documentation
- ✓ 3+ Jupyter notebook tutorials
- ✓ README with quick start guide

**Risks:**
- Documentation may be rushed if earlier phases delayed
- **Mitigation**: Write docs incrementally throughout development

### Timeline Visualization

```
Week 1: Foundation
Mon  Tue  Wed  Thu  Fri
├────┼────┼────┼────┼────┤
│ 1.1 Augmentation Presets │  Dev A
├────────────┼─────────────┤
│  1.2 Image │ 1.3 Batch   │  Dev B
│  Handlers  │ Processing  │
└────────────┴─────────────┘

Week 2: OCR & Data
Mon  Tue  Wed  Thu  Fri
├────┼────┼────┼────┼────┤
│  2.1 OCR Metrics    │    Dev B
├─────────────────────┼────┤
│ 2.2 GT │  2.3 Datasets  │  Dev A
│  Mgmt  │                │
└────────┴────────────────┘

Week 3: RL (CRITICAL PATH)
Mon  Tue  Wed  Thu  Fri
├────┼────┼────┼────┼────┤
│  3.1 DocumentEnv      │  Both devs
│  (pair programming)  │
├───────────────┼────────┤
│ 3.2 Training  │ Test  │  Dev A
│   Pipeline    │ &Fix  │  Dev B
└───────────────┴────────┘

Week 4: Evaluation & Polish
Mon  Tue  Wed  Thu  Fri
├────┼────┼────┼────┼────┤
│ 4.1 Eval  │ 4.2 Bench │  Dev A
│ Framework │  marks    │  Dev B
├───────────┴───────────┤
│  4.3 Documentation    │  Dev C
│  (all hands on deck)  │
└───────────────────────┘
```

### Effort Summary

| Phase | Developer Days | Calendar Days | Critical Path? |
|-------|---------------|---------------|----------------|
| Phase 1 | 5 | 3-4 | No |
| Phase 2 | 5 | 3-4 | No |
| Phase 3 | 5 | 4-5 | **YES** |
| Phase 4 | 5 | 3-4 | No |
| **Total** | **20 dev-days** | **~4 weeks** | |

**With 2 developers**: Can be completed in **3-4 weeks** with parallelization.

**With 1 developer**: Requires **4-5 weeks** (no parallelization).

### Milestones

| Milestone | Date | Criteria |
|-----------|------|----------|
| M1: Foundation Complete | End of Week 1 | All Phase 1 tests passing, CLI augment works |
| M2: OCR Integration | End of Week 2 | All Phase 2 tests passing, CLI ocr works |
| M3: RL Training Works | Mid Week 3 | Environment runs without errors |
| M4: First Trained Model | End of Week 3 | Model shows >baseline performance |
| M5: Production Ready | End of Week 4 | All tests pass, docs complete, benchmarks meet targets |

---

### Critical Files for Implementation

Based on this comprehensive plan, here are the 5 most critical files for implementing the document_simulator project:

- **/Users/amuhamadafendi/Git_VSCode/document_simulator/src/document_simulator/rl/environment.py** - Core RL environment implementation; defines state/action spaces, reward function, and integration of augmentation+OCR; this is the heart of the RL optimization system

- **/Users/amuhamadafendi/Git_VSCode/document_simulator/src/document_simulator/augmentation/presets.py** - Augmentation preset factory and configurations; defines the parameter spaces that RL will optimize; critical for both manual usage and RL training

- **/Users/amuhamadafendi/Git_VSCode/document_simulator/src/document_simulator/ocr/metrics.py** - OCR quality metrics (CER, WER, confidence); used extensively in reward calculation and evaluation; must be accurate and efficient

- **/Users/amuhamadafendi/Git_VSCode/document_simulator/src/document_simulator/data/datasets.py** - Dataset loading and ground truth management; provides training data for RL and evaluation; must support multiple formats (ICDAR, SROIE, custom)

- **/Users/amuhamadafendi/Git_VSCode/document_simulator/tests/integration/test_rl_training.py** - Integration tests for the complete RL training pipeline; validates end-to-end workflow; early detection of integration issues
