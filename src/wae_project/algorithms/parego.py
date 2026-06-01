"""ParEGO optimizer integration based on BoTorch."""

from __future__ import annotations

from dataclasses import dataclass
import random

import numpy as np

from wae_project.algorithms.mo_cma_es import BiObjectiveProblem, EvaluationRecord, OptimizationResult
from wae_project.experiments.config import ParEgoConfig


BOTORCH_INSTALL_HINT = (
    "ParEGO requires BoTorch. Install project dependencies with "
    "`python -m pip install -e .` or install it directly with "
    "`python -m pip install torch botorch gpytorch`."
)


@dataclass(frozen=True)
class _BotorchModules:
    torch: object
    SobolEngine: object
    SingleTaskGP: object
    ExactMarginalLogLikelihood: object
    fit_gpytorch_mll: object
    expected_improvement: object
    optimize_acqf: object


def run_parego(
    problem: BiObjectiveProblem,
    config: ParEgoConfig,
    budget: int,
    seed: int,
) -> OptimizationResult:
    """Run ParEGO on one bi-objective problem with a fixed evaluation budget."""

    if config.name != "parego":
        raise ValueError(f"Unsupported algorithm config: {config.name!r}.")
    if budget <= 0:
        raise ValueError("Evaluation budget must be positive.")

    modules = _import_botorch()
    _seed_global_generators(seed, modules.torch)

    initial_points = min(config.initial_points, budget)
    train_x = _sobol_points(modules, problem.dimension, initial_points, seed)
    records = _evaluate_points(problem, train_x, start_evaluation=1)
    train_y = _records_to_objectives(modules, records)

    while len(records) < budget:
        candidate = _next_candidate(modules, config, train_x, train_y, seed + len(records))
        new_records = _evaluate_points(problem, candidate, start_evaluation=len(records) + 1)
        records.extend(new_records)
        train_x = modules.torch.cat([train_x, candidate], dim=0)
        train_y = _records_to_objectives(modules, records)

    return OptimizationResult(
        algorithm=config.name,
        evaluations=len(records),
        records=tuple(records),
    )


def _next_candidate(
    modules: _BotorchModules,
    config: ParEgoConfig,
    train_x,
    train_y,
    seed: int,
):
    best_candidate = None
    best_value = None

    for offset in range(config.scalarization_samples):
        generator = modules.torch.Generator(device=train_x.device)
        generator.manual_seed(seed + offset)
        weights = modules.torch.rand(train_y.shape[-1], generator=generator, dtype=train_x.dtype)
        weights = weights / weights.sum()

        scalar_y = _scalarized_training_values(modules, train_y, weights)
        model = modules.SingleTaskGP(train_x, scalar_y)
        mll = modules.ExactMarginalLogLikelihood(model.likelihood, model)
        modules.fit_gpytorch_mll(mll)

        acquisition = modules.expected_improvement(model=model, best_f=scalar_y.max())
        candidate, acquisition_value = modules.optimize_acqf(
            acq_function=acquisition,
            bounds=_unit_bounds(modules, train_x.shape[-1], train_x.dtype),
            q=1,
            num_restarts=config.candidate_restarts,
            raw_samples=config.raw_samples,
            options={"batch_limit": 5, "maxiter": 100},
        )

        value = float(acquisition_value.detach().cpu().item())
        if best_value is None or value > best_value:
            best_value = value
            best_candidate = candidate.detach()

    if best_candidate is None:
        raise RuntimeError("ParEGO did not produce a candidate point.")
    return best_candidate


def _scalarized_training_values(modules: _BotorchModules, objectives, weights):
    normalized = _normalize_objectives(modules, objectives)
    weighted = normalized * weights
    cost = weighted.max(dim=-1).values + 0.05 * weighted.sum(dim=-1)
    return -cost.unsqueeze(-1)


def _normalize_objectives(modules: _BotorchModules, objectives):
    lower = objectives.min(dim=0).values
    upper = objectives.max(dim=0).values
    scale = modules.torch.clamp(upper - lower, min=1e-12)
    return (objectives - lower) / scale


def _evaluate_points(
    problem: BiObjectiveProblem,
    unit_points,
    start_evaluation: int,
) -> list[EvaluationRecord]:
    records: list[EvaluationRecord] = []
    points = unit_points.detach().cpu().numpy()

    for offset, unit_point in enumerate(points):
        x = _from_unit_cube(problem, unit_point)
        values = problem.evaluate(x)
        records.append(
            EvaluationRecord(
                evaluation=start_evaluation + offset,
                x=tuple(float(value) for value in x),
                objectives=(float(values[0]), float(values[1])),
            )
        )
    return records


def _records_to_objectives(modules: _BotorchModules, records: list[EvaluationRecord]):
    values = [[record.objectives[0], record.objectives[1]] for record in records]
    return modules.torch.tensor(values, dtype=modules.torch.double)


def _sobol_points(modules: _BotorchModules, dimension: int, count: int, seed: int):
    engine = modules.SobolEngine(dimension=dimension, scramble=True, seed=seed)
    return engine.draw(count).to(dtype=modules.torch.double)


def _from_unit_cube(problem: BiObjectiveProblem, unit_point: np.ndarray) -> np.ndarray:
    lower = np.asarray(problem.lower_bounds, dtype=float)
    upper = np.asarray(problem.upper_bounds, dtype=float)
    return lower + np.asarray(unit_point, dtype=float) * (upper - lower)


def _unit_bounds(modules: _BotorchModules, dimension: int, dtype):
    return modules.torch.stack(
        [
            modules.torch.zeros(dimension, dtype=dtype),
            modules.torch.ones(dimension, dtype=dtype),
        ]
    )


def _seed_global_generators(seed: int, torch) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _import_botorch() -> _BotorchModules:
    try:
        import torch
        try:
            from botorch.acquisition import LogExpectedImprovement as ExpectedImprovementClass
        except ImportError:
            from botorch.acquisition import ExpectedImprovement as ExpectedImprovementClass
        from botorch.fit import fit_gpytorch_mll
        from botorch.models import SingleTaskGP
        from botorch.optim import optimize_acqf
        from gpytorch.mlls import ExactMarginalLogLikelihood
        from torch.quasirandom import SobolEngine
    except ImportError as exc:
        raise RuntimeError(BOTORCH_INSTALL_HINT) from exc

    return _BotorchModules(
        torch=torch,
        SobolEngine=SobolEngine,
        SingleTaskGP=SingleTaskGP,
        ExactMarginalLogLikelihood=ExactMarginalLogLikelihood,
        fit_gpytorch_mll=fit_gpytorch_mll,
        expected_improvement=ExpectedImprovementClass,
        optimize_acqf=optimize_acqf,
    )
