"""Build 3 treatment-site registry smoke tests."""

from sites.registry import display_names, get_site, normalize_site_key


def test_display_names():
    assert display_names() == ("Prostate", "Head & Neck")


def test_site_aliases():
    assert normalize_site_key("Prostate") == "prostate"
    assert normalize_site_key("Head & Neck") == "head_neck"
    assert normalize_site_key("HN") == "head_neck"


def test_prostate_profile_loads():
    site = get_site("Prostate")
    assert site.PROFILE.key == "prostate"
    assert site.canonical_oar_name("Rectum") == "Rectum"
    assert len(site.configured_metrics_for("Rectum")) >= 1


def test_head_neck_profile_loads():
    site = get_site("Head & Neck")
    assert site.PROFILE.key == "head_neck"
    assert site.canonical_oar_name("SpinalCord") == "SpinalCord"
    assert len(site.configured_metrics_for("Mandible")) == 1


def test_hn_eval_target_logic():
    site = get_site("Head & Neck")
    assert site.is_target("PTV70_eval")
    assert site.is_eval_target("PTV70_eval")
    assert not site.is_target("zPTV70")
    assert not site.is_target("PTV70_opti")
