from core.metric_engine import (
    score_lower_is_better,
    score_target_coverage,
    score_target_minimum,
    score_v105,
)


def test_hn_upper_limit_scale():
    assert score_lower_is_better(
        20, preferred=26, ideal=20, profile="head_neck"
    ).score == 100
    assert score_lower_is_better(
        26, preferred=26, ideal=20, profile="head_neck"
    ).score == 90
    assert score_lower_is_better(
        27, preferred=26, ideal=20, profile="head_neck"
    ).score == 0


def test_v105_scale():
    assert score_v105(5).score == 100
    assert score_v105(10).score == 90
    assert score_v105(20).score == 0


def test_target_coverage_and_minimum():
    assert score_target_coverage(100, 100).score == 100
    assert score_target_coverage(95, 95).score == 90
    assert score_target_coverage(90, 94).score == 0
    assert score_target_minimum(80).score == 100
    assert score_target_minimum(79.9).score == 0
