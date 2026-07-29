from core.comparison_engine import compare_results


def _result(name, overall, target, oar):
    return {
        "display_name": name,
        "metrics": [
            {
                "structure": "PTV",
                "metric": "Coverage",
                "domain": "Target",
                "category": "TV",
                "score": target,
            },
            {
                "structure": "Rectum",
                "metric": "V75",
                "domain": "OAR",
                "category": "OAR",
                "score": oar,
            },
        ],
        "domains": {"Target": target, "OAR": oar},
        "overall": overall,
        "grade": "",
        "treatability": "",
        "dvhs": {},
    }


def test_comparison_summary():
    summary = compare_results(
        _result("Clinical", 85, 90, 80),
        _result("AI", 90, 95, 85),
    )
    assert summary.winner == "Plan B"
    assert summary.difference == -5
    assert summary.target_b == 95
    assert len(summary.metric_rows) == 2
