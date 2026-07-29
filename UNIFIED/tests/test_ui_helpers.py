"""Build 4 UI helper tests that do not require rendering Streamlit."""

import pandas as pd

from ui.exports import csv_bytes, json_bytes
from ui.status import score_status, treatability_label, winner
from ui.tables import metrics_dataframe


def test_score_status_thresholds():
    assert score_status(90) == "Achieved"
    assert score_status(75) == "Marginal"
    assert score_status(74.9) == "Failed"
    assert score_status(None) == "Not scored"


def test_treatability_thresholds():
    assert treatability_label(75) == "Treatable"
    assert treatability_label(74.9) == "Marginally Treatable"
    assert treatability_label(60) == "Marginally Treatable"
    assert treatability_label(59.9) == "Non-Treatable / REPLAN"


def test_winner():
    assert winner(90, 80) == "Plan A"
    assert winner(80, 90) == "Plan B"
    assert winner(90, 90) == "Tie"


def test_export_helpers():
    frame = pd.DataFrame([{"Metric": "V95", "Score": 100}])
    assert b"Metric" in csv_bytes(frame)
    assert b'"Score": 100' in json_bytes({"Score": 100})


def test_metrics_dataframe():
    result = {"metrics": [{"Metric": "V95", "Score": 100}]}
    frame = metrics_dataframe(result)
    assert list(frame.columns) == ["Metric", "Score"]
