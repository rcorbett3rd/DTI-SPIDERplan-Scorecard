from __future__ import annotations

import io
import math
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pydicom
from dicompylercore import dicomparser, dvhcalc


@dataclass
class PlanFiles:
    plan: pydicom.dataset.FileDataset
    structures: pydicom.dataset.FileDataset
    dose: pydicom.dataset.FileDataset
    plan_bytes: bytes
    structures_bytes: bytes
    dose_bytes: bytes


def _read_bytes(uploaded: Any) -> bytes:
    uploaded.seek(0)
    return uploaded.read()


def classify_files(uploaded_files: list[Any]) -> PlanFiles:
    found: dict[str, tuple[Any, bytes]] = {}
    for f in uploaded_files:
        raw = _read_bytes(f)
        ds = pydicom.dcmread(io.BytesIO(raw), force=True)
        modality = str(getattr(ds, "Modality", "")).upper()
        if modality in {"RTPLAN", "RTSTRUCT", "RTDOSE"}:
            found[modality] = (ds, raw)
    missing = [m for m in ("RTPLAN", "RTSTRUCT", "RTDOSE") if m not in found]
    if missing:
        raise ValueError("Missing required DICOM object(s): " + ", ".join(missing))
    return PlanFiles(
        plan=found["RTPLAN"][0],
        structures=found["RTSTRUCT"][0],
        dose=found["RTDOSE"][0],
        plan_bytes=found["RTPLAN"][1],
        structures_bytes=found["RTSTRUCT"][1],
        dose_bytes=found["RTDOSE"][1],
    )


def plan_label(plan: pydicom.dataset.Dataset) -> str:
    return str(getattr(plan, "RTPlanLabel", getattr(plan, "RTPlanName", "Unnamed Plan")))


def treatment_beam_mus(plan: pydicom.dataset.Dataset) -> list[float]:
    beam_mu: dict[int, float] = {}
    for fg in getattr(plan, "FractionGroupSequence", []):
        for ref in getattr(fg, "ReferencedBeamSequence", []):
            num = int(getattr(ref, "ReferencedBeamNumber", -1))
            beam_mu[num] = max(beam_mu.get(num, 0.0), float(getattr(ref, "BeamMeterset", 0.0) or 0.0))

    valid_nums: set[int] = set()
    for beam in getattr(plan, "BeamSequence", []):
        num = int(getattr(beam, "BeamNumber", -1))
        delivery = str(getattr(beam, "TreatmentDeliveryType", "TREATMENT")).upper()
        radiation = str(getattr(beam, "RadiationType", "PHOTON")).upper()
        if delivery in {"TREATMENT", "CONTINUATION"} and radiation in {"PHOTON", "X-RAY", "X"}:
            valid_nums.add(num)
    return [mu for num, mu in beam_mu.items() if num in valid_nums and mu > 0]


def fraction_count(plan: pydicom.dataset.Dataset) -> int | None:
    vals = []
    for fg in getattr(plan, "FractionGroupSequence", []):
        n = getattr(fg, "NumberOfFractionsPlanned", None)
        if n:
            vals.append(int(n))
    return max(vals) if vals else None


def _normalize_plan_dose_gy(value: float) -> float:
    """Normalize plan prescription values to Gy."""
    dose = float(value)
    return dose / 100.0 if dose > 250.0 else dose


def prescription_dose_gy(plan: pydicom.dataset.Dataset) -> float | None:
    candidates: list[float] = []
    for dr in getattr(plan, "DoseReferenceSequence", []):
        val = getattr(dr, "TargetPrescriptionDose", None)
        if val is not None:
            candidates.append(_normalize_plan_dose_gy(float(val)))
        val = getattr(dr, "DeliveryMaximumDose", None)
        if val is not None:
            candidates.append(_normalize_plan_dose_gy(float(val)))
    return max(candidates) if candidates else None


def fraction_dose_cgy(plan: pydicom.dataset.Dataset, fallback_rx_gy: float | None = None) -> float | None:
    rx = prescription_dose_gy(plan) or fallback_rx_gy
    n = fraction_count(plan)
    if rx and n:
        return rx * 100.0 / n
    return None


def modulation_factor(plan: pydicom.dataset.Dataset, fallback_rx_gy: float | None = None) -> dict[str, float | None]:
    mus = treatment_beam_mus(plan)
    total = float(sum(mus))
    fx = fraction_dose_cgy(plan, fallback_rx_gy)
    return {"total_mu": total, "fraction_dose_cgy": fx, "muf": total / fx if fx and fx > 0 else None}


def structure_names(ds: pydicom.dataset.Dataset) -> dict[int, str]:
    parser = dicomparser.DicomParser(ds)
    return {int(k): str(v["name"]) for k, v in parser.GetStructures().items()}


def calculate_dvh(files: PlanFiles, roi_number: int):
    # dicompyler-core supports paths most reliably, so persist temporary DICOM objects.
    with tempfile.TemporaryDirectory() as td:
        p = Path(td)
        rs_path = p / "RS.dcm"
        rd_path = p / "RD.dcm"
        rs_path.write_bytes(files.structures_bytes)
        rd_path.write_bytes(files.dose_bytes)
        return dvhcalc.get_dvh(str(rs_path), str(rd_path), roi_number)


