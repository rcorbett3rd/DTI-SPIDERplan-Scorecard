from pathlib import Path

from core.release_validation import validate_plan_result, validate_repository


def test_plan_result_validation():
    result = {
        "metrics": [],
        "domains": {},
        "overall": 0,
        "grade": "",
        "treatability": "",
        "dvhs": {},
    }
    items = validate_plan_result(result)
    codes = {item.code for item in items}
    assert "no_metrics" in codes
    assert "no_dvh" in codes


def test_repository_validation_detects_missing_files(tmp_path: Path):
    items = validate_repository(tmp_path)
    assert any(item.code == "missing_file" for item in items)
