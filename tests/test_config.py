"""Testy ładowania konfiguracji YAML."""

from pathlib import Path

import pytest

from wae_project.experiments.config import (
    MoCmaEsConfig,
    ParEgoConfig,
    load_experiment_config,
)


@pytest.mark.parametrize(
    "config_name",
    [
        "smoke.yaml",
        "comparison_smoke.yaml",
        "pilot_comparison.yaml",
        "full_benchmark.yaml",
    ],
)
def test_load_configs(config_name: str):
    root = Path(__file__).resolve().parents[1]
    cfg = load_experiment_config(root / "configs" / config_name)
    assert cfg.name
    assert len(cfg.algorithms) >= 1
    assert cfg.benchmark.dimensions


def test_comparison_has_both_algorithms():
    root = Path(__file__).resolve().parents[1]
    cfg = load_experiment_config(root / "configs" / "comparison_smoke.yaml")
    names = {a.name for a in cfg.algorithms}
    assert "mo-cma-es" in names
    assert "parego" in names
    assert any(isinstance(a, MoCmaEsConfig) for a in cfg.algorithms)
    assert any(isinstance(a, ParEgoConfig) for a in cfg.algorithms)


def test_full_benchmark_has_55_functions():
    root = Path(__file__).resolve().parents[1]
    cfg = load_experiment_config(root / "configs" / "full_benchmark.yaml")
    assert len(cfg.benchmark.function_ids) == 55
    assert cfg.coco_output_dir is not None
    assert len(cfg.seeds) == 30
