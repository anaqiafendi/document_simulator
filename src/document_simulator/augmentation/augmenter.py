"""Document image augmentation using Augraphy."""

from pathlib import Path
from typing import Optional, Union

import numpy as np
from augraphy import AugraphyPipeline
from loguru import logger
from PIL import Image

from document_simulator.config import settings


class DocumentAugmenter:
    """Document image augmenter using Augraphy pipeline."""

    def __init__(
        self,
        pipeline: str = "default",
        custom_augmentations: Optional[list] = None,
    ):
        """Initialize the document augmenter.

        Args:
            pipeline: Augmentation pipeline preset ('default', 'light', 'heavy').
                Ignored when *custom_augmentations* is provided.
            custom_augmentations: Optional list of pre-configured Augraphy augmentation
                objects.  When supplied, the preset is bypassed and these objects are
                split into ink / paper / post phases using the CATALOGUE metadata.
                Pass an empty list to create a no-op pipeline.
        """
        self.pipeline = pipeline
        if custom_augmentations is not None:
            self._augraphy_pipeline = self._create_custom_pipeline(custom_augmentations)
            logger.info(
                f"Initialized DocumentAugmenter with {len(custom_augmentations)} "
                "custom augmentation(s)"
            )
        else:
            self._augraphy_pipeline = self._create_pipeline(pipeline)
            logger.info(f"Initialized DocumentAugmenter with '{pipeline}' pipeline")

    def _create_custom_pipeline(self, augmentations: list) -> AugraphyPipeline:
        """Create an AugraphyPipeline from a list of augmentation objects.

        Each object's class name is looked up in ``CATALOGUE`` to determine
        its phase (ink / paper / post).  Objects not found in CATALOGUE are
        placed in ``post_phase`` by default.

        Args:
            augmentations: List of Augraphy augmentation instances.

        Returns:
            Configured AugraphyPipeline.
        """
        from document_simulator.augmentation.catalogue import CATALOGUE

        ink_phase: list = []
        paper_phase: list = []
        post_phase: list = []

        for aug in augmentations:
            class_name = type(aug).__name__
            phase = CATALOGUE.get(class_name, {}).get("phase", "post")
            if phase == "ink":
                ink_phase.append(aug)
            elif phase == "paper":
                paper_phase.append(aug)
            else:
                post_phase.append(aug)

        return AugraphyPipeline(
            ink_phase=ink_phase,
            paper_phase=paper_phase,
            post_phase=post_phase,
        )

    def _create_pipeline(self, preset: str) -> AugraphyPipeline:
        """Create Augraphy pipeline based on preset.

        Args:
            preset: Pipeline preset name ('light', 'medium', 'heavy', 'default')

        Returns:
            Configured AugraphyPipeline
        """
        from document_simulator.augmentation.presets import PresetFactory

        config = PresetFactory.create(preset)
        return AugraphyPipeline(
            ink_phase=config.ink_phase,
            paper_phase=config.paper_phase,
            post_phase=config.post_phase,
        )

    def augment(
        self, image: Union[np.ndarray, Image.Image]
    ) -> Union[np.ndarray, Image.Image]:
        """Augment a single image.

        Args:
            image: Input image (numpy array or PIL Image)

        Returns:
            Augmented image in the same format as input
        """
        input_is_pil = isinstance(image, Image.Image)

        # Convert to numpy array if needed
        if input_is_pil:
            image_array = np.array(image)
        else:
            image_array = image

        # Apply augmentation
        augmented = self._augraphy_pipeline(image_array)

        # Convert back to PIL if needed
        if input_is_pil:
            return Image.fromarray(augmented)
        else:
            return augmented

    def augment_file(self, input_path: Path, output_path: Path) -> None:
        """Augment an image from file and save to output.

        Args:
            input_path: Path to input image
            output_path: Path to save augmented image
        """
        logger.info(f"Augmenting {input_path}")

        # Load image
        image = Image.open(input_path)

        # Augment
        augmented = self.augment(image)

        # Save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        augmented.save(output_path)

        logger.success(f"Saved augmented image to {output_path}")
