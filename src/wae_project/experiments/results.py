"""Utilities for writing experiment results."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from wae_project.algorithms.mo_cma_es import OptimizationResult
from wae_project.benchmarks.coco_biobj import CocoBiobjProblem
from wae_project.experiments.config import SeedEntry


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


@dataclass(frozen=True)
class RunKey:
    algorithm: str
    run_id: str
    seed: int
    function_id: int
    dimension: int
    instance: int

    @classmethod
    def from_problem(
        cls, algorithm: str, seed_entry: SeedEntry, problem: CocoBiobjProblem
    ) -> RunKey:
        return cls(
            algorithm=algorithm,
            run_id=seed_entry.run_id,
            seed=seed_entry.seed,
            function_id=problem.spec.function_id,
            dimension=problem.spec.dimension,
            instance=problem.spec.instance,
        )

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> RunKey:
        return cls(
            algorithm=str(row["algorithm"]),
            run_id=str(row["run_id"]),
            seed=int(row["seed"]),
            function_id=int(row["function_id"]),
            dimension=int(row["dimension"]),
            instance=int(row["instance"]),
        )


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


def load_completed_run_keys(path: str | Path) -> set[RunKey]:
    """Return run keys that already have at least one row in the CSV."""

    csv_path = Path(path)
    if not csv_path.is_file():
        return set()

    completed: set[RunKey] = set()
    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return set()
        for row in reader:
            completed.add(RunKey.from_row(row))
    return completed


def write_results_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    """Write experiment rows to a CSV file (overwrite)."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def append_results_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    """Append rows to a CSV, creating the file and header when needed."""

    if not rows:
        return

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not output_path.is_file() or output_path.stat().st_size == 0

    with output_path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
