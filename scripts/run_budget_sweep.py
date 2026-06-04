"""Uruchamia ten sam eksperyment dla wielu mnożników budżetu (E3 z konspektu)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="Bazowy YAML (bez budget override)")
    parser.add_argument(
        "--multipliers",
        type=str,
        default="10,50,100",
        help="Lista mnożników budżetu, np. 10,50,100,1000",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("results/raw/budget_sweep"))
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip runs already present in each sweep CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    multipliers = [int(x.strip()) for x in args.multipliers.split(",") if x.strip()]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    import yaml

    base_path = args.config
    with base_path.open("r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    for mult in multipliers:
        cfg = dict(base)
        cfg["budget"] = dict(base.get("budget", {}))
        cfg["budget"]["evaluations_multiplier"] = mult
        cfg["experiment"] = dict(base.get("experiment", {}))
        cfg["experiment"]["name"] = f"{base['experiment']['name']}_b{mult}"

        tmp = args.output_dir / f"_tmp_budget_{mult}.yaml"
        out_csv = args.output_dir / f"{cfg['experiment']['name']}.csv"
        with tmp.open("w", encoding="utf-8") as f:
            yaml.dump(cfg, f, allow_unicode=True)

        cmd = [
            sys.executable,
            str(Path(__file__).parent / "run_experiment.py"),
            "--config",
            str(tmp),
            "--output",
            str(out_csv),
        ]
        if args.resume:
            cmd.append("--resume")
        print(" ".join(cmd))
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            return result.returncode
        tmp.unlink(missing_ok=True)

    print(f"Budget sweep done. CSV files in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
