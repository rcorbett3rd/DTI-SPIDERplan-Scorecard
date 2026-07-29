from core.prescription_engine import (
    assign_target_prescriptions,
    dose_from_structure_name,
)
from sites.registry import get_site


def test_numeric_dose_extraction():
    assert dose_from_structure_name("PTV_7000") == 70.0
    assert dose_from_structure_name("PTV63") == 63.0


def test_hn_semantic_and_eval_inheritance():
    site = get_site("Head & Neck")
    assignments = assign_target_prescriptions(
        ["PTV_High", "PTV_Low", "PTV_Low_eval"],
        is_target=site.is_target,
        is_eval_target=site.is_eval_target,
        semantic_doses=site.PROFILE.standard_prescriptions_gy,
        plan_prescription_gy=70,
    )
    result = {item.structure: item.prescription_gy for item in assignments}
    assert result["PTV_High"] == 70.0
    assert result["PTV_Low"] == 56.0
    assert result["PTV_Low_eval"] == 56.0
