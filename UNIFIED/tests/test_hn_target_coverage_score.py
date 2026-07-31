"""Regression test for H&N PTV coverage scoring.

A valid coverage/minimum-dose score must not be overwritten by a failing
highest-dose V105Rx or D0.03cc review value.
"""

import pandas as pd

from hn_scorecard_engine import _score_target_coverage


def test_valid_ptv_coverage_is_not_zeroed_by_hotspot_review():
    row = pd.Series(
        {
            "structure": "PTV_6000",
            "assigned_rx_gy": 60.0,
            "V100Rx_%": 95.07,
            "V95Rx_%": 98.69,
            "Dmin_%Rx": 86.56,
            # Deliberately failing high-dose review values.
            "D0.03cc_%Rx": 120.0,
            "V105Rx_%": 25.0,
        }
    )

    score, notes = _score_target_coverage(row, highest_rx=60.0)

    assert score == 90.1
    assert "coverage score=90.1" in notes
    assert "min-dose score=100.0" in notes
