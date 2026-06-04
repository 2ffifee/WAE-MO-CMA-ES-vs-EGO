"""Run configured optimization experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

from wae_project.experiments.config import load_experiment_config
from wae_project.experiments.runner import RunOverrides, run_experiment


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
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip runs already present in the output CSV.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print task count without running optimizers.",
    )
    parser.add_argument(
        "--function-from",
        type=int,
        default=None,
        help="Override benchmark: first function id (inclusive).",
    )
    parser.add_argument(
        "--function-to",
        type=int,
        default=None,
        help="Override benchmark: last function id (inclusive).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_experiment_config(args.config)
    output_path = args.output or config.output_dir / f"{config.name}.csv"
    resume = args.resume or config.resume

    overrides = None
    if args.function_from is not None or args.function_to is not None:
        function_from = args.function_from or min(config.benchmark.function_ids)
        function_to = args.function_to or max(config.benchmark.function_ids)
        overrides = RunOverrides(function_ids=tuple(range(function_from, function_to + 1)))

    return run_experiment(
        config,
        output_path,
        resume=resume,
        overrides=overrides,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
