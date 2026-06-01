"""Check whether the COCO BBOB-BIOBJ backend is available."""

from __future__ import annotations

from pathlib import Path
import sys

from wae_project.benchmarks.coco_biobj import load_single_coco_biobj_problem
from wae_project.experiments.config import load_experiment_config


def main() -> int:
    config = load_experiment_config(Path("configs") / "smoke.yaml")
    function_id = config.benchmark.function_ids[0]
    dimension = config.benchmark.dimensions[0]
    instance = config.benchmark.instances[0]

    try:
        problem = load_single_coco_biobj_problem(
            benchmark=config.benchmark,
            function_id=function_id,
            dimension=dimension,
            instance=instance,
            budget_multiplier=config.budget.evaluations_multiplier,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    midpoint = (problem.lower_bounds + problem.upper_bounds) / 2.0
    values = problem.evaluate(midpoint)

    print("COCO backend OK")
    print(f"problem_id={problem.id}")
    print(f"dimension={problem.dimension}")
    print(f"objectives={problem.number_of_objectives}")
    print(f"midpoint_values={values.tolist()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
