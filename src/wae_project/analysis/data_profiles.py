"""Data profiles — frakcja rozwiązanych problemów vs budżet ewaluacji."""

from __future__ import annotations

import numpy as np
import pandas as pd

from wae_project.analysis.metrics import cumulative_hypervolume_trace, reference_point


PROBLEM_KEY = ["suite", "function_id", "instance", "dimension", "run_id", "seed"]


def final_hypervolume_per_run(data: pd.DataFrame) -> pd.DataFrame:
    """Hypervolume końcowy dla każdej (algorithm, problem, run)."""
    rows = []
    for keys, group in data.groupby(["algorithm", *PROBLEM_KEY]):
        algorithm = keys[0]
        problem_keys = keys[1:]
        objectives = group.sort_values("evaluation")[["objective_1", "objective_2"]].to_numpy(
            dtype=float
        )
        ref = reference_point(objectives)
        _, hv_trace = cumulative_hypervolume_trace(objectives, ref)
        rows.append(
            {
                "algorithm": algorithm,
                **dict(zip(PROBLEM_KEY, problem_keys)),
                "evaluations": int(group["evaluation"].max()),
                "budget": int(group["budget"].iloc[0]),
                "final_hypervolume": float(hv_trace[-1]) if len(hv_trace) else 0.0,
                "reference_objective_1": ref[0],
                "reference_objective_2": ref[1],
            }
        )
    return pd.DataFrame(rows)


def data_profile(
    data: pd.DataFrame,
    budget_grid: np.ndarray,
    success_fraction: float = 0.9,
) -> pd.DataFrame:
    """
    Dla każdego budżetu B: jaki % problemów osiągnął >= success_fraction * najlepszego HV
    w danym algorytmie (proxy data profile z konspektu).
    """
    finals = final_hypervolume_per_run(data)
    best_per_problem = (
        finals.groupby(["suite", "function_id", "instance", "dimension"])["final_hypervolume"]
        .max()
        .reset_index(name="best_hv")
    )
    merged = finals.merge(
        best_per_problem,
        on=["suite", "function_id", "instance", "dimension"],
    )
    merged["success"] = merged["final_hypervolume"] >= success_fraction * merged["best_hv"]

    profiles = []
    for algorithm in sorted(merged["algorithm"].unique()):
        alg_data = merged[merged["algorithm"] == algorithm]
        n_problems = len(
            alg_data.drop_duplicates(["suite", "function_id", "instance", "dimension"])
        )
        for budget_limit in budget_grid:
            subset = alg_data[alg_data["evaluations"] <= budget_limit]
            if subset.empty:
                solved_frac = 0.0
            else:
                solved = (
                    subset.groupby(["suite", "function_id", "instance", "dimension"])["success"]
                    .any()
                    .sum()
                )
                solved_frac = solved / max(n_problems, 1)
            profiles.append(
                {
                    "algorithm": algorithm,
                    "budget_limit": int(budget_limit),
                    "solved_fraction": float(solved_frac),
                    "n_problems": n_problems,
                }
            )
    return pd.DataFrame(profiles)


def ert_to_hypervolume_threshold(
    data: pd.DataFrame, hv_fraction: float = 0.95
) -> pd.DataFrame:
    """
    Uproszczony ERT: liczba ewaluacji do osiągnięcia hv_fraction * końcowego HV
    (proxy ERT z konspektu względem hypervolume).
    """
    rows = []
    for (algorithm, *rest), group in data.groupby(["algorithm", *PROBLEM_KEY]):
        objectives = group.sort_values("evaluation")[["objective_1", "objective_2"]].to_numpy(
            dtype=float
        )
        ref = reference_point(objectives)
        evals, hv_trace = cumulative_hypervolume_trace(objectives, ref)
        target = hv_fraction * hv_trace[-1] if len(hv_trace) else 0.0
        ert = int(evals[-1]) if len(evals) else 0
        for i, hv in enumerate(hv_trace):
            if hv >= target:
                ert = int(evals[i])
                break
        rows.append(
            {
                "algorithm": algorithm,
                **dict(zip(PROBLEM_KEY, rest)),
                "ert_evaluations": ert,
                "target_hypervolume": target,
                "final_hypervolume": float(hv_trace[-1]) if len(hv_trace) else 0.0,
            }
        )
    return pd.DataFrame(rows)
