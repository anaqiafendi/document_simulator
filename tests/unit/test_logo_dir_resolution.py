"""Tests for where scraped brand logos are read from.

The logos are not in git, so the pool must live outside the checkout: a git
worktree is disposable, and keeping 28MB under one means re-scraping 749 images
every time a branch is created.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from document_simulator import config
from document_simulator.config import DEFAULT_LOGO_CACHE, resolve_logo_dir


@pytest.fixture
def _no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(config.settings, "receiptfaker_logo_dir", None)


def test_default_cache_is_outside_any_repo(_no_override: None) -> None:
    """The whole point: worktrees come and go, the pool must not."""
    resolved = str(resolve_logo_dir())
    assert ".worktrees" not in resolved
    assert "/document_simulator/src/" not in resolved
    assert resolved.startswith(str(Path.home())) or "XDG" in resolved


def test_explicit_setting_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """RECEIPTFAKER_LOGO_DIR overrides everything, even a populated repo dir."""
    repo_local = tmp_path / "repo"
    repo_local.mkdir()
    (repo_local / "a.png").write_bytes(b"x")
    override = tmp_path / "elsewhere"
    monkeypatch.setattr(config.settings, "receiptfaker_logo_dir", override)

    assert resolve_logo_dir(repo_local) == override


def test_populated_repo_dir_is_preferred_over_the_cache(
    _no_override: None, tmp_path: Path
) -> None:
    """An existing checkout that already has the images keeps working."""
    repo_local = tmp_path / "repo"
    repo_local.mkdir()
    (repo_local / "a.png").write_bytes(b"x")

    assert resolve_logo_dir(repo_local) == repo_local


def test_empty_repo_dir_falls_through_to_the_cache(_no_override: None, tmp_path: Path) -> None:
    """An empty data/receiptfaker/logos/ must not shadow a populated cache."""
    empty = tmp_path / "repo"
    empty.mkdir()

    assert resolve_logo_dir(empty) == DEFAULT_LOGO_CACHE


def test_missing_repo_dir_falls_through_to_the_cache(_no_override: None, tmp_path: Path) -> None:
    assert resolve_logo_dir(tmp_path / "does-not-exist") == DEFAULT_LOGO_CACHE


def test_resolution_never_returns_none(_no_override: None) -> None:
    """Callers need a stable path to write into even when nothing exists yet."""
    assert isinstance(resolve_logo_dir(None), Path)


def test_xdg_cache_home_is_honoured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Reimport-free check that the default is derived from XDG, not hardcoded."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert config._user_cache_root() == tmp_path / "document_simulator"
