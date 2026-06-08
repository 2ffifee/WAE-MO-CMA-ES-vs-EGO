"""COCO BBOB-BIOBJ benchmark adapter."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Iterable

import numpy as np

from wae_project.experiments.config import BenchmarkConfig


COCO_INSTALL_HINT = (
    "COCO Python modules are required. Install project dependencies with "
    "`python -m pip install -e .` or install COCO directly with "
    "`python -m pip install coco-experiment cocopp`."
)


@dataclass(frozen=True)
class CocoProblemSpec:
    suite: str
    function_id: int
    instance: int
    dimension: int
    budget: int


@dataclass
class CocoBiobjProblem:
    """Small wrapper around a single COCO bi-objective problem."""

    spec: CocoProblemSpec
    problem: object

    @property
    def id(self) -> str:
        return str(getattr(self.problem, "id", self.spec))

    @property
    def name(self) -> str:
        return str(getattr(self.problem, "name", self.id))

    @property
    def dimension(self) -> int:
        return self.spec.dimension

    @property
    def number_of_objectives(self) -> int:
        value = getattr(self.problem, "number_of_objectives", 2)
        return int(value)

    @property
    def lower_bounds(self) -> np.ndarray:
        return np.asarray(getattr(self.problem, "lower_bounds"), dtype=float)

    @property
    def upper_bounds(self) -> np.ndarray:
        return np.asarray(getattr(self.problem, "upper_bounds"), dtype=float)

    def evaluate(self, x: np.ndarray) -> np.ndarray:
        """Evaluate a candidate point and return a two-objective vector."""

        candidate = np.asarray(x, dtype=float)
        if candidate.shape != (self.dimension,):
            raise ValueError(
                f"Expected candidate shape {(self.dimension,)}, got {candidate.shape}."
            )
        values = np.asarray(self.problem(candidate), dtype=float)
        if values.shape != (self.number_of_objectives,):
            raise ValueError(
                "COCO problem returned unexpected objective shape "
                f"{values.shape}, expected {(self.number_of_objectives,)}."
            )
        return values

    def observe_with(self, observer: object) -> None:
        """Attach a COCO observer so evaluations are logged for cocopp."""

        observe = getattr(self.problem, "observe_with", None)
        if not callable(observe):
            raise RuntimeError("COCO problem backend does not support observe_with().")
        observe(observer)

    def free(self) -> None:
        """Release the underlying COCO problem if the backend exposes this method."""

        free = getattr(self.problem, "free", None)
        if callable(free):
            free()


def iter_coco_biobj_problems(
    benchmark: BenchmarkConfig,
    budget_multiplier: int,
) -> Iterable[CocoBiobjProblem]:
    """Yield selected BBOB-BIOBJ problems from COCO."""

    if benchmark.suite != "bbob-biobj":
        raise ValueError(f"Unsupported COCO suite: {benchmark.suite!r}.")

    cocoex = _import_cocoex()
    suite = cocoex.Suite(benchmark.suite, "", _suite_filter_options(benchmark))

    for dimension in benchmark.dimensions:
        for function_id in benchmark.function_ids:
            for instance in benchmark.instances:
                problem = suite.get_problem_by_function_dimension_instance(
                    function_id,
                    dimension,
                    instance,
                )
                yield CocoBiobjProblem(
                    spec=CocoProblemSpec(
                        suite=benchmark.suite,
                        function_id=function_id,
                        instance=instance,
                        dimension=dimension,
                        budget=budget_multiplier * dimension,
                    ),
                    problem=problem,
                )


def load_single_coco_biobj_problem(
    benchmark: BenchmarkConfig,
    function_id: int,
    dimension: int,
    instance: int,
    budget_multiplier: int,
) -> CocoBiobjProblem:
    """Load one selected BBOB-BIOBJ problem from COCO."""

    if benchmark.suite != "bbob-biobj":
        raise ValueError(f"Unsupported COCO suite: {benchmark.suite!r}.")

    cocoex = _import_cocoex()
    suite = cocoex.Suite(benchmark.suite, "", _suite_filter_options(benchmark))
    problem = suite.get_problem_by_function_dimension_instance(function_id, dimension, instance)
    return CocoBiobjProblem(
        spec=CocoProblemSpec(
            suite=benchmark.suite,
            function_id=function_id,
            instance=instance,
            dimension=dimension,
            budget=budget_multiplier * dimension,
        ),
        problem=problem,
    )


def _suite_filter_options(benchmark: BenchmarkConfig) -> str:
    function_ids = ",".join(str(value) for value in benchmark.function_ids)
    dimensions = ",".join(str(value) for value in benchmark.dimensions)
    instances = ",".join(str(value) for value in benchmark.instances)
    return (
        f"dimensions: {dimensions} "
        f"function_indices: {function_ids} "
        f"instance_indices: {instances}"
    )


def _import_cocoex():
    try:
        import cocoex
    except ImportError as exc:
        raise RuntimeError(COCO_INSTALL_HINT) from exc
    return cocoex
