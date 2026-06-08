import numpy as np

from wae_project.analysis.metrics import hypervolume_2d, nondominated_points


def test_nondominated_filters_dominated():
    points = np.array([[1.0, 2.0], [2.0, 1.0], [3.0, 3.0]])
    nd = nondominated_points(points)
    assert len(nd) == 2


def test_hypervolume_positive():
    points = np.array([[1.0, 2.0], [2.0, 1.0]])
    ref = np.array([5.0, 5.0])
    hv = hypervolume_2d(points, ref)
    assert hv > 0
