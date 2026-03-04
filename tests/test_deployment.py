"""Validate deployment configuration files for Hugging Face Spaces."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_dockerfile_exists():
    assert (REPO_ROOT / "Dockerfile").exists(), "Dockerfile missing from repo root"


def test_dockerfile_exposes_7860():
    content = (REPO_ROOT / "Dockerfile").read_text()
    assert "EXPOSE 7860" in content, "Dockerfile must EXPOSE 7860 for HF Spaces"


def test_dockerfile_cmd_uses_port_7860():
    content = (REPO_ROOT / "Dockerfile").read_text()
    assert "7860" in content.split("CMD")[1], "CMD must use port 7860 for HF Spaces"


def test_dockerfile_uses_uv_sync_frozen():
    content = (REPO_ROOT / "Dockerfile").read_text()
    assert "uv sync --frozen" in content, "Must use --frozen to respect uv.lock exactly"


def test_dockerfile_excludes_dev_deps():
    content = (REPO_ROOT / "Dockerfile").read_text()
    assert "--no-dev" in content, "Production image must not install dev dependencies"


def test_streamlit_config_exists():
    assert (REPO_ROOT / ".streamlit" / "config.toml").exists(), (
        ".streamlit/config.toml missing — required for HF Spaces"
    )


def test_streamlit_config_disables_cors():
    content = (REPO_ROOT / ".streamlit" / "config.toml").read_text()
    assert "enableCORS = false" in content, (
        "enableCORS must be false for HF Spaces iframe embedding"
    )


def test_streamlit_config_disables_xsrf():
    content = (REPO_ROOT / ".streamlit" / "config.toml").read_text()
    assert "enableXsrfProtection = false" in content, (
        "enableXsrfProtection must be false for HF Spaces"
    )


def test_dockerignore_excludes_venv():
    content = (REPO_ROOT / ".dockerignore").read_text()
    assert ".venv/" in content, ".dockerignore must exclude .venv/"


def test_dockerignore_excludes_secrets():
    content = (REPO_ROOT / ".dockerignore").read_text()
    assert "secrets.toml" in content, ".dockerignore must exclude .streamlit/secrets.toml"
