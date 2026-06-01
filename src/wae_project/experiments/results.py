"""Utilities for writing experiment results."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from wae_project.algorithms.mo_cma_es import OptimizationResult
from wae_project.benchmarks.coco_biobj import CocoBiobjProblem


RESULT_COLUMNS = [
    "experiment",
    "algorithm",
    "run_id",
    "seed",
    "suite",
    "function_id",
    "instance",
    "dimension",
    "budget",
    "problem_id",
    "evaluation",
    "x",
    "objective_1",
    "objective_2",
]


def result_rows(
    experiment_name: str,
    run_id: str,
    seed: int,
    problem: CocoBiobjProblem,
    result: OptimizationResult,
) -> list[dict[str, Any]]:
    """Convert one optimizer result to flat CSV rows."""

    rows: list[dict[str, Any]] = []
    for record in result.records:
        rows.append(
            {
                "experiment": experiment_name,
                "algorithm": result.algorithm,
                "run_id": run_id,
                "seed": seed,
                "suite": problem.spec.suite,
                "function_id": problem.spec.function_id,
                "instance": problem.spec.instance,
                "dimension": problem.spec.dimension,
                "budget": problem.spec.budget,
                "problem_id": problem.id,
                "evaluation": record.evaluation,
                "x": json.dumps(record.x),
                "objective_1": record.objectives[0],
                "objective_2": record.objectives[1],
            }
        )
    return rows


def write_results_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    """Write experiment rows to a CSV file."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