def _dose_scale_to_gy(dvh) -> float:
    """Return the conversion factor needed to express DVH dose values in Gy."""
    units = str(getattr(dvh, "dose_units", "") or "").strip().lower()
    if units in {"cgy", "centigray", "centigrays"}:
        return 0.01
    if units in {"gy", "gray", "grays"}:
        return 1.0

    # Defensive fallback for non-standard exports.
    raw_doses = np.asarray(getattr(dvh, "bincenters", []), dtype=float)
    finite = raw_doses[np.isfinite(raw_doses)]
    return 0.01 if finite.size and float(np.nanmax(finite)) > 250.0 else 1.0


def _dose_value_gy(value: float, dvh) -> float:
    return float(value) * _dose_scale_to_gy(dvh)


def dvh_arrays(dvh) -> tuple[np.ndarray, np.ndarray, float]:
    """Return dose in Gy and cumulative volume.

    dicompyler-core get_dvh returns a cumulative DVH. The previous build
    cumulatively summed those counts a second time, which caused impossible
    values such as V30Gy above 100%.
    """
    doses = np.asarray(dvh.bincenters, dtype=float) * _dose_scale_to_gy(dvh)
    counts = np.asarray(dvh.counts, dtype=float)

    if counts.size == 0:
        return doses, counts, 0.0

    dvh_type = str(getattr(dvh, "dvh_type", "cumulative") or "cumulative").lower()
    cumulative = (
        np.cumsum(counts[::-1])[::-1]
        if dvh_type == "differential"
        else counts.copy()
    )

    cumulative = np.maximum.accumulate(cumulative[::-1])[::-1]
    cumulative = np.clip(cumulative, 0.0, None)

    volume_units = str(getattr(dvh, "volume_units", "cm3") or "cm3").lower()
    total_volume = 100.0 if volume_units in {"%", "percent", "relative"} else float(cumulative[0])
    return doses, cumulative, total_volume


def volume_at_dose(dvh, dose_gy: float, relative: bool) -> float:
    doses, cumulative_volume, total_volume = dvh_arrays(dvh)
    if doses.size == 0 or cumulative_volume.size == 0:
        return math.nan

    value = float(
        np.interp(
            float(dose_gy),
            doses,
            cumulative_volume,
            left=float(cumulative_volume[0]),
            right=0.0,
        )
    )
    value = max(0.0, min(value, total_volume)) if total_volume > 0 else max(0.0, value)

    if relative:
        if total_volume <= 0:
            return math.nan
        return max(0.0, min(100.0, 100.0 * value / total_volume))
    return value


def dose_at_volume_cc(dvh, volume_cc: float) -> float:
    doses, cumulative_volume, total_volume = dvh_arrays(dvh)
    if doses.size == 0 or cumulative_volume.size == 0:
        return math.nan

    target = max(0.0, min(float(volume_cc), total_volume))
    return float(
        np.interp(
            target,
            cumulative_volume[::-1],
            doses[::-1],
            left=float(doses[-1]),
            right=float(doses[0]),
        )
    )


def mean_dose(dvh) -> float:
    try:
        return _dose_value_gy(float(dvh.mean), dvh)
    except Exception:
        doses = np.asarray(dvh.bincenters, dtype=float) * _dose_scale_to_gy(dvh)
        counts = np.asarray(dvh.counts, dtype=float)
        if doses.size == 0 or counts.size == 0:
            return math.nan

        dvh_type = str(getattr(dvh, "dvh_type", "cumulative") or "cumulative").lower()
        if dvh_type == "differential":
            differential = counts
            dose_values = doses
        else:
            differential = np.maximum(counts[:-1] - counts[1:], 0.0)
            dose_values = doses[:-1]

        return (
            float(np.average(dose_values, weights=differential))
            if differential.size and differential.sum() > 0
            else math.nan
        )


def max_dose(dvh) -> float:
    try:
        return _dose_value_gy(float(dvh.max), dvh)
    except Exception:
        doses, cumulative, _ = dvh_arrays(dvh)
        nz = np.flatnonzero(cumulative > 0)
        return float(doses[nz[-1]]) if nz.size else math.nan


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def target_rx_from_name(name: str, standards: dict[str, float]) -> float | None:
    low = name.lower()
    # Numeric doses override high/mid/low. Prefer 4-digit cGy tokens, then decimal/integer Gy.
    tokens = re.findall(r"(?<!\d)(\d{4})(?!\d)", low)
    if tokens:
        val = float(tokens[-1]) / 100.0
        if 20 <= val <= 100:
            return val
    decimal_tokens = re.findall(r"(?<!\d)(\d{2}(?:[._]\d)?)(?!\d)", low)
    for token in reversed(decimal_tokens):
        val = float(token.replace("_", "."))
        if 20 <= val <= 100:
            return val
    for key in ("high", "mid", "low"):
        if key in low:
            return float(standards[key])
    return None


def is_target(name: str) -> bool:
    """Identify true target structures by a target prefix.

    OAR-derived structures such as ``Bladder-CTV`` or ``Rectum-PTV`` are not
    targets. They are normal-tissue evaluation structures and must remain
    available for OAR assignment.
    """
    low = name.strip().lower()
    if low.startswith("z") or "opti" in low:
        return False
    return bool(re.match(r"^(ptv|ctv|gtv|itv|tv)(?:[^a-z]|$)", low))
