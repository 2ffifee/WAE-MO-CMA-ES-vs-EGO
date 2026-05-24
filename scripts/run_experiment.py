"""Run a configured MO-CMA-ES experiment."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from wae_project.algorithms.mo_cma_es import run_mo_cma_es
from wae_project.benchmarks.coco_biobj import iter_coco_biobj_problems
from wae_project.experiments.config import load_experiment_config
from wae_project.experiments.results import result_rows, write_results_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs") / "smoke.yaml",
        help="Path to the YAML experiment configuration.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output CSV path. Defaults to <output_dir>/<experiment_name>.csv.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_experiment_config(args.config)
    output_path = args.output or config.output_dir / f"{config.name}.csv"

    rows = []
    try:
        for seed_entry in config.seeds:
            for problem in iter_coco_biobj_problems(
                config.benchmark,
                config.budget.evaluations_multiplier,
            ):
                try:
                    print(
                        "Running "
                        f"{config.algorithm.name} "
                        f"run_id={seed_entry.run_id} "
                        f"seed={seed_entry.seed} "
                        f"problem={problem.id} "
                        f"budget={problem.spec.budget}"
                    )
                    result = run_mo_cma_es(
                        problem=problem,
                        config=config.algorithm,
                        budget=problem.spec.budget,
                        seed=seed_entry.seed,
                    )
                    rows.extend(
                        result_rows(
                            experiment_name=config.name,
                            run_id=seed_entry.run_id,
                            seed=seed_entry.seed,
                            problem=problem,
                            result=result,
                        )
                    )
                finally:
                    problem.free()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    write_results_csv(output_path, rows)
    print(f"Wrote {len(rows)} evaluations to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
