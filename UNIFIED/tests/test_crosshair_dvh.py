"""Build 4 crosshair DVH smoke tests."""

from ui.dvh import make_crosshair_dvh, make_comparison_crosshair_dvh


SAMPLE = {
    "PTV70": {
        "dose_gy": [0, 35, 70],
        "volume_pct": [100, 99, 95],
        "category": "TV",
    }
}


def test_single_dvh():
    figure = make_crosshair_dvh(SAMPLE)
    assert len(figure.data) == 1
    assert figure.layout.hovermode == "x unified"


def test_comparison_dvh():
    figure = make_comparison_crosshair_dvh(SAMPLE, SAMPLE)
    assert len(figure.data) == 2
    assert figure.data[1].line.dash == "dash"
