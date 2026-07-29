from core.constants import VERSION
from core.release import release_health


def test_release_candidate_version():
    assert VERSION == "1.0.0-rc.1"


def test_release_health_reports_missing_repository_items(tmp_path):
    health = release_health(tmp_path)
    assert health.ready is False
    assert health.repository_errors > 0
