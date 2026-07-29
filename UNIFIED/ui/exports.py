"""Shared export serialization helpers."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def json_bytes(payload: Any, *, indent: int = 2) -> bytes:
    return json.dumps(
        payload,
        indent=indent,
        default=str,
        ensure_ascii=False,
    ).encode("utf-8")
