"""Gymnasium environment for document augmentation RL optimization."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import gymnasium as gym
import numpy as np

from document_simulator.augmentation.augmenter import DocumentAugmenter
from document_simulator.data.datasets import DocumentDataset
from document_simulator.ocr.metrics import aggregate_confidence, calculate_cer


# Number of continuous action dimensions (augmentation hyper-parameters)
ACTION_DIM = 12

# Observation image size fed to the CNN policy
OBS_HEIGHT = 224
OBS_WIDTH = 224


class DocumentEnv(gym.Env):
    """RL environment that learns optimal augmentation parameters.

    **Observation space**: ``Box(0, 255, shape=(224, 224, 3), dtype=float32)``
    — the current document image resized to 224×224.

    **Action space**: ``Box(0, 1, shape=(12,), dtype=float32)``
    — 12 continuous parameters that are mapped to Augraphy augmentation
    probabilities and intensities:

    ============  =================================
    Index         Parameter
    ============  =================================
    0             ``InkBleed`` probability
    1             ``InkBleed`` intensity (max)
    2             ``Fading`` probability
    3             ``Fading`` value (max)
    4             ``Markup`` probability
    5             ``NoiseTexturize`` probability
    6             ``NoiseTexturize`` sigma (max, ×20)
    7             ``ColorShift`` probability
    8             ``Brightness`` probability
    9             ``Brightness`` range spread
    10            ``Gamma`` probability
    11            ``Jpeg`` probability
    ============  =================================

    **Reward**: Composite score balancing OCR accuracy and visible degradation::

        reward = 0.5 × CAR + 0.3 × mean_confidence + 0.2 × (1 − SSIM)

    where CAR = 1 − CER.

    Args:
        dataset_path: Directory containing paired image/annotation files.
            When ``None`` the environment uses synthetic blank images for
            testing without a real dataset.
        target_degradation: Hint for future reward shaping (unused currently).
        ocr_engine: An :class:`~document_simulator.ocr.OCREngine` instance.
            When ``None`` the OCR step is *skipped* and a reward of 0 is
            returned — useful for fast unit tests.
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        dataset_path: Optional[Path] = None,
        target_degradation: str = "medium",
        ocr_engine=None,
    ):
        super().__init__()

        self.action_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(ACTION_DIM,), dtype=np.float32
        )
        self.observation_space = gym.spaces.Box(
            low=0,
            high=255,
            shape=(OBS_HEIGHT, OBS_WIDTH, 3),
            dtype=np.uint8,
        )

        self.target_degradation = target_degradation
        self._ocr = ocr_engine
        self._dataset: Optional[DocumentDataset] = None
        self._dataset_path = dataset_path

        if dataset_path is not None:
            self._dataset = DocumentDataset(Path(dataset_path))

        self._current_image: Optional[np.ndarray] = None
        self._current_gt_text: str = ""

    # ------------------------------------------------------------------
    # Gym interface
    # ------------------------------------------------------------------

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Load a random document and return the initial observation.

        Args:
            seed: Optional random seed for reproducibility.
            options: Unused; present for API compatibility.

        Returns:
            Tuple of (observation, info_dict).
        """
        super().reset(seed=seed)

        if self._dataset and len(self._dataset) > 0:
            idx = self.np_random.integers(0, len(self._dataset))
            pil_image, gt = self._dataset[idx]
            self._current_image = np.array(pil_image)
            self._current_gt_text = gt.text
        else:
            # Synthetic blank image for testing without data
            self._current_image = np.full(
                (256, 256, 3), fill_value=255, dtype=np.uint8
            )
            self._current_gt_text = ""

        obs = self._image_to_obs(self._current_image)
        return obs, {}

    def step(
        self, action: np.ndarray
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Apply augmentation from *action*, run OCR, and return reward.

        Args:
            action: Array of shape ``(12,)`` with values in ``[0, 1]``.

        Returns:
            ``(next_obs, reward, terminated, truncated, info)``
        """
        params = self._action_to_params(action)
        augmenter = self._build_augmenter(params)
        aug_image = augmenter.augment(self._current_image)

        if isinstance(aug_image, np.ndarray):
            aug_arr = aug_image
        else:
            aug_arr = np.array(aug_image)

        reward, info = self._calculate_reward(aug_arr, params)
        next_obs = self._image_to_obs(aug_arr)

        # Each episode is a single augmentation step
        return next_obs, reward, True, False, info

    def render(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _action_to_params(self, action: np.ndarray) -> Dict[str, Any]:
        """Map continuous action vector to Augraphy parameter dict."""
        a = action.tolist()
        return {
            "ink_bleed_p": float(a[0]),
            "ink_bleed_intensity_max": float(a[1]),
            "fading_p": float(a[2]),
            "fading_value_max": float(a[3]),
            "markup_p": float(a[4]),
            "noise_p": float(a[5]),
            "noise_sigma_max": float(a[6]) * 20.0,  # scale [0,1] → [0, 20]
            "color_shift_p": float(a[7]),
            "brightness_p": float(a[8]),
            "brightness_spread": float(a[9]) * 0.4,  # scale [0,1] → [0, 0.4]
            "gamma_p": float(a[10]),
            "jpeg_p": float(a[11]),
        }

    def _build_augmenter(self, params: Dict[str, Any]) -> DocumentAugmenter:
        """Construct a DocumentAugmenter from an action parameter dict.

        We inject the parameters by temporarily patching the preset before
        creating the Augraphy pipeline.
        """
        from augraphy import AugraphyPipeline
        from augraphy.augmentations import (
            Brightness,
            ColorShift,
            Gamma,
            InkBleed,
            Jpeg,
            LowLightNoise,
            Markup,
            NoiseTexturize,
        )

        p = params
        spread = p["brightness_spread"]
        ink_phase = [
            InkBleed(
                p=p["ink_bleed_p"],
                intensity_range=(0.0, max(0.01, p["ink_bleed_intensity_max"])),
            ),
            LowLightNoise(p=p["fading_p"]),
            Markup(p=p["markup_p"]),
        ]
        paper_phase = [
            NoiseTexturize(
                p=p["noise_p"],
                sigma_range=(1, max(2, int(p["noise_sigma_max"]))),
            ),
            ColorShift(p=p["color_shift_p"]),
        ]
        post_phase = [
            Brightness(
                p=p["brightness_p"],
                brightness_range=(max(0.5, 1.0 - spread), min(1.5, 1.0 + spread)),
            ),
            Gamma(p=p["gamma_p"]),
            Jpeg(p=p["jpeg_p"]),
        ]

        pipeline = AugraphyPipeline(
            ink_phase=ink_phase,
            paper_phase=paper_phase,
            post_phase=post_phase,
        )

        # Wrap in a thin object that exposes augment()
        augmenter = DocumentAugmenter.__new__(DocumentAugmenter)
        augmenter.pipeline = "custom"
        augmenter._augraphy_pipeline = pipeline
        return augmenter

    def _calculate_reward(
        self, aug_arr: np.ndarray, params: Dict[str, Any]
    ) -> Tuple[float, Dict[str, Any]]:
        """Compute composite reward from OCR quality and visual change.

        Returns:
            Tuple of (reward_float, info_dict).
        """
        info: Dict[str, Any] = {"params": params}

        if self._ocr is None:
            # No OCR engine — return neutral reward for testing
            return 0.0, info

        ocr_result = self._ocr.recognize(aug_arr)
        cer = calculate_cer(ocr_result["text"], self._current_gt_text)
        car = 1.0 - min(cer, 1.0)
        confidence = aggregate_confidence(ocr_result["scores"])

        ssim_score = self._compute_ssim(self._current_image, aug_arr)

        reward = (
            0.5 * car
            + 0.3 * confidence
            + 0.2 * (1.0 - ssim_score)
        )

        info.update({
            "cer": cer,
            "car": car,
            "confidence": confidence,
            "ssim": ssim_score,
        })
        return float(reward), info

    @staticmethod
    def _compute_ssim(orig: np.ndarray, aug: np.ndarray) -> float:
        """Structural similarity between two uint8 images."""
        try:
            from skimage.metrics import structural_similarity as ssim

            # Resize aug to match orig if needed
            if orig.shape != aug.shape:
                aug = cv2.resize(aug, (orig.shape[1], orig.shape[0]))
            score = ssim(orig, aug, channel_axis=2)
            return float(np.clip(score, 0.0, 1.0))
        except Exception:
            return 0.5  # fallback if skimage unavailable

    @staticmethod
    def _image_to_obs(image: np.ndarray) -> np.ndarray:
        """Resize image to 224×224 and return as uint8."""
        resized = cv2.resize(image, (OBS_WIDTH, OBS_HEIGHT))
        return resized.astype(np.uint8)
