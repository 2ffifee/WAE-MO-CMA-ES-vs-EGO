"""MO-CMA-ES optimizer integration based on pycomocma."""

from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Protocol

import numpy as np

from wae_project.experiments.config import MoCmaEsConfig


COMOCMA_INSTALL_HINT = (
    "MO-CMA-ES requires pycomocma. Install project dependencies with "
    "`python -m pip install -e .` or install it directly with "
    "`python -m pip install comocma cma`."
)


class BiObjectiveProblem(Protocol):
    dimension: int
    lower_bounds: np.ndarray
    upper_bounds: np.ndarray

    def evaluate(self, x: np.ndarray) -> np.ndarray:
        """Return the objective vector for a candidate point."""


@dataclass(frozen=True)
class EvaluationRecord:
    evaluation: int
    x: tuple[float, ...]
    objectives: tuple[float, float]


@dataclass(frozen=True)
class OptimizationResult:
    algorithm: str
    evaluations: int
    records: tuple[EvaluationRecord, ...]


def run_mo_cma_es(
    problem: BiObjectiveProblem,
    config: MoCmaEsConfig,
    budget: int,
    seed: int,
) -> OptimizationResult:
    """Run COMO-CMA-ES on one bi-objective problem with a fixed evaluation budget."""

    if config.name != "mo-cma-es":
        raise ValueError(f"Unsupported algorithm config: {config.name!r}.")
    if budget <= 0:
        raise ValueError("Evaluation budget must be positive.")

    comocma = _import_comocma()
    _seed_global_generators(seed)

    x0 = _initial_kernel_centers(problem, config.num_kernels, seed)
    cma_options = {
        "bounds": [problem.lower_bounds.tolist(), problem.upper_bounds.tolist()],
        "seed": seed,
        "verbose": -9,
    }
    solvers = comocma.get_cmas(x0.tolist(), config.sigma0, inopts=cma_options)
    optimizer = comocma.Sofomore(
        solvers,
        list(config.reference_point),
        opts={"archive": True, "restart": None, "update_order": None},
    )

    records: list[EvaluationRecord] = []

    while len(records) < budget and not optimizer.stop():
        ask_argument = "all" if config.ask_mode == "all" else None
        solutions = optimizer.ask(ask_argument) if ask_argument else optimizer.ask()
        if not solutions:
            break
        if len(records) + len(solutions) > budget:
            break

        objective_values: list[list[float]] = []
        for solution in solutions:
            clipped = np.clip(
                np.asarray(solution, dtype=float),
                problem.lower_bounds,
                problem.upper_bounds,
            )
            values = problem.evaluate(clipped)
            objective_pair = (float(values[0]), float(values[1]))
            objective_values.append([objective_pair[0], objective_pair[1]])
            records.append(
                EvaluationRecord(
                    evaluation=len(records) + 1,
                    x=tuple(float(value) for value in clipped),
                    objectives=objective_pair,
                )
            )

        optimizer.tell(solutions, objective_values)

    return OptimizationResult(
        algorithm=config.name,
        evaluations=len(records),
        records=tuple(records),
    )


def _initial_kernel_centers(
    problem: BiObjectiveProblem,
    num_kernels: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    lower = np.asarray(problem.lower_bounds, dtype=float)
    upper = np.asarray(problem.upper_bounds, dtype=float)
    return rng.uniform(lower, upper, size=(num_kernels, problem.dimension))


def _seed_global_generators(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def _import_comocma():
    try:
        import comocma
    except ImportError as exc:
        raise RuntimeError(COMOCMA_INSTALL_HINT) from exc
    return comocma
