"""Log experiment evaluations in COCO format for cocopp post-processing."""

from __future__ import annotations

from pathlib import Path

from wae_project.benchmarks.coco_biobj import CocoBiobjProblem, _import_cocoex

BBOB_BIOBJ_FUNCTION_COUNT = 55

COCO_ALGORITHM_NAMES = {
    "mo-cma-es": "MO-CMA-ES",
    "parego": "ParEGO",
}


def ensure_exdata_root() -> Path:
    """COCO writes under ``exdata/`` relative to the process working directory."""

    root = Path("exdata")
    root.mkdir(parents=True, exist_ok=True)
    return root


def coco_result_subfolder(result_root: Path, algorithm: str) -> str:
    """
    Return a ``result_folder`` option for :class:`cocoex.Observer`.

    COCO prepends ``exdata/`` automatically, so do not include that prefix here.
    """

    safe = algorithm.replace(" ", "_").replace("/", "_")
    relative = result_root / safe
    text = relative.as_posix()
    if text.startswith("exdata/"):
        text = text[len("exdata/") :]
    return text


class CocoRunLogger:
    """Attach a COCO observer to one problem for the duration of a single run."""

    def __init__(self, suite: str, result_root: Path, algorithm: str) -> None:
        self._suite = suite
        self._algorithm = algorithm
        self._folder = coco_result_subfolder(result_root, algorithm)
        self._observer = None

    def attach(self, problem: CocoBiobjProblem) -> None:
        cocoex = _import_cocoex()
        display_name = COCO_ALGORITHM_NAMES.get(self._algorithm, self._algorithm)
        options = f"result_folder: {self._folder} algorithm_name: {display_name}"
        self._observer = cocoex.Observer(self._suite, options)
        problem.observe_with(self._observer)

    @property
    def result_folder(self) -> str:
        return self._folder
