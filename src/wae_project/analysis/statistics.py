"""Statistical tests from the project report: Friedman, Wilcoxon, Holm, binomial, Wilson."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass(frozen=True)
class PairwiseComparison:
    algorithm_a: str
    algorithm_b: str
    n_problems: int
    wins_a: int
    wins_b: int
    ties: int
    wilcoxon_statistic: float | None
    wilcoxon_pvalue: float | None
    binomial_pvalue: float | None
    wilson_ci_a: tuple[float, float] | None


@dataclass(frozen=True)
class FriedmanResult:
    statistic: float
    pvalue: float
    n_algorithms: int
    n_blocks: int


def holm_correction(pvalues: np.ndarray) -> np.ndarray:
    """Holm step-down adjusted p-values for a family of tests."""

    pvalues = np.asarray(pvalues, dtype=float)
    n = len(pvalues)
    if n == 0:
        return pvalues

    order = np.argsort(pvalues)
    adjusted = np.empty(n, dtype=float)
    previous = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, pvalues[index] * (n - rank))
        value = max(value, previous)
        adjusted[index] = value
        previous = value
    return adjusted


def friedman_on_metric(
    finals: pd.DataFrame,
    metric_column: str = "final_hypervolume",
) -> FriedmanResult | None:
    """
    Friedman test on per-problem metric values across algorithms.

    Each problem (function, dimension, instance, run) is one block; algorithms are treatments.
    """

    if metric_column not in finals.columns:
        raise ValueError(f"DataFrame must contain column {metric_column!r}.")

    block_cols = ["suite", "function_id", "instance", "dimension", "run_id", "seed"]
    pivot = finals.pivot_table(
        index=block_cols,
        columns="algorithm",
        values=metric_column,
        aggfunc="mean",
    ).dropna(axis=0, how="any")

    if pivot.shape[1] < 3 or pivot.shape[0] < 2:
        return None

    statistic, pvalue = stats.friedmanchisquare(
        *[pivot[algorithm].to_numpy() for algorithm in pivot.columns]
    )
    return FriedmanResult(
        statistic=float(statistic),
        pvalue=float(pvalue),
        n_algorithms=int(pivot.shape[1]),
        n_blocks=int(pivot.shape[0]),
    )


def pairwise_wilcoxon(
    values_a: np.ndarray,
    values_b: np.ndarray,
) -> tuple[float | None, float | None]:
    """Wilcoxon signed-rank test (two-sided) on paired samples."""

    if len(values_a) != len(values_b) or len(values_a) < 1:
        return None, None
    if np.allclose(values_a, values_b):
        return 0.0, 1.0
    try:
        result = stats.wilcoxon(values_a, values_b, alternative="two-sided", zero_method="wilcox")
        return float(result.statistic), float(result.pvalue)
    except ValueError:
        return None, None


def binomial_win_test(wins: int, n: int, p_null: float = 0.5) -> float | None:
    """Two-sided binomial test for win count vs fair coin."""

    if n <= 0:
        return None
    result = stats.binomtest(wins, n=n, p=p_null, alternative="two-sided")
    return float(result.pvalue)


def wilson_confidence_interval(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float] | None:
    """Wilson score interval for a binomial proportion."""

    if n <= 0:
        return None
    z = stats.norm.ppf(1 - alpha / 2)
    phat = successes / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((phat * (1 - phat) + z**2 / (4 * n)) / n) / denom
    return (float(max(0.0, center - margin)), float(min(1.0, center + margin)))


def compare_algorithms_on_metric(
    data: pd.DataFrame,
    metric_column: str = "final_hypervolume",
    higher_is_better: bool = True,
) -> tuple[list[PairwiseComparison], FriedmanResult | None, pd.DataFrame]:
    """
    Pairwise Wilcoxon + binomial win counts per problem, plus Friedman across all algorithms.
    """

    block_cols = ["suite", "function_id", "instance", "dimension", "run_id", "seed"]
    grouped = (
        data.groupby(block_cols + ["algorithm"], as_index=False)[metric_column]
        .mean()
        .rename(columns={metric_column: "value"})
    )

    algorithms = sorted(grouped["algorithm"].unique())
    friedman_input = grouped.rename(columns={"value": metric_column})
    friedman = friedman_on_metric(friedman_input, metric_column=metric_column)

    comparisons: list[PairwiseComparison] = []
    summary_rows = []

    for i, alg_a in enumerate(algorithms):
        for alg_b in algorithms[i + 1 :]:
            merged = grouped[grouped["algorithm"] == alg_a].merge(
                grouped[grouped["algorithm"] == alg_b],
                on=block_cols,
                suffixes=("_a", "_b"),
            )
            if merged.empty:
                continue

            a_vals = merged["value_a"].to_numpy(dtype=float)
            b_vals = merged["value_b"].to_numpy(dtype=float)
            if higher_is_better:
                wins_a = int(np.sum(a_vals > b_vals))
                wins_b = int(np.sum(b_vals > a_vals))
            else:
                wins_a = int(np.sum(a_vals < b_vals))
                wins_b = int(np.sum(b_vals < a_vals))
            ties = int(len(merged) - wins_a - wins_b)

            w_stat, w_p = pairwise_wilcoxon(a_vals, b_vals)
            binom_p = binomial_win_test(wins_a, wins_a + wins_b) if wins_a + wins_b > 0 else None
            ci = wilson_confidence_interval(wins_a, wins_a + wins_b) if wins_a + wins_b > 0 else None

            comparisons.append(
                PairwiseComparison(
                    algorithm_a=alg_a,
                    algorithm_b=alg_b,
                    n_problems=len(merged),
                    wins_a=wins_a,
                    wins_b=wins_b,
                    ties=ties,
                    wilcoxon_statistic=w_stat,
                    wilcoxon_pvalue=w_p,
                    binomial_pvalue=binom_p,
                    wilson_ci_a=ci,
                )
            )
            summary_rows.append(
                {
                    "algorithm_a": alg_a,
                    "algorithm_b": alg_b,
                    "n_problems": len(merged),
                    "wins_a": wins_a,
                    "wins_b": wins_b,
                    "ties": ties,
                    "wilcoxon_statistic": w_stat,
                    "wilcoxon_pvalue": w_p,
                    "binomial_pvalue": binom_p,
                    "wilson_ci_a_low": None if ci is None else ci[0],
                    "wilson_ci_a_high": None if ci is None else ci[1],
                }
            )

    summary = pd.DataFrame(summary_rows)
    if not summary.empty and summary["wilcoxon_pvalue"].notna().any():
        mask = summary["wilcoxon_pvalue"].notna()
        adjusted = np.full(len(summary), np.nan)
        adjusted[mask.to_numpy()] = holm_correction(summary.loc[mask, "wilcoxon_pvalue"].to_numpy())
        summary["wilcoxon_pvalue_holm"] = adjusted

    if friedman is not None:
        summary.attrs["friedman"] = friedman

    return comparisons, friedman, summary
