"""End-to-end tests for the CLI entry point."""

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image


def _run_cli(*args):
    """Run the document-simulator CLI via uv run python -m."""
    cmd = [sys.executable, "-m", "document_simulator"] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True)


@pytest.fixture
def small_image(tmp_path):
    p = tmp_path / "input.png"
    Image.new("RGB", (64, 64), color="white").save(p)
    return p


# ---------------------------------------------------------------------------
# --help / --version
# ---------------------------------------------------------------------------

def test_cli_help():
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "document" in result.stdout.lower()


def test_cli_version():
    result = _run_cli("--version")
    assert result.returncode == 0


def test_cli_no_command_shows_help():
    result = _run_cli()
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# augment command
# ---------------------------------------------------------------------------

def test_cli_augment_command(small_image, tmp_path):
    output = tmp_path / "output.png"
    result = _run_cli("augment", str(small_image), str(output))
    assert result.returncode == 0, result.stderr
    assert output.exists()


def test_cli_augment_light_preset(small_image, tmp_path):
    output = tmp_path / "output_light.png"
    result = _run_cli("augment", str(small_image), str(output), "--pipeline", "light")
    assert result.returncode == 0, result.stderr
    assert output.exists()


def test_cli_augment_nonexistent_input(tmp_path):
    result = _run_cli("augment", "/nonexistent/image.jpg", str(tmp_path / "out.jpg"))
    assert result.returncode != 0
