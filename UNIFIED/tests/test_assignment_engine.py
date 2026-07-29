"""Build 5 shared assignment-engine tests."""

from core.assignment_engine import (
    apply_oar_assignments,
    apply_score_inclusions,
    default_oar_candidate,
    scored_structures,
)


SAMPLE = {
    "metrics": [
        {
            "structure": "Plan",
            "metric": "MUF",
            "domain": "Plan Modulation",
            "category": "Plan",
            "score": 90,
        },
        {
            "structure": "Rectum",
            "metric": "V75Gy",
            "domain": "OAR Sparing",
            "category": "OAR",
            "oar_group": "Rectum",
            "score": 80,
        },
        {
            "structure": "Rectum-PTV",
            "metric": "V75Gy",
            "domain": "OAR Sparing",
            "category": "OAR",
            "oar_group": "Rectum",
            "score": 95,
        },
        {
            "structure": "PTV70",
            "metric": "V95%",
            "domain": "Target Coverage",
            "category": "TV",
            "score": 100,
        },
    ],
    "domains": {},
    "overall": 0,
    "grade": "",
    "treatability": "",
    "dvhs": {},
    "oar_candidates": {"Rectum": ["Rectum", "Rectum-PTV"]},
}


def test_default_candidate_prefers_base_structure():
    assert default_oar_candidate("Rectum", ["Rectum-PTV", "Rectum"]) == "Rectum"


def test_assignment_filters_duplicate_oar_candidates():
    result = apply_oar_assignments(SAMPLE, {"Rectum": "Rectum-PTV"})
    structures = [row["structure"] for row in result["metrics"]]
    assert "Rectum-PTV" in structures
    assert "Rectum" not in structures


def test_scored_structures_excludes_plan():
    assert scored_structures(SAMPLE) == ["PTV70", "Rectum", "Rectum-PTV"]


def test_score_inclusion_recalculates_domains():
    result = apply_score_inclusions(SAMPLE, {"PTV70", "Rectum"})
    assert result["domains"]["Target Coverage"] == 100
    assert result["domains"]["OAR Sparing"] == 80
    assert result["domains"]["Plan Modulation"] == 90
    assert result["overall"] == 90
