"""Deploy the app to a Hugging Face Space via the Hub HTTP API.

Uses upload_folder() instead of git push to avoid the git pack-objects hang
that occurs with large git histories.

Usage:
    # Authenticate once (stores token in ~/.cache/huggingface/)
    hf auth login

    # Deploy current working directory to your Space
    uv run python scripts/deploy_to_hf_spaces.py --repo-id <username>/<space-name>

    # Dry run — print what would be uploaded without uploading
    uv run python scripts/deploy_to_hf_spaces.py --repo-id <username>/<space-name> --dry-run
"""

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Files and patterns to exclude from the upload (mirrors .dockerignore + secrets)
IGNORE_PATTERNS = [
    "**/.git/**",
    "**/.venv/**",
    "**/__pycache__/**",
    "**/*.py[cod]",
    "**/augraphy_cache/**",
    "**/cache/**",
    "**/models/**",
    "**/output/**",
    "**/logs/**",
    "**/checkpoints/**",
    "**/wandb/**",
    "**/.pytest_cache/**",
    "**/htmlcov/**",
    "**/coverage.xml",
    "**/.coverage",
    "**/tests/output/**",
    "**/.streamlit/secrets.toml",
    "**/.env",
    "**/.env.local",
    "**/*.log",
    "logs-*.txt",
    "**/.DS_Store",
    "**/Thumbs.db",
    "**/*.pth",
    "**/*.pt",
    "**/*.ckpt",
    "**/*.pdparams",
    "**/*.pdopt",
    "**/*.pdmodel",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy to Hugging Face Spaces")
    parser.add_argument(
        "--repo-id",
        required=True,
        help="HF repo ID in the form <username>/<space-name>",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("HF_TOKEN"),
        help="HF write token (or set HF_TOKEN env var). Defaults to cached login.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be uploaded without uploading",
    )
    args = parser.parse_args()

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("huggingface_hub not installed. Run: uv add huggingface_hub", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print(f"[dry-run] Would upload {REPO_ROOT} → spaces/{args.repo_id}")
        print(f"[dry-run] Ignoring patterns:\n  " + "\n  ".join(IGNORE_PATTERNS))
        return

    print(f"Uploading {REPO_ROOT} → huggingface.co/spaces/{args.repo_id} ...")
    api = HfApi(token=args.token or None)

    api.upload_folder(
        folder_path=str(REPO_ROOT),
        repo_id=args.repo_id,
        repo_type="space",
        ignore_patterns=IGNORE_PATTERNS,
        commit_message="deploy: update Space from local branch",
    )

    print(f"Done. View your Space at: https://huggingface.co/spaces/{args.repo_id}")


if __name__ == "__main__":
    main()
