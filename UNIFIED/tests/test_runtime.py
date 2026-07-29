from core.runtime import prepare_comparison, prepare_plan


RAW = {
    "metrics": [
        {
            "structure": "Plan",
            "metric": "MUF",
            "domain": "Plan Quality",
            "category": "Plan",
            "score": 90,
        },
        {
            "structure": "PTV",
            "metric": "Coverage",
            "domain": "Target",
            "category": "TV",
            "score": 100,
        },
    ],
    "domains": {},
    "overall": 0,
    "grade": "",
    "treatability": "",
    "dvhs": {},
}


def test_runtime_prepares_plan_and_comparison():
    plan_a = prepare_plan(
        RAW,
        display_name="Plan A",
        treatment_site="Prostate",
        included_structures={"PTV"},
    )
    plan_b = prepare_plan(
        RAW,
        display_name="Plan B",
        treatment_site="Prostate",
        included_structures={"PTV"},
    )
    summary = prepare_comparison(plan_a, plan_b)
    assert summary.winner == "Tie"
    assert plan_a.result["overall"] == 95
