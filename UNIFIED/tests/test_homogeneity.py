import math

from core.homogeneity import (
    homogeneity_index,
    score_homogeneity_index,
    should_score_target_homogeneity,
)


def test_formula():
    assert math.isclose(homogeneity_index(74.0, 70.0, 67.0), 0.1)


def test_invalid_d50():
    assert homogeneity_index(74.0, 0.0, 67.0) is None


def test_score_boundaries():
    assert score_homogeneity_index(0.10).score == 100.0
    assert score_homogeneity_index(0.15).score == 90.0
    assert score_homogeneity_index(0.20).score == 50.0
    assert score_homogeneity_index(0.21).score == 0.0


def test_midpoint_interpolation():
    assert score_homogeneity_index(0.125).score == 95.0
    assert score_homogeneity_index(0.175).score == 70.0


def test_sib_target_selection():
    assert should_score_target_homogeneity("PTV_High", 70.0, 70.0)
    assert not should_score_target_homogeneity("PTV_Low", 56.0, 70.0)
    assert should_score_target_homogeneity("PTV_Low_eval", 56.0, 70.0)
    assert not should_score_target_homogeneity("PTV_Low_opti", 56.0, 70.0)
    assert not should_score_target_homogeneity("CTV_High", 70.0, 70.0)
