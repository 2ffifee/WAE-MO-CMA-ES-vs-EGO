"""Summarize experiment CSV files and plot Pareto fronts."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
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

    output_stem = args.input.stem
    summary_path = args.output_dir / f"{output_stem}_summary.csv"
    plot_path = args.output_dir / f"{output_stem}_fronts.png"

    summary.to_csv(summary_path, index=False)
    _plot_problem_fronts(data, plot_path)

    print(summary.to_string(index=False))
    print(f"Wrote summary to {summary_path}")
    print(f"Wrote final front plot to {plot_path}")
    return 0


def _build_summary(data: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["algorithm", "run_id", "seed", "suite", "function_id", "instance", "dimension"]
    aggregate = (
        data.groupby(group_columns, as_index=False)
        .agg(
            evaluations=("evaluation", "max"),
            best_objective_1=("objective_1", "min"),
            best_objective_2=("objective_2", "min"),
            final_objective_1=("objective_1", "last"),
            final_objective_2=("objective_2", "last"),
        )
        .sort_values(group_columns)
    )
    metrics = data.groupby(group_columns).apply(_front_metrics, include_groups=False).reset_index()
    return aggregate.merge(metrics, on=group_columns)


def _front_metrics(group: pd.DataFrame) -> pd.Series:
    points = group[["objective_1", "objective_2"]].to_numpy(dtype=float)
    nondominated = _nondominated_points(points)
    reference = _reference_point(points)
    return pd.Series(
        {
            "nondominated_points": len(nondominated),
            "hypervolume_2d": _hypervolume_2d(nondominated, reference),
        }
    )


def _plot_problem_fronts(data: pd.DataFrame, output_path: Path) -> None:
    selected = _last_problem_data(data)
    algorithms = sorted(selected["algorithm"].unique())

    plt.figure(figsize=(7, 4.8))
    for algorithm in algorithms:
        algorithm_data = selected[selected["algorithm"] == algorithm]
        points = algorithm_data[["objective_1", "objective_2"]].to_numpy(dtype=float)
        nondominated = _nondominated_points(points)

        plt.scatter(
            algorithm_data["objective_1"],
            algorithm_data["objective_2"],
            s=18,
            alpha=0.35,
            label=f"{algorithm} evaluated",
        )
        if len(nondominated):
            order = nondominated[:, 0].argsort()
            plt.plot(
                nondominated[order, 0],
                nondominated[order, 1],
                marker="o",
                linewidth=1.2,
                label=f"{algorithm} nondominated",
            )

    plt.xlabel("objective 1")
    plt.ylabel("objective 2")
    plt.title(_plot_title(selected))
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def _last_problem_data(data: pd.DataFrame) -> pd.DataFrame:
    last_row = data.iloc[-1]
    return data[
        (data["run_id"] == last_row["run_id"])
        & (data["seed"] == last_row["seed"])
        & (data["function_id"] == last_row["function_id"])
        & (data["instance"] == last_row["instance"])
        & (data["dimension"] == last_row["dimension"])
    ]


def _nondominated_points(points: np.ndarray) -> np.ndarray:
    nondominated = []
    for point in points:
        dominated = (
            (points[:, 0] <= point[0])
            & (points[:, 1] <= point[1])
            & ((points[:, 0] < point[0]) | (points[:, 1] < point[1]))
        ).any()
        if not dominated:
            nondominated.append(point)
    if not nondominated:
        return np.empty((0, 2), dtype=float)
    return np.asarray(nondominated, dtype=float)


def _reference_point(points: np.ndarray) -> np.ndarray:
    span = points.max(axis=0) - points.min(axis=0)
    margin = np.maximum(span * 0.1, 1.0)
    return points.max(axis=0) + margin


def _hypervolume_2d(points: np.ndarray, reference: np.ndarray) -> float:
    if not len(points):
        return 0.0

    ordered = points[points[:, 0].argsort()]
    area = 0.0
    best_y = reference[1]
    for x_value, y_value in ordered:
        if y_value < best_y:
            area += max(reference[0] - x_value, 0.0) * max(best_y - y_value, 0.0)
            best_y = y_value
    return float(area)


def _plot_title(data: pd.DataFrame) -> str:
    row = data.iloc[-1]
    return (
        f"{row['algorithm']} on {row['suite']} "
        f"f{int(row['function_id'])}, i{int(row['instance'])}, d{int(row['dimension'])}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
