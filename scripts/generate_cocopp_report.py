"""Generate COCO post-processing reports (HTML/LaTeX) via cocopp."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("exdata") / "coco",
        help="Folder under exdata/ with COCO result subfolders per algorithm.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results") / "coco_reports",
        help="Directory for cocopp output (working directory during run).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = args.data_dir
    if not data_dir.is_dir():
        print(
            f"COCO data directory not found: {data_dir}\n"
            "Run experiments with coco_output_dir set in the YAML first.",
            file=sys.stderr,
        )
        return 1

    try:
        import cocopp
    except ImportError:
        print("cocopp is not installed. Run: python -m pip install -e .", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    # cocopp resolves paths relative to cwd; use exdata-prefixed folder names.
    folder_arg = str(data_dir.as_posix())
    if not folder_arg.startswith("exdata/"):
        folder_arg = f"exdata/{folder_arg}"

    print(f"Running cocopp on {folder_arg}")
    try:
        cocopp.main(folder_arg)
    except SystemExit as exc:
        if int(exc.code) != 0:
            print(f"cocopp exited with code {exc.code}", file=sys.stderr)
            return int(exc.code)
    except Exception as exc:
        print(f"cocopp failed: {exc}", file=sys.stderr)
        return 1

    print(f"cocopp report generated (see cwd and {args.output_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
