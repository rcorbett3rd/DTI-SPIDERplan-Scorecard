"""Shared metric-table styling based on the finalized Prostate interface."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def _row_style(row: pd.Series) -> list[str]:
    status = str(row.get("Status", ""))
    score = row.get("Score", math.nan)

    if status == "Missing eval structure":
        css = "background-color:#00AEEF;color:#00111A;font-weight:700;"
    elif pd.isna(score):
        css = "background-color:#4b5563;color:white;"
    elif float(score) >= 90:
        css = "background-color:#dcfce7;color:#14532d;"
    elif float(score) >= 75:
        css = "background-color:#fef9c3;color:#713f12;"
    else:
        css = "background-color:#fee2e2;color:#7f1d1d;"

    return [css] * len(row)


def style_metric_table(df: pd.DataFrame):
    """Apply shared clinical status styling to a metric DataFrame."""

    if df.empty:
        return df.style

    formatters: dict[str, Any] = {}
    if "Score" in df.columns:
        formatters["Score"] = "{:.1f}"

    return df.style.apply(_row_style, axis=1).format(formatters, na_rep="—")


def metrics_dataframe(result: dict[str, Any] | None) -> pd.DataFrame:
    """Return a safe metric DataFrame from the shared result contract."""

    if not result:
        return pd.DataFrame()
    rows = result.get("metrics", [])
    return pd.DataFrame(rows if isinstance(rows, list) else [])
