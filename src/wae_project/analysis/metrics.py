"""Metryki Pareto: front niezdominowany, hypervolume 2D."""

from __future__ import annotations

import numpy as np


def nondominated_points(points: np.ndarray) -> np.ndarray:
    if len(points) == 0:
        return np.empty((0, 2), dtype=float)
    nondominated = []
    for point in points:
        dominated = (
            (points[:, 0] <= point[0])
            & (points[:, 1] <= point[1])
            & ((points[:, 0] < point[0]) | (points[:, 1] < point[1]))
        ).any()
        if not dominated:
            nondominated.append(point)
    return np.asarray(nondominated, dtype=float)


def reference_point(points: np.ndarray, margin_ratio: float = 0.1) -> np.ndarray:
    if len(points) == 0:
        return np.array([1.0, 1.0])
    span = points.max(axis=0) - points.min(axis=0)
    margin = np.maximum(span * margin_ratio, 1.0)
    return points.max(axis=0) + margin


def hypervolume_2d(points: np.ndarray, ref: np.ndarray) -> float:
    """Hypervolume 2D (minimalizacja obu celów)."""
    if len(points) == 0:
        return 0.0
    ordered = points[points[:, 0].argsort()]
    area = 0.0
    best_y = ref[1]
    for x_value, y_value in ordered:
        if y_value < best_y:
            area += max(ref[0] - x_value, 0.0) * max(best_y - y_value, 0.0)
            best_y = y_value
    return float(area)


def cumulative_hypervolume_trace(
    objectives: np.ndarray, ref: np.ndarray | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Zwraca (evaluations, hypervolume) po kolejnych ewaluacjach."""
    if ref is None:
        ref = reference_point(objectives)
    evaluations = np.arange(1, len(objectives) + 1)
    hvs = []
    for i in range(1, len(objectives) + 1):
        nd = nondominated_points(objectives[:i])
        hvs.append(hypervolume_2d(nd, ref))
    return evaluations, np.asarray(hvs, dtype=float)
