"""Tests for statistical comparison helpers."""

import numpy as np
import pandas as pd

from wae_project.analysis.statistics import (
    compare_algorithms_on_metric,
    holm_correction,
    wilson_confidence_interval,
)


def _synthetic_finals() -> pd.DataFrame:
    rows = []
    for problem in range(3):
        for algorithm, offset in (("mo-cma-es", 0.0), ("parego", 0.5)):
            rows.append(
                {
                    "suite": "bbob-biobj",
                    "function_id": problem + 1,
                    "instance": 1,
                    "dimension": 2,
                    "run_id": "run-01",
                    "seed": 1,
                    "algorithm": algorithm,
                    "final_hypervolume": 10.0 + problem + offset,
                }
            )
    return pd.DataFrame(rows)


def test_holm_correction_monotone():
    raw = np.array([0.01, 0.04, 0.2])
    adjusted = holm_correction(raw)
    assert adjusted[0] <= adjusted[1] <= adjusted[2]
    assert all(adjusted >= raw)


def test_wilson_interval_in_unit_interval():
    low, high = wilson_confidence_interval(7, 10)
    assert 0.0 <= low <= high <= 1.0


def test_compare_algorithms_produces_pairwise_table():
    _, friedman, summary = compare_algorithms_on_metric(_synthetic_finals())
    assert friedman is None  # Friedman wymaga >= 3 algorytmow (mamy 2)
    assert len(summary) == 1
    assert "wilcoxon_pvalue" in summary.columns
