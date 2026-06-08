"""Analiza wyników: ERT, data profiles, skalowanie budżetu (konspekt projektu)."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from wae_project.analysis.data_profiles import data_profile, ert_to_hypervolume_threshold
from wae_project.analysis.data_profiles import final_hypervolume_per_run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="CSV z run_experiment.py lub katalog z plikami *.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results") / "processed",
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

    finals = final_hypervolume_per_run(data)
    finals_path = args.output_dir / f"{stem}_final_hypervolume.csv"
    finals.to_csv(finals_path, index=False)

    ert = ert_to_hypervolume_threshold(data)
    ert_path = args.output_dir / f"{stem}_ert.csv"
    ert.to_csv(ert_path, index=False)

    max_budget = int(data["evaluation"].max())
    grid = np.unique(
        np.clip(
            np.array([10, 20, 50, 100, 200, 500, 1000, max_budget]),
            1,
            max_budget,
        )
    )
    profiles = data_profile(data, budget_grid=grid)
    profiles_path = args.output_dir / f"{stem}_data_profiles.csv"
    profiles.to_csv(profiles_path, index=False)

    _plot_data_profiles(profiles, args.output_dir / f"{stem}_data_profiles.png")
    _plot_ert_boxplot(ert, args.output_dir / f"{stem}_ert_boxplot.png")
    _plot_hv_by_algorithm(finals, args.output_dir / f"{stem}_hv_comparison.png")

    print(f"Wrote {finals_path}")
    print(f"Wrote {ert_path}")
    print(f"Wrote {profiles_path}")
    return 0


def _plot_data_profiles(profiles: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for algorithm in profiles["algorithm"].unique():
        sub = profiles[profiles["algorithm"] == algorithm].sort_values("budget_limit")
        ax.plot(
            sub["budget_limit"],
            sub["solved_fraction"],
            "o-",
            label=algorithm,
            linewidth=2,
        )
    ax.set_xlabel("Limit budżetu ewaluacji")
    ax.set_ylabel("Frakcja problemów (proxy HV)")
    ax.set_title("Data profiles (uproszczone)")
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_ert_boxplot(ert: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    algorithms = sorted(ert["algorithm"].unique())
    data = [ert.loc[ert["algorithm"] == a, "ert_evaluations"].to_numpy() for a in algorithms]
    ax.boxplot(data, labels=algorithms)
    ax.set_ylabel("ERT (ewaluacje do progu HV)")
    ax.set_title("Porównanie ERT (proxy)")
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_hv_by_algorithm(finals: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    algorithms = sorted(finals["algorithm"].unique())
    data = [finals.loc[finals["algorithm"] == a, "final_hypervolume"].to_numpy() for a in algorithms]
    ax.boxplot(data, labels=algorithms)
    ax.set_ylabel("Końcowy hypervolume 2D")
    ax.set_title("Rozkład jakości frontów Pareto")
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
