"""Document dataset loaders."""

import random
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

try:
    from torch.utils.data import Dataset
except ImportError:
    # torch is an optional dep (in [project.optional-dependencies] rl).
    # Provide a minimal shim so the module is importable without torch.
    class Dataset:  # type: ignore[no-redef]
        def __len__(self):
            raise NotImplementedError
        def __getitem__(self, idx):
            raise NotImplementedError

from document_simulator.data.ground_truth import GroundTruth, GroundTruthLoader
from document_simulator.utils.image_io import ImageHandler


class DocumentDataset(Dataset):
    """PyTorch-compatible dataset of document image / ground-truth pairs.

    The dataset expects a directory layout where each image file has a
    corresponding annotation file with the same stem but a ``.json`` or
    ``.xml`` extension::

        data_dir/
            invoice_001.jpg
            invoice_001.json
            form_002.png
            form_002.xml
            ...

    Args:
        data_dir: Root directory that contains image and annotation files.
        image_extensions: File extensions to treat as images.
        transform: Optional callable applied to each PIL Image.
    """

    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".pdf"}

    def __init__(
        self,
        data_dir: Path,
        image_extensions: Optional[List[str]] = None,
        transform=None,
    ):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self._extensions = set(image_extensions or self.IMAGE_EXTENSIONS)
        self._samples: List[Tuple[Path, Path]] = self._discover_samples()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _discover_samples(self) -> List[Tuple[Path, Path]]:
        """Return (image_path, annotation_path) pairs found in data_dir."""
        pairs: List[Tuple[Path, Path]] = []
        for img_path in sorted(self.data_dir.iterdir()):
            if img_path.suffix.lower() not in self._extensions:
                continue
            # Look for a matching annotation file
            gt_path = self._find_annotation(img_path)
            if gt_path is not None:
                pairs.append((img_path, gt_path))
        return pairs

    def _find_annotation(self, img_path: Path) -> Optional[Path]:
        """Return a JSON or XML annotation file for *img_path*, or None."""
        for ext in (".json", ".xml"):
            candidate = img_path.with_suffix(ext)
            if candidate.exists():
                return candidate
        return None

    # ------------------------------------------------------------------
    # Dataset protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, idx: int) -> Tuple[Image.Image, GroundTruth]:
        img_path, gt_path = self._samples[idx]
        if img_path.suffix.lower() == ".pdf":
            try:
                import fitz
            except ImportError:
                raise ImportError(
                    "PyMuPDF required for PDF datasets. "
                    "Install with: uv sync --extra synthesis"
                )
            doc = fitz.open(str(img_path))
            mat = fitz.Matrix(150 / 72, 150 / 72)  # 150 DPI
            pix = doc[0].get_pixmap(matrix=mat)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        else:
            image = ImageHandler.load(img_path)
        gt = GroundTruthLoader.detect_and_load(gt_path)

        if self.transform is not None:
            image = self.transform(image)

        return image, gt

    # ------------------------------------------------------------------
    # Split utilities
    # ------------------------------------------------------------------

    def split(
        self,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        seed: int = 42,
    ) -> Tuple["DocumentDataset", "DocumentDataset", "DocumentDataset"]:
        """Split the dataset into train / validation / test subsets.

        Args:
            val_ratio: Fraction for validation (0 < val_ratio < 1).
            test_ratio: Fraction for test (0 < test_ratio < 1).
            seed: Random seed for reproducibility.

        Returns:
            Three :class:`DocumentDataset` instances (train, val, test).
        """
        indices = list(range(len(self)))
        rng = random.Random(seed)
        rng.shuffle(indices)

        n = len(indices)
        n_test = max(1, int(n * test_ratio))
        n_val = max(1, int(n * val_ratio))

        test_idx = indices[:n_test]
        val_idx = indices[n_test: n_test + n_val]
        train_idx = indices[n_test + n_val:]

        return (
            _SubsetDataset(self, train_idx),
            _SubsetDataset(self, val_idx),
            _SubsetDataset(self, test_idx),
        )


class _SubsetDataset(DocumentDataset):
    """A view into a DocumentDataset using a list of indices."""

    def __init__(self, parent: DocumentDataset, indices: List[int]):
        # Bypass __init__ scanning
        self.data_dir = parent.data_dir
        self.transform = parent.transform
        self._extensions = parent._extensions
        self._samples = [parent._samples[i] for i in indices]
