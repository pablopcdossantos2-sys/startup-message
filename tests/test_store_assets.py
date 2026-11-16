"""Garante que arte automática não possa ser considerada pronta para a Store."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ASSETS_SCRIPT = Path(__file__).resolve().parents[1] / "packaging" / "make_assets.py"


def load_asset_builder():
    spec = importlib.util.spec_from_file_location("make_assets_for_test", ASSETS_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_rejects_missing_store_assets(tmp_path, monkeypatch):
    module = load_asset_builder()
    monkeypatch.setattr(module, "ASSETS", tmp_path / "assets")
    monkeypatch.setattr(module, "MSIX_ASSETS", tmp_path / "Assets")
    monkeypatch.setattr(module, "PLACEHOLDER_MARKER", tmp_path / "assets" / "PLACEHOLDER_ASSETS.txt")
    with pytest.raises(ValueError, match="ausentes"):
        module.check_store_assets()


def test_generated_artwork_is_explicitly_blocked_from_store(tmp_path, monkeypatch):
    module = load_asset_builder()
    monkeypatch.setattr(module, "ASSETS", tmp_path / "assets")
    monkeypatch.setattr(module, "MSIX_ASSETS", tmp_path / "Assets")
    monkeypatch.setattr(module, "PLACEHOLDER_MARKER", tmp_path / "assets" / "PLACEHOLDER_ASSETS.txt")
    monkeypatch.setattr(sys, "argv", ["make_assets.py"])
    module.main()
    assert module.PLACEHOLDER_MARKER.exists()
    with pytest.raises(ValueError, match="provisórios"):
        module.check_store_assets()
    # Apagar apenas o marcador não pode legitimar o desenho provisório.
    module.PLACEHOLDER_MARKER.unlink()
    with pytest.raises(ValueError, match="placeholder"):
        module.check_store_assets()
