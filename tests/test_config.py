"""Config load smoke test."""

from pathlib import Path

from src.config import load_config


def test_default_config():
    cfg = load_config()
    assert cfg.model.embed_dim >= 64
    assert cfg.model.twist_rate > 0


def test_yaml_config():
    path = Path(__file__).resolve().parent.parent / "configs" / "default.yaml"
    cfg = load_config(path)
    assert cfg.model.embed_dim == 384
