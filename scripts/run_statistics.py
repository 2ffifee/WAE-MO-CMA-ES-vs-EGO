"""Run Friedman / Wilcoxon / binomial tests on processed experiment metrics."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from wae_project.analysis.data_profiles import ert_to_hypervolume_threshold, final_hypervolume_per_run
from wae_project.analysis.statistics import compare_algorithms_on_metric


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Raw experiment CSV or directory of CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results") / "processed",
    )
    parser.add_argument(
        "--metric",
        choices=("hypervolume", "ert"),
        default="hypervolume",
        help="Metric used for pairwise comparison.",
    )
    return parser.parse_args()


def _load_inputs(path: Path) -> pd.DataFrame:
    if path.is_dir():
        frames = [pd.read_csv(csv) for csv in sorted(path.glob("*.csv"))]
        if not frames:
            raise ValueError(f"No CSV files in {path}")
        return pd.concat(frames, ignore_index=True)
    return pd.read_csv(path)


def main() -> int:
    args = parse_args()
    data = _load_inputs(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem if args.input.is_file() else "combined"

    if args.metric == "hypervolume":
        metric_df = final_hypervolume_per_run(data)
        metric_column = "final_hypervolume"
        higher_is_better = True
    else:
        metric_df = ert_to_hypervolume_threshold(data)
        metric_column = "ert_evaluations"
        higher_is_better = False

    _, friedman, summary = compare_algorithms_on_metric(
        metric_df,
        metric_column=metric_column,
        higher_is_better=higher_is_better,
    )

    summary_path = args.output_dir / f"{stem}_{args.metric}_statistics.csv"
    summary.to_csv(summary_path, index=False)

    friedman_path = args.output_dir / f"{stem}_{args.metric}_friedman.txt"
    with friedman_path.open("w", encoding="utf-8") as file:
        if friedman is None:
            file.write("Friedman test: not enough complete blocks.\n")
        else:
            file.write(
                f"Friedman chi-square={friedman.statistic:.6f}\n"
                f"p-value={friedman.pvalue:.6g}\n"
                f"algorithms={friedman.n_algorithms}\n"
                f"blocks={friedman.n_blocks}\n"
            )

    print(f"Wrote {summary_path}")
    print(f"Wrote {friedman_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
