"""Build 5 result-contract tests."""

from core.result_contract import normalize_result, validate_result


def test_capitalized_metric_columns_are_normalized():
    result = normalize_result(
        {
            "metrics": [
                {
                    "Structure": "PTV70",
                    "Metric": "V95%",
                    "Score": 100,
                    "Domain": "Target Coverage",
                    "Category": "TV",
                }
            ],
            "domains": {"Target Coverage": 100},
            "overall": 100,
            "grade": "A",
            "treatability": "Treatable",
            "dvhs": {},
        }
    )
    assert result["metrics"][0]["structure"] == "PTV70"
    assert result["metrics"][0]["score"] == 100


def test_valid_result_has_no_contract_issues():
    result = {
        "metrics": [],
        "domains": {},
        "overall": 0,
        "grade": "F",
        "treatability": "Non-Treatable / REPLAN",
        "dvhs": {},
    }
    assert validate_result(result) == []
