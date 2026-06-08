"""Orchestrate all experiment phases from configs/study_plan.yaml."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path("configs") / "study_plan.yaml",
        help="Study plan YAML.",
    )
    parser.add_argument(
        "--phase",
        type=str,
        default=None,
        help="Run only this phase id (default: all phases).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing.",
    )
    parser.add_argument(
        "--skip-analysis",
        action="store_true",
        help="Do not run analyze/statistics/cocopp after experiments.",
    )
    return parser.parse_args()


def _run_command(cmd: list[str], dry_run: bool) -> int:
    print(" ".join(cmd))
    if dry_run:
        return 0
    result = subprocess.run(cmd, check=False)
    return int(result.returncode)


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent.parent
    scripts = root / "scripts"

    with args.plan.open("r", encoding="utf-8") as file:
        plan = yaml.safe_load(file)

    phases = plan.get("phases", [])
    if not isinstance(phases, list):
        raise ValueError("study_plan.yaml must contain a 'phases' list.")

    for phase in phases:
        phase_id = phase.get("id")
        if args.phase is not None and phase_id != args.phase:
            continue

        phase_type = phase.get("type", "experiment")
        print(f"\n### Phase: {phase_id} ({phase_type}) ###")

        if phase_type == "experiment":
            config_path = root / phase["config"]
            cmd = [
                sys.executable,
                str(scripts / "run_experiment.py"),
                "--config",
                str(config_path),
            ]
            if phase.get("resume", False):
                cmd.append("--resume")
            code = _run_command(cmd, args.dry_run)
            if code != 0:
                return code

        elif phase_type == "full_benchmark":
            config_path = root / phase["config"]
            cmd = [
                sys.executable,
                str(scripts / "run_full_benchmark.py"),
                "--config",
                str(config_path),
                "--chunk-size",
                str(phase.get("chunk_size", 5)),
            ]
            if phase.get("resume", False):
                cmd.append("--resume")
            code = _run_command(cmd, args.dry_run)
            if code != 0:
                return code

        elif phase_type == "budget_sweep":
            config_path = root / phase["config"]
            multipliers = ",".join(str(value) for value in phase["multipliers"])
            output_dir = root / phase.get("output_dir", "results/raw/budget_sweep")
            cmd = [
                sys.executable,
                str(scripts / "run_budget_sweep.py"),
                "--config",
                str(config_path),
                "--multipliers",
                multipliers,
                "--output-dir",
                str(output_dir),
            ]
            code = _run_command(cmd, args.dry_run)
            if code != 0:
                return code

        else:
            raise ValueError(f"Unsupported phase type: {phase_type!r}")

        if not args.skip_analysis and phase.get("analyze"):
            for analyze in phase["analyze"]:
                analyze_type = analyze.get("type")
                if analyze_type == "analyze_results":
                    cmd = [
                        sys.executable,
                        str(scripts / "analyze_results.py"),
                        "--input",
                        str(root / analyze["input"]),
                        "--output-dir",
                        str(root / analyze.get("output_dir", "results/processed")),
                    ]
                    code = _run_command(cmd, args.dry_run)
                    if code != 0:
                        return code
                elif analyze_type == "statistics":
                    cmd = [
                        sys.executable,
                        str(scripts / "run_statistics.py"),
                        "--input",
                        str(root / analyze["input"]),
                        "--output-dir",
                        str(root / analyze.get("output_dir", "results/processed")),
                    ]
                    code = _run_command(cmd, args.dry_run)
                    if code != 0:
                        return code
                elif analyze_type == "cocopp":
                    cmd = [
                        sys.executable,
                        str(scripts / "generate_cocopp_report.py"),
                        "--data-dir",
                        str(root / analyze["data_dir"]),
                    ]
                    code = _run_command(cmd, args.dry_run)
                    if code != 0:
                        return code

    print("\nStudy plan finished.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
