"""Build 5 shared post-analysis pipeline test."""

from core.score_pipeline import ScorePipelineOptions, process_scored_result


def test_pipeline_applies_assignment_and_inclusion():
    raw = {
        "metrics": [
            {
                "structure": "Plan",
                "domain": "Plan Modulation",
                "category": "Plan",
                "score": 90,
            },
            {
                "structure": "Cord",
                "domain": "Critical OARs",
                "category": "OAR",
                "oar_group": "SpinalCord",
                "score": 80,
            },
            {
                "structure": "Cord-PTV",
                "domain": "Critical OARs",
                "category": "OAR",
                "oar_group": "SpinalCord",
                "score": 95,
            },
        ],
        "domains": {},
        "overall": 0,
        "grade": "",
        "treatability": "",
        "dvhs": {},
        "oar_candidates": {"SpinalCord": ["Cord", "Cord-PTV"]},
    }

    output = process_scored_result(
        raw,
        options=ScorePipelineOptions(
            treatment_site="Head & Neck",
            oar_assignments={"SpinalCord": "Cord-PTV"},
            included_structures={"Cord-PTV"},
        ),
    )

    structures = [row["structure"] for row in output.result["metrics"]]
    assert structures == ["Plan", "Cord-PTV"]
    assert output.result["treatment_site"] == "Head & Neck"
    assert output.validation_issues == []
