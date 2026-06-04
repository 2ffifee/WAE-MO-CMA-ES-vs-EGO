"""Run the full BBOB-BIOBJ benchmark (55 functions) in resumable chunks."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from wae_project.experiments.config import load_experiment_config
from wae_project.experiments.runner import RunOverrides, count_tasks, run_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs") / "full_benchmark.yaml",
        help="Full benchmark YAML (default: 55 functions, D=2,3,5,10).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output CSV (default: <output_dir>/<experiment_name>.csv).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=5,
        help="Number of function ids per chunk (resume-friendly).",
    )
    parser.add_argument(
        "--chunk-index",
        type=int,
        default=None,
        help="Run only this chunk (0-based). Default: all chunks.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip runs already stored in the output CSV.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned chunks and task counts only.",
    )
    return parser.parse_args()


def _chunk_bounds(
    function_ids: tuple[int, ...], chunk_size: int, chunk_index: int | None
) -> list[tuple[int, int]]:
    chunks: list[tuple[int, int]] = []
    ordered = tuple(sorted(function_ids))
    n_chunks = math.ceil(len(ordered) / chunk_size)
    indices = range(n_chunks) if chunk_index is None else [chunk_index]

    for index in indices:
        if index < 0 or index >= n_chunks:
            raise ValueError(f"chunk-index {index} out of range [0, {n_chunks - 1}].")
        start = index * chunk_size
        end = min(start + chunk_size, len(ordered))
        chunks.append((ordered[start], ordered[end - 1]))

    return chunks


def main() -> int:
    args = parse_args()
    config = load_experiment_config(args.config)
    output_path = args.output or config.output_dir / f"{config.name}.csv"
    resume = args.resume or config.resume
    chunks = _chunk_bounds(config.benchmark.function_ids, args.chunk_size, args.chunk_index)

    if args.dry_run:
        print(f"Experiment: {config.name}")
        print(f"Functions: {len(config.benchmark.function_ids)} ids")
        print(f"Chunks ({args.chunk_size} functions each): {len(chunks)}")
        for index, (start, end) in enumerate(chunks):
            overrides = RunOverrides(function_ids=tuple(range(start, end + 1)))
            n_tasks = count_tasks(config, overrides)
            print(f"  chunk {index}: f{start}..f{end} -> {n_tasks} runs")
        print(f"Total runs (all chunks): {count_tasks(config, None)}")
        return 0

    for index, (start, end) in enumerate(chunks):
        print(f"=== Chunk {index + 1}/{len(chunks)}: functions {start}..{end} ===")
        overrides = RunOverrides(function_ids=tuple(range(start, end + 1)))
        code = run_experiment(
            config,
            output_path,
            resume=resume,
            overrides=overrides,
        )
        if code != 0:
            return code

    print(f"Full benchmark complete: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
