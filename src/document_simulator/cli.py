"""Command-line interface for Document Simulator."""

import argparse
import sys
from pathlib import Path

from loguru import logger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Document Simulator - Document image augmentation and OCR training"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Augmentation command
    augment_parser = subparsers.add_parser("augment", help="Augment document images")
    augment_parser.add_argument("input", type=Path, help="Input image path")
    augment_parser.add_argument("output", type=Path, help="Output image path")
    augment_parser.add_argument(
        "--pipeline",
        type=str,
        default="default",
        help="Augmentation pipeline preset",
    )

    # OCR command
    ocr_parser = subparsers.add_parser("ocr", help="Run OCR on document images")
    ocr_parser.add_argument("input", type=Path, help="Input image path")
    ocr_parser.add_argument(
        "--output",
        type=Path,
        help="Output text file path",
    )
    ocr_parser.add_argument(
        "--use-gpu",
        action="store_true",
        help="Use GPU for OCR",
    )

    # Train command
    train_parser = subparsers.add_parser("train", help="Train RL pipeline optimizer")
    train_parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Training data directory",
    )
    train_parser.add_argument(
        "--num-steps",
        type=int,
        default=100000,
        help="Number of training steps",
    )
    train_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./models"),
        help="Model output directory",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Execute commands
    try:
        if args.command == "augment":
            from document_simulator.augmentation import DocumentAugmenter

            logger.info(f"Augmenting image: {args.input}")
            augmenter = DocumentAugmenter(pipeline=args.pipeline)
            augmenter.augment_file(args.input, args.output)
            logger.success(f"Augmented image saved to: {args.output}")

        elif args.command == "ocr":
            from document_simulator.ocr import OCREngine

            logger.info(f"Running OCR on: {args.input}")
            ocr = OCREngine(use_gpu=args.use_gpu)
            result = ocr.recognize_file(args.input)

            if args.output:
                args.output.write_text(result["text"])
                logger.success(f"OCR result saved to: {args.output}")
            else:
                print(result["text"])

        elif args.command == "train":
            from document_simulator.rl import PipelineOptimizer

            logger.info(f"Training RL pipeline optimizer")
            optimizer = PipelineOptimizer(data_dir=args.data_dir)
            optimizer.train(num_steps=args.num_steps, output_dir=args.output_dir)
            logger.success(f"Model saved to: {args.output_dir}")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
