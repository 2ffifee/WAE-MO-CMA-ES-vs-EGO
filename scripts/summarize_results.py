"""Summarize a MO-CMA-ES experiment CSV and plot final objective values."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results") / "raw" / "mo_cma_es_smoke.csv",
        help="Path to an experiment CSV produced by scripts/run_experiment.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results") / "processed",
        help="Directory for summary tables and plots.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = pd.read_csv(args.input)
    if data.empty:
        raise ValueError(f"Input file {args.input} does not contain any evaluations.")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = _build_summary(data)

    summary_path = args.output_dir / "mo_cma_es_smoke_summary.csv"
    plot_path = args.output_dir / "mo_cma_es_smoke_front.png"

    summary.to_csv(summary_path, index=False)
    _plot_final_front(data, plot_path)

    print(summary.to_string(index=False))
    print(f"Wrote summary to {summary_path}")
    print(f"Wrote final front plot to {plot_path}")
    return 0


def _build_summary(data: pd.DataFrame) -> pd.DataFrame:
    grouped = data.groupby(
        ["algorithm", "run_id", "seed", "suite", "function_id", "instance", "dimension"],
        as_index=False,
    )
    return grouped.agg(
        evaluations=("evaluation", "max"),
        best_objective_1=("objective_1", "min"),
        best_objective_2=("objective_2", "min"),
        final_objective_1=("objective_1", "last"),
        final_objective_2=("objective_2", "last"),
    )


def _plot_final_front(data: pd.DataFrame, output_path: Path) -> None:
    last_problem = data[
        (data["function_id"] == data["function_id"].iloc[-1])
        & (data["instance"] == data["instance"].iloc[-1])
        & (data["dimension"] == data["dimension"].iloc[-1])
    ]
    nondominated = _nondominated_points(
        last_problem[["objective_1", "objective_2"]].to_numpy(dtype=float)
    )

    plt.figure(figsize=(6, 4))
    plt.scatter(
        last_problem["objective_1"],
        last_problem["objective_2"],
        s=18,
        alpha=0.45,
        label="evaluated points",
    )
    if len(nondominated):
        order = nondominated[:, 0].argsort()
        plt.plot(
            nondominated[order, 0],
            nondominated[order, 1],
            marker="o",
            linewidth=1.2,
            label="nondominated points",
        )
    plt.xlabel("objective 1")
    plt.ylabel("objective 2")
    plt.title(_plot_title(last_problem))
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _nondominated_points(points):
    nondominated = []
    for index, point in enumerate(points):
        dominated = (
            (points[:, 0] <= point[0])
            & (points[:, 1] <= point[1])
            & ((points[:, 0] < point[0]) | (points[:, 1] < point[1]))
        ).any()
        if not dominated:
            nondominated.append(point)
    return pd.DataFrame(nondominated).to_numpy(dtype=float)


def _plot_title(data: pd.DataFrame) -> str:
    row = data.iloc[-1]
    return (
        f"{row['algorithm']} on {row['suite']} "
        f"f{int(row['function_id'])}, i{int(row['instance'])}, d{int(row['dimension'])}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
