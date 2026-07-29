from core.comparison_engine import compare_results
from core.export_engine import (
    comparison_csv_bytes,
    comparison_json_bytes,
    result_csv_bytes,
    result_json_bytes,
    safe_filename,
)


RESULT = {
    "display_name": "Plan A",
    "metrics": [{"structure": "PTV", "metric": "V95", "score": 100}],
    "domains": {"Target": 100},
    "overall": 100,
    "grade": "A",
    "treatability": "Treatable",
    "dvhs": {},
}


def test_result_exports():
    assert b"structure" in result_csv_bytes(RESULT)
    assert b'"overall": 100' in result_json_bytes(RESULT)


def test_comparison_exports():
    summary = compare_results(RESULT, RESULT)
    assert b"Structure" in comparison_csv_bytes(summary)
    assert b'"winner": "Tie"' in comparison_json_bytes(summary)


def test_safe_filename():
    assert safe_filename("Plan A / Test", ".csv") == "Plan_A___Test.csv"
