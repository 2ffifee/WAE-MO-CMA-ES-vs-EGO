"""Core experiment execution loop with resume and optional COCO logging."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from wae_project.algorithms.mo_cma_es import run_mo_cma_es
from wae_project.algorithms.parego import run_parego
from wae_project.benchmarks.coco_biobj import iter_coco_biobj_problems
from wae_project.benchmarks.coco_logging import CocoRunLogger, ensure_exdata_root
from wae_project.experiments.config import (
    AlgorithmConfig,
    BenchmarkConfig,
    ExperimentConfig,
    MoCmaEsConfig,
    ParEgoConfig,
)
from wae_project.experiments.results import (
    RunKey,
    append_results_csv,
    load_completed_run_keys,
    result_rows,
)


@dataclass(frozen=True)
class RunOverrides:
    function_ids: tuple[int, ...] | None = None


def benchmark_with_overrides(
    benchmark: BenchmarkConfig, overrides: RunOverrides | None
) -> BenchmarkConfig:
    if overrides is None or overrides.function_ids is None:
        return benchmark
    return BenchmarkConfig(
        suite=benchmark.suite,
        dimensions=benchmark.dimensions,
        function_ids=overrides.function_ids,
        instances=benchmark.instances,
        lower_bound=benchmark.lower_bound,
        upper_bound=benchmark.upper_bound,
    )


def count_tasks(config: ExperimentConfig, overrides: RunOverrides | None = None) -> int:
    benchmark = benchmark_with_overrides(config.benchmark, overrides)
    n_problems = (
        len(benchmark.function_ids)
        * len(benchmark.dimensions)
        * len(benchmark.instances)
    )
    return len(config.algorithms) * len(config.seeds) * n_problems


def run_experiment(
    config: ExperimentConfig,
    output_path: Path,
    *,
    resume: bool = False,
    overrides: RunOverrides | None = None,
    dry_run: bool = False,
) -> int:
    """Run all configured tasks, optionally resuming from an existing CSV."""

    benchmark = benchmark_with_overrides(config.benchmark, overrides)
    completed = load_completed_run_keys(output_path) if resume else set()
    total = count_tasks(config, overrides)
    done_before = len(completed)
    rows_written = 0

    if dry_run:
        print(
            f"Dry run: {total} tasks "
            f"({len(config.algorithms)} algorithms × {len(config.seeds)} seeds × "
            f"{len(benchmark.function_ids)} functions × {len(benchmark.dimensions)} D × "
            f"{len(benchmark.instances)} instances)"
        )
        if resume:
            print(f"Resume: {done_before} already in {output_path}")
        return 0

    coco_root = None
    if config.coco_output_dir is not None:
        ensure_exdata_root()
        coco_root = config.coco_output_dir

    try:
        for algorithm in config.algorithms:
            for seed_entry in config.seeds:
                for problem in iter_coco_biobj_problems(
                    benchmark,
                    config.budget.evaluations_multiplier,
                ):
                    key = RunKey.from_problem(algorithm.name, seed_entry, problem)
                    if key in completed:
                        print(f"Skip (done): {key}")
                        continue

                    logger = None
                    try:
                        print(
                            "Running "
                            f"{algorithm.name} "
                            f"run_id={seed_entry.run_id} "
                            f"seed={seed_entry.seed} "
                            f"problem={problem.id} "
                            f"budget={problem.spec.budget}"
                        )
                        if coco_root is not None:
                            logger = CocoRunLogger(
                                suite=benchmark.suite,
                                result_root=coco_root,
                                algorithm=algorithm.name,
                            )
                            logger.attach(problem)

                        result = _run_algorithm(
                            algorithm=algorithm,
                            problem=problem,
                            budget=problem.spec.budget,
                            seed=seed_entry.seed,
                        )
                        rows = result_rows(
                            experiment_name=config.name,
                            run_id=seed_entry.run_id,
                            seed=seed_entry.seed,
                            problem=problem,
                            result=result,
                        )
                        append_results_csv(output_path, rows)
                        rows_written += len(rows)
                        completed.add(key)
                    finally:
                        problem.free()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(
        f"Finished: wrote {rows_written} evaluation rows to {output_path} "
        f"({len(completed)}/{total} runs complete)"
    )
    return 0


def _run_algorithm(
    algorithm: AlgorithmConfig,
    problem,
    budget: int,
    seed: int,
):
    if isinstance(algorithm, MoCmaEsConfig):
        return run_mo_cma_es(problem=problem, config=algorithm, budget=budget, seed=seed)
    if isinstance(algorithm, ParEgoConfig):
        return run_parego(problem=problem, config=algorithm, budget=budget, seed=seed)
    raise ValueError(f"Unsupported algorithm config type: {type(algorithm).__name__}.")
