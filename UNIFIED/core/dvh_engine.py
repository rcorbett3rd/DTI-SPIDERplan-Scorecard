"""Shared DVH façade.

The finalized Prostate DVH functions and the Head & Neck voxel-based DVH
functions remain intact. This module provides explicit shared imports and avoids
silently replacing either site's clinical calculations.
"""

from __future__ import annotations

import hn_dvh_engine as head_neck
import prostate_dicom_engine as prostate


# Finalized Prostate DVH helpers.
dvh_arrays = prostate.dvh_arrays
volume_at_dose = prostate.volume_at_dose
dose_at_volume_cc = prostate.dose_at_volume_cc
mean_dose = prostate.mean_dose
max_dose = prostate.max_dose


# Existing Head & Neck voxel-dose helpers.
DoseGeometry = head_neck.DoseGeometry
get_dose_geometry = head_neck.get_dose_geometry
global_hotspot_analysis = head_neck.global_hotspot_analysis
calculate_dvh_metrics = head_neck.calculate_dvh_metrics
dvh_note = head_neck.dvh_note


def prostate_metrics(dvh, *, dose_gy: float | None = None) -> dict[str, float]:
    """Return common finalized Prostate DVH values from a dicompyler DVH."""

    result = {
        "mean_gy": float(mean_dose(dvh)),
        "max_gy": float(max_dose(dvh)),
    }
    if dose_gy is not None:
        result["volume_at_dose_percent"] = float(
            volume_at_dose(dvh, dose_gy, relative=True)
        )
        result["volume_at_dose_cc"] = float(
            volume_at_dose(dvh, dose_gy, relative=False)
        )
    return result


def head_neck_metrics(*args, **kwargs):
    """Call the existing Head & Neck DVH metric engine unchanged."""

    return calculate_dvh_metrics(*args, **kwargs)
