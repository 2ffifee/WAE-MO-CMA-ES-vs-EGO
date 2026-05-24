"""Experiment configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv

import yaml


@dataclass(frozen=True)
class BenchmarkConfig:
    suite: str
    dimensions: tuple[int, ...]
    function_ids: tuple[int, ...]
    instances: tuple[int, ...]
    lower_bound: float
    upper_bound: float


@dataclass(frozen=True)
class BudgetConfig:
    evaluations_multiplier: int


@dataclass(frozen=True)
class AlgorithmConfig:
    name: str
    num_kernels: int
    sigma0: float
    reference_point: tuple[float, float]
    ask_mode: str


@dataclass(frozen=True)
class SeedEntry:
    run_id: str
    seed: int


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    output_dir: Path
    algorithm: AlgorithmConfig
    benchmark: BenchmarkConfig
    budget: BudgetConfig
    seeds: tuple[SeedEntry, ...]


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    """Load and validate an experiment configuration file."""

    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)

    if not isinstance(raw, dict):
        raise ValueError(f"Configuration file {config_path} must contain a mapping.")

    experiment = _required_mapping(raw, "experiment")
    algorithm = _required_mapping(raw, "algorithm")
    benchmark = _required_mapping(raw, "benchmark")
    budget = _required_mapping(raw, "budget")
    seed_config = _required_mapping(raw, "seeds")

    benchmark_config = BenchmarkConfig(
        suite=_required_str(benchmark, "suite"),
        dimensions=_required_int_tuple(benchmark, "dimensions"),
        function_ids=_required_int_tuple(benchmark, "function_ids"),
        instances=_required_int_tuple(benchmark, "instances"),
        lower_bound=float(_required_number(benchmark, "lower_bound")),
        upper_bound=float(_required_number(benchmark, "upper_bound")),
    )
    _validate_benchmark(benchmark_config)

    budget_config = BudgetConfig(
        evaluations_multiplier=_required_positive_int(budget, "evaluations_multiplier")
    )
    algorithm_config = AlgorithmConfig(
        name=_required_str(algorithm, "name"),
        num_kernels=_required_positive_int(algorithm, "num_kernels"),
        sigma0=float(_required_number(algorithm, "sigma0")),
        reference_point=_required_float_pair(algorithm, "reference_point"),
        ask_mode=_required_str(algorithm, "ask_mode"),
    )
    _validate_algorithm(algorithm_config)

    seeds = _load_seeds(
        config_path.parent / _required_str(seed_config, "file"),
        requested_run_ids=tuple(seed_config.get("run_ids", ())),
    )
    if not seeds:
        raise ValueError("At least one seed entry must be selected.")

    return ExperimentConfig(
        name=_required_str(experiment, "name"),
        output_dir=Path(_required_str(experiment, "output_dir")),
        algorithm=algorithm_config,
        benchmark=benchmark_config,
        budget=budget_config,
        seeds=seeds,
    )


def _load_seeds(path: Path, requested_run_ids: tuple[str, ...]) -> tuple[SeedEntry, ...]:
    requested = set(requested_run_ids)
    entries: list[SeedEntry] = []

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        expected_fields = {"run_id", "seed"}
        if set(reader.fieldnames or ()) != expected_fields:
            raise ValueError(f"Seed file {path} must contain columns: run_id, seed.")

        for row in reader:
            run_id = row["run_id"].strip()
            if requested and run_id not in requested:
                continue
            entries.append(SeedEntry(run_id=run_id, seed=int(row["seed"])))

    return tuple(entries)


def _validate_benchmark(config: BenchmarkConfig) -> None:
    if config.lower_bound >= config.upper_bound:
        raise ValueError("Benchmark lower_bound must be smaller than upper_bound.")


def _validate_algorithm(config: AlgorithmConfig) -> None:
    if config.name != "mo-cma-es":
        raise ValueError(f"Unsupported algorithm in this workflow: {config.name!r}.")
    if config.sigma0 <= 0.0:
        raise ValueError("Algorithm sigma0 must be positive.")
    if config.ask_mode not in {"sequential", "all"}:
        raise ValueError("Algorithm ask_mode must be either 'sequential' or 'all'.")


def _required_mapping(raw: dict, key: str) -> dict:
    value = raw.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing or invalid '{key}' section.")
    return value


def _required_str(raw: dict, key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing or invalid string value '{key}'.")
    return value


def _required_number(raw: dict, key: str) -> int | float:
    value = raw.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"Missing or invalid numeric value '{key}'.")
    return value


def _required_positive_int(raw: dict, key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"Missing or invalid positive integer value '{key}'.")
    return value


def _required_int_tuple(raw: dict, key: str) -> tuple[int, ...]:
    value = raw.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"Missing or invalid non-empty integer list '{key}'.")
    if not all(isinstance(item, int) and item > 0 for item in value):
        raise ValueError(f"All values in '{key}' must be positive integers.")
    return tuple(value)


def _required_float_pair(raw: dict, key: str) -> tuple[float, float]:
    value = raw.get(key)
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"Missing or invalid two-value numeric list '{key}'.")
    if not all(isinstance(item, (int, float)) for item in value):
        raise ValueError(f"All values in '{key}' must be numeric.")
    return (float(value[0]), float(value[1]))
