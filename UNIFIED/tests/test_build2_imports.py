"""Build 2 smoke tests.

Run from the repository root with:
    python -m pytest tests/test_build2_imports.py
"""

from core import constants
from core.comparison_engine import compare_scores
from core.dicom_engine import normalize_site


def test_supported_sites():
    assert constants.SUPPORTED_SITES == ("Prostate", "Head & Neck")


def test_site_normalization():
    assert normalize_site("Prostate") == "prostate"
    assert normalize_site("Head & Neck") == "head_neck"
    assert normalize_site("HN") == "head_neck"


def test_score_comparison():
    result = compare_scores(91.0, 87.5)
    assert result["winner"] == "Plan A"
    assert result["difference"] == 3.5
