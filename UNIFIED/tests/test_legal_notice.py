from core.constants import LEGAL_NOTICE


def test_legal_notice_contains_required_scope():
    assert "research, development, and plan-review support only" in LEGAL_NOTICE
    assert "does not replace physician approval" in LEGAL_NOTICE
    assert "physicist QA" in LEGAL_NOTICE
