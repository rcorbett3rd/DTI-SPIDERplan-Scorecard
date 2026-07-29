from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from prostate_dicom_engine import (
    calculate_dvh,
    classify_files,
    dose_at_volume_cc,
    dvh_arrays,
    fraction_count,
    is_target,
    mean_dose,
    modulation_factor,
    normalize_name,
    plan_label,
    prescription_dose_gy,
    structure_names,
    target_rx_from_name,
    treatment_beam_mus,
    volume_at_dose,
)
from prostate_reporting import make_pdf
from prostate_scoring_engine import (
    coverage_score,
    grade,
    hotspot_score,
    muf_score,
    oar_score,
    safe_mean,
    treatability,
    v105_score,
)


ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / "hn_scoring_config.json").read_text(encoding="utf-8"))
from hn_scorecard_engine import build_metric_table, final_grade as hn_final_grade, OAR_RULES
from core.homogeneity import (
    HI_DISPLAY_NAME,
    HI_GOAL,
    HI_TOOLTIP,
    format_homogeneity_details,
    homogeneity_index,
    score_homogeneity_index,
    should_score_target_homogeneity,
)


def _csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _result_metrics_df(result: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(result.get("metrics", []))


def _score_status(score: float) -> str:
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return "Not scored"
    if score >= 90:
        return "Achieved"
    if score >= 75:
        return "Marginal"
    return "Failed"


def _style_metrics(df: pd.DataFrame):
    def row_style(row: pd.Series) -> list[str]:
        status = str(row.get("Status", ""))
        score = row.get("Score", math.nan)
        if status == "Missing eval structure":
            color = "background-color:#00AEEF;color:#00111A;font-weight:700;"
        elif pd.isna(score):
            color = "background-color:#4b5563;color:white;"
        elif float(score) >= 90:
            color = "background-color:#dcfce7;color:#14532d;"
        elif float(score) >= 75:
            color = "background-color:#fef9c3;color:#713f12;"
        else:
            color = "background-color:#fee2e2;color:#7f1d1d;"
        return [color] * len(row)

    return df.style.apply(row_style, axis=1).format({"Score": "{:.1f}"})


@st.cache_data(show_spinner=False)
def analyze_uploaded(
    file_payloads: tuple[tuple[str, bytes], ...],
    structure_limit: int = 500,
) -> dict[str, Any]:
    """Analyze H&N DICOM with the same result contract used by the Prostate UI."""
    class Upload:
        def __init__(self, name: str, raw: bytes):
            import io
            self.name = name
            self._bio = io.BytesIO(raw)
        def seek(self, n: int):
            self._bio.seek(n)
        def read(self):
            return self._bio.read()

    def is_hn_target(name: str) -> bool:
        n = str(name).strip().lower()
        if n.startswith("z") or n.endswith("opti") or "ln" in re.split(r"[^a-z0-9]+", n):
            return False
        return any(k in n for k in ("ptv", "ctv", "gtv"))

    def assigned_rx(name: str) -> float | None:
        low = str(name).lower()
        four = re.findall(r"(?<!\d)(\d{4})(?!\d)", low)
        if four:
            value = float(four[-1]) / 100.0
            if 20 <= value <= 100:
                return value
        nums = re.findall(r"(?<!\d)(\d{2}(?:\.\d+)?)(?!\d)", low)
        vals = [float(x) for x in nums if 20 <= float(x) <= 100]
        if vals:
            return vals[-1]
        if any(token in low for token in ("high", "highest", "boost")):
            return 70.0
        if any(token in low for token in ("mid", "intermediate", "int")):
            return 63.0
        if any(token in low for token in ("low", "elective")):
            return 56.0
        return None

    def oar_group(name: str) -> str | None:
        norm = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
        for rule in OAR_RULES:
            if any(k in norm for k in rule["keys"]):
                label = str(rule["label"]).split(" D0.03cc")[0].split(" mean")[0].split(" V30Gy")[0].split(" D5%")[0]
                side = ""
                if re.search(r"(?:^|_)(l|lt|left)(?:_|$)", norm): side = " L"
                elif re.search(r"(?:^|_)(r|rt|right)(?:_|$)", norm): side = " R"
                return label + side
        return None

    uploads = [Upload(name, raw) for name, raw in file_payloads]
    files = classify_files(uploads)
    names = structure_names(files.structures)
    names = dict(list(names.items())[: max(1, int(structure_limit))])

    target_rxs = {name: assigned_rx(name) for name in names.values() if is_hn_target(name)}
    known = [float(x) for x in target_rxs.values() if x is not None]
    highest_rx = max(known) if known else prescription_dose_gy(files.plan)

    raw_rows=[]
    dvhs={}
    warnings=[]
    target_assignments=[]
    oar_candidates={}
    eval_rxs=set()
    lower_target_rxs={}

    for roi,name in names.items():
        low=name.lower()
        if low.startswith('z') or low.endswith('opti'):
            continue
        try:
            dvh=calculate_dvh(files,roi)
            doses,cum,total=dvh_arrays(dvh)
        except Exception as exc:
            warnings.append(f"{name}: DVH calculation failed — {exc}")
            continue
        if doses.size and cum.size and total>0:
            pct=np.clip(100.0*cum/total,0.0,100.0)
            dvhs[name]={"dose_gy":doses.tolist(),"volume_pct":pct.tolist(),"volume_cc":cum.tolist(),"total_volume_cc":float(total),"category":"TV" if is_hn_target(name) else "OAR"}

        rx=target_rxs.get(name)
        if is_hn_target(name):
            target_assignments.append({"Target":name,"Assigned Rx (Gy)":rx,"Assignment source":"Dose parsed from target name / H&N level","Score eligible":rx is not None})
            if 'eval' in low and rx is not None: eval_rxs.add(round(float(rx),2))
            elif rx is not None and highest_rx is not None and not math.isclose(float(rx),float(highest_rx),abs_tol=.05):
                lower_target_rxs.setdefault(round(float(rx),2),[]).append(name)
        else:
            grp=oar_group(name)
            if grp:
                oar_candidates.setdefault(grp,[]).append(name)

        d003=dose_at_volume_cc(dvh,min(.03,total)) if total>0 else math.nan
        d95=dose_at_volume_cc(dvh,.95*total) if total>0 else math.nan
        d98=dose_at_volume_cc(dvh,.98*total) if total>0 else math.nan
        d50=dose_at_volume_cc(dvh,.50*total) if total>0 else math.nan
        d5=dose_at_volume_cc(dvh,.05*total) if total>0 else math.nan
        d2=dose_at_volume_cc(dvh,.02*total) if total>0 else math.nan
        hi=homogeneity_index(d2,d50,d98)
        dmin=dose_at_volume_cc(dvh,.999*total) if total>0 else math.nan
        row={
            "structure":name,"status":"Calculated","approx_volume_cc":round(float(total),2),
            "Dmin_Gy":dmin,"Dmean_Gy":mean_dose(dvh),"Dmax_Gy":float(doses[-1]) if doses.size else math.nan,
            "D0.03cc_Gy":d003,"D98_Gy":d98,"D50_Gy":d50,"Homogeneity_Index_ICRU":hi,"D95_Gy":d95,"D5_Gy":d5,"D2_Gy":d2,
            "V30Gy_%":volume_at_dose(dvh,30.0,True),"assigned_rx_gy":rx if rx is not None else math.nan,
        }
        if rx is not None and rx>0:
            row.update({
                "D95_%Rx":100*d95/rx,"Dmin_%Rx":100*dmin/rx,"V100Rx_%":volume_at_dose(dvh,rx,True),
                "D0.03cc_%Rx":100*d003/rx,"D2_%Rx":100*d2/rx,"D50_%Rx":100*d50/rx,"D98_%Rx":100*d98/rx,"V95Rx_%":volume_at_dose(dvh,.95*rx,True),
                "V105Rx_%":volume_at_dose(dvh,1.05*rx,True),
            })
        raw_rows.append(row)

    raw_df=pd.DataFrame(raw_rows)
    metric_df=build_metric_table(raw_df,rx_dose_gy=highest_rx)
    rows=[]
    hi_rows: list[dict[str, Any]] = []
    for _,r in metric_df.iterrows():
        score=pd.to_numeric(pd.Series([r.get('score')]),errors='coerce').iloc[0]
        category=str(r.get('category','Not scored'))
        is_tv=is_hn_target(str(r.get('structure','')))
        role=str(r.get('scoring_role',''))
        # Display the clinically relevant value in the same compact Prostate table format.
        value=math.nan; value_text='Not scored'; metric=role or category; goal=str(r.get('notes',''))
        if is_tv and 'eval' in str(r.get('structure','')).lower():
            value=r.get('V105Rx_%',math.nan); value_text=f"{float(value):.1f}%" if pd.notna(value) else 'Not available'; metric='V105%'
        elif is_tv:
            value=r.get('V100Rx_%',math.nan); value_text=f"{float(value):.1f}%" if pd.notna(value) else 'Not available'; metric='Target Coverage / Dose Quality'
        else:
            notes_lower = str(r.get("notes", "")).lower()
            candidates = (
                ("D0.03cc_Gy", "D0.03cc", " Gy", "d0.03cc"),
                ("Dmean_Gy", "Mean", " Gy", "mean"),
                ("V30Gy_%", "V30Gy", "%", "v30gy"),
                ("D5_Gy", "D5%", " Gy", "d5%"),
            )
            for col, label, unit, note_token in candidates:
                candidate = pd.to_numeric(pd.Series([r.get(col)]), errors="coerce").iloc[0]
                if pd.notna(candidate) and note_token in notes_lower:
                    value = float(candidate)
                    value_text = f"{value:.2f}{unit}"
                    metric = label
                    break
            # Never display "Not scored" when a finite score exists.
            if pd.notna(score) and value_text == "Not scored":
                value_text = "Scored"
        grp=oar_group(str(r.get('structure',''))) if not is_tv else None
        rows.append({"structure":r.get('structure'),"metric":metric,"value":value,"value_text":value_text,"goal":goal,
                     "score":float(score) if pd.notna(score) else math.nan,"domain":category,"category":"TV" if is_tv else "OAR",
                     "oar_group":grp,"missing_eval":False})

    # Add one independently scored ICRU HI row per eligible target.
    # Highest-dose PTV is evaluated directly; lower-dose levels use matching PTV_eval.
    for raw in raw_rows:
        structure_name = str(raw.get("structure", ""))
        assigned = raw.get("assigned_rx_gy")
        if not should_score_target_homogeneity(structure_name, assigned, highest_rx):
            continue
        hi_value = raw.get("Homogeneity_Index_ICRU")
        evaluation = score_homogeneity_index(hi_value)
        d2_value = raw.get("D2_Gy")
        d50_value = raw.get("D50_Gy")
        d98_value = raw.get("D98_Gy")
        hi_rows.append({
            "structure": structure_name,
            "metric": HI_DISPLAY_NAME,
            "value": evaluation.value if evaluation.value is not None else math.nan,
            "value_text": format_homogeneity_details(d2_value, d50_value, d98_value, hi_value),
            "goal": HI_GOAL,
            "score": evaluation.score if evaluation.value is not None else math.nan,
            "domain": "Target Dose Quality",
            "category": "TV",
            "oar_group": None,
            "missing_eval": False,
            "notes": HI_TOOLTIP,
            "D2_Gy": d2_value,
            "D50_Gy": d50_value,
            "D98_Gy": d98_value,
        })

    missing=[]
    for rx,targets in sorted(lower_target_rxs.items(),reverse=True):
        if rx not in eval_rxs:
            rows.append({"structure":f"PTV_eval ({rx:g} Gy)","metric":"V105%","value":math.nan,"value_text":"Missing eval structure",
                         "goal":"≤5% ideal; ≤10% acceptable","score":math.nan,"domain":"PTV_eval Hotspot Review","category":"TV","missing_eval":True})
            missing.append(f"{rx:g} Gy eval target missing for {', '.join(targets)}")

    # Place HI rows together at the end of the clinical metrics, immediately before MUF.
    rows.extend(hi_rows)

    muf=modulation_factor(files.plan,highest_rx)
    ms=muf_score(muf['muf'])
    rows.append({"structure":"Plan","metric":"MUF","value":muf['muf'] if muf['muf'] is not None else math.nan,
                 "value_text":f"{muf['muf']:.2f}" if muf['muf'] is not None else 'Not evaluable',"goal":"≤5.00","score":ms,
                 "domain":"Plan Modulation","category":"PLAN","missing_eval":False})

    # H&N domain scores and weighted final grade.
    score_df=pd.DataFrame([{"category":r['domain'],"score":r['score']} for r in rows if pd.notna(r.get('score'))])
    if score_df.empty:
        domains={}; overall=0.0; letter='N/A'
    else:
        ddf=score_df.groupby('category',as_index=False)['score'].mean().rename(columns={'category':'domain','score':'domain_score'})
        g=hn_final_grade(ddf); overall=float(g['score']); letter=str(g['grade']); domains=dict(zip(ddf['domain'],ddf['domain_score']))

    fractions=fraction_count(files.plan); total_mu=float(sum(treatment_beam_mus(files.plan))); plan_rx=prescription_dose_gy(files.plan)
    plan_summary=[
        {"Item":"Plan label","Value":str(plan_label(files.plan))},
        {"Item":"Plan prescription","Value":f"{plan_rx:.2f} Gy" if plan_rx else "Not found"},
        {"Item":"Fractions planned","Value":str(fractions) if fractions else "Not found"},
        {"Item":"Highest dose/fraction","Value":f"{muf['fraction_dose_cgy']:.1f} cGy" if muf['fraction_dose_cgy'] else "Not found"},
        {"Item":"Total treatment MU/fraction","Value":f"{total_mu:.1f} MU"},
        {"Item":"MUF","Value":f"{muf['muf']:.2f}" if muf['muf'] is not None else "Not evaluable"},
        {"Item":"Structures detected","Value":str(len(names))},
        {"Item":"DVHs calculated","Value":str(len(dvhs))},
    ]
    return {"label":plan_label(files.plan),"metrics":rows,"domains":domains,"overall":overall,"grade":letter,
            "treatability":treatability(overall),"dvhs":dvhs,"muf":muf,"structures":list(names.values()),
            "target_assignments":target_assignments,"plan_summary":plan_summary,"warnings":warnings,
            "oar_candidates":oar_candidates,"missing_eval":bool(missing),"missing_eval_details":missing}


def _default_oar_candidate(group: str, candidates: list[str]) -> str:
    """Prefer the base OAR contour, while allowing derived OAR-minus-target options."""
    if not candidates:
        return ""
    group_norm = normalize_name(group)
    exact = [name for name in candidates if normalize_name(name) == group_norm]
    if exact:
        return exact[0]

    # Prefer the shortest recognized alias without a target suffix.
    target_tokens = ("ptv", "ctv", "gtv", "itv", "tv")
    non_subtracted = [
        name for name in candidates
        if not any(token in name.lower() for token in target_tokens)
    ]
    pool = non_subtracted or candidates
    return sorted(pool, key=lambda value: (len(value), value.lower()))[0]


def apply_oar_assignments(
    result: dict[str, Any],
    assignments: dict[str, str],
) -> dict[str, Any]:
    """Keep only the user-assigned structure for each configured OAR group."""
    filtered = dict(result)
    kept_rows: list[dict[str, Any]] = []

    for row in result["metrics"]:
        if row.get("category") != "OAR":
            kept_rows.append(row)
            continue

        group = row.get("oar_group")
        selected = assignments.get(group)
        if selected is None or row.get("structure") == selected:
            kept_rows.append(row)

    filtered["metrics"] = kept_rows
    filtered["oar_assignments"] = assignments
    return filtered


def apply_score_inclusions(
    result: dict[str, Any],
    included_structures: set[str],
) -> dict[str, Any]:
    filtered = dict(result)
    rows = [
        row
        for row in result["metrics"]
        if row["structure"] == "Plan" or row["structure"] in included_structures
    ]

    domains: dict[str, list[float]] = {}
    for row in rows:
        score = row.get("score")
        if score is None or pd.isna(score):
            continue
        domains.setdefault(row["domain"], []).append(float(score))

    filtered["metrics"] = rows
    filtered["domains"] = {
        domain: safe_mean(scores) for domain, scores in domains.items() if scores
    }
    filtered["overall"] = safe_mean(list(filtered["domains"].values()))
    filtered["grade"] = grade(filtered["overall"])
    filtered["treatability"] = treatability(filtered["overall"])
    filtered["missing_eval"] = result.get("missing_eval", False)
    filtered["missing_eval_details"] = result.get("missing_eval_details", [])
    return filtered


def radar_figure(
    results: list[dict[str, Any]],
    title: str,
    category_filter: str | None = None,
) -> go.Figure:
    domain_union: list[str] = []
    for result in results:
        for domain in result["domains"]:
            if category_filter == "TV" and not domain.startswith("Target"):
                continue
            if category_filter == "OAR" and (
                domain.startswith("Target") or domain == "Plan Modulation"
            ):
                continue
            if domain not in domain_union:
                domain_union.append(domain)

    fig = go.Figure()
    plan_colors = ["#2563EB", "#F97316", "#16A34A", "#A855F7"]
    for index, result in enumerate(results):
        values = [result["domains"].get(domain, 0) for domain in domain_union]
        if not values:
            continue
        color = plan_colors[index % len(plan_colors)]
        fig.add_trace(
            go.Scatterpolar(
                r=values + values[:1],
                theta=domain_union + domain_union[:1],
                fill="toself",
                name=result["display_name"],
                line=dict(color=color, width=3),
                marker=dict(color=color),
                opacity=0.72,
            )
        )

    fig.update_layout(
        title=title,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickmode="array",
                tickvals=list(range(0, 101, 10)),
                ticktext=[str(v) for v in range(0, 101, 10)],
            )
        ),
        height=560,
        legend=dict(orientation="h"),
        margin=dict(l=60, r=60, t=80, b=50),
    )
    return fig


def structure_radar_figure(
    results: list[dict[str, Any]],
    category: str,
    title: str,
) -> go.Figure | None:
    structure_union: list[str] = []
    value_maps: list[dict[str, float]] = []
    over_100_maps: list[set[str]] = []

    for result in results:
        df = _result_metrics_df(result)
        if category == "TV":
            # H&N target rows use the compact metric label
            # "Target Coverage / Dose Quality" rather than a V100%-prefixed label.
            # Include every scored, non-missing target row and plot its actual V100Rx value.
            df = df[
                (df["category"] == "TV")
                & (~df["missing_eval"].fillna(False).astype(bool))
                & (~df["structure"].astype(str).str.contains("eval", case=False, na=False))
                & pd.to_numeric(df["value"], errors="coerce").notna()
            ].copy()
            grouped = (
                df.assign(value_numeric=pd.to_numeric(df["value"], errors="coerce"))
                .groupby("structure")["value_numeric"]
                .mean()
                .to_dict()
            )
        else:
            df = df[
                (df["category"] == "OAR")
                & pd.to_numeric(df["score"], errors="coerce").notna()
            ].copy()
            grouped = df.groupby("structure")["score"].mean().to_dict()

        value_maps.append({key: float(value) for key, value in grouped.items()})
        over_100_maps.append(
            {key for key, value in grouped.items() if float(value) > 100.0}
        )
        for structure in grouped:
            if structure not in structure_union:
                structure_union.append(structure)

    if not structure_union:
        return None

    fig = go.Figure()
    plan_colors = ["#2563EB", "#F97316", "#16A34A", "#A855F7"]

    for index, (result, value_map, over_100) in enumerate(
        zip(results, value_maps, over_100_maps)
    ):
        raw_values = [float(value_map.get(structure, 0)) for structure in structure_union]
        plotted_values = [min(value, 100.0) for value in raw_values]
        hover_text = [
            (
                f"{structure}: {raw:.2f}%* (capped at 100% for display)"
                if structure in over_100
                else f"{structure}: {raw:.2f}%"
            )
            if category == "TV"
            else f"{structure}: score {raw:.1f}"
            for structure, raw in zip(structure_union, raw_values)
        ]
        color = plan_colors[index % len(plan_colors)]
        fig.add_trace(
            go.Scatterpolar(
                r=plotted_values + plotted_values[:1],
                theta=structure_union + structure_union[:1],
                fill="toself",
                name=result["display_name"],
                line=dict(color=color, width=3),
                marker=dict(
                    color=color,
                    size=[
                        12 if structure in over_100 else 7
                        for structure in structure_union
                    ] + [12 if structure_union[0] in over_100 else 7],
                    symbol=[
                        "asterisk" if structure in over_100 else "circle"
                        for structure in structure_union
                    ] + [
                        "asterisk" if structure_union[0] in over_100 else "circle"
                    ],
                ),
                text=hover_text + hover_text[:1],
                hovertemplate="%{text}<extra></extra>",
                opacity=0.72,
            )
        )

    if category == "TV":
        radial_axis = dict(
            visible=True,
            range=[70, 100],
            tickmode="array",
            tickvals=list(range(70, 101, 5)),
            ticktext=[str(v) for v in range(70, 101, 5)],
        )
        annotation = (
            "* Asterisk indicates a raw coverage value above 100%; "
            "the plotted point is capped at 100."
        )
    else:
        radial_axis = dict(
            visible=True,
            range=[0, 100],
            tickmode="array",
            tickvals=list(range(0, 101, 10)),
            ticktext=[str(v) for v in range(0, 101, 10)],
        )
        annotation = ""

    fig.update_layout(
        title=title,
        polar=dict(radialaxis=radial_axis),
        height=max(600, 40 * len(structure_union)),
        legend=dict(orientation="h"),
        margin=dict(l=90, r=90, t=100, b=70),
        annotations=(
            [
                dict(
                    text=annotation,
                    x=0.5,
                    y=-0.10,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=12),
                )
            ]
            if annotation
            else []
        ),
    )
    return fig


def dvh_figure(
    results: list[dict[str, Any]],
    selected_structures: list[str],
    volume_mode: str,
    dose_units: str,
) -> go.Figure:
    fig = go.Figure()
    dose_scale = 100.0 if dose_units == "cGy" else 1.0
    y_key = "volume_pct" if volume_mode == "Relative (%)" else "volume_cc"

    for plan_index, result in enumerate(results):
        dash = "solid" if plan_index == 0 else "dash"
        for structure in selected_structures:
            arr = result["dvhs"].get(structure)
            if not arr:
                continue
            fig.add_trace(
                go.Scatter(
                    x=np.asarray(arr["dose_gy"], dtype=float) * dose_scale,
                    y=arr[y_key],
                    mode="lines",
                    name=f"{result['display_name']} – {structure}",
                    legendgroup=structure,
                    line=dict(width=2.5, dash=dash),
                    hovertemplate=(
                        f"<b>{result['display_name']} – {structure}</b><br>"
                        f"Dose: %{{x:.2f}} {dose_units}<br>"
                        + (
                            "Volume: %{y:.2f}%<extra></extra>"
                            if volume_mode == "Relative (%)"
                            else "Volume: %{y:.2f} cc<extra></extra>"
                        )
                    ),
                )
            )

    y_title = "Volume (%)" if volume_mode == "Relative (%)" else "Volume (cc)"
    fig.update_layout(
        title="Interactive Comparison DVH",
        xaxis_title=f"Dose ({dose_units})",
        yaxis_title=y_title,
        xaxis=dict(
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikedash="dot",
            spikethickness=1,
        ),
        yaxis=dict(
            range=[0, 105] if volume_mode == "Relative (%)" else None,
            showspikes=True,
            spikemode="across",
            spikesnap="cursor",
            spikedash="dot",
            spikethickness=1,
        ),
        height=720,
        hovermode="closest",
        legend=dict(groupclick="toggleitem"),
        margin=dict(l=60, r=30, t=80, b=60),
    )
    return fig


def dvh_long_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for structure, arr in result["dvhs"].items():
        for dose, pct, cc in zip(
            arr["dose_gy"], arr["volume_pct"], arr["volume_cc"]
        ):
            records.append(
                {
                    "Plan": result["display_name"],
                    "Structure": structure,
                    "Dose_Gy": dose,
                    "Volume_percent": pct,
                    "Volume_cc": cc,
                }
            )
    return pd.DataFrame(records)


def scorecard_snapshot(results: list[dict[str, Any]]) -> None:
    st.header("SPIDERplan Scorecard Snapshot")

    columns = st.columns(len(results))
    winner = None
    if len(results) == 2:
        winner = 0 if results[0]["overall"] >= results[1]["overall"] else 1

    for index, (column, result) in enumerate(zip(columns, results)):
        best = winner == index
        if best:
            style = (
                "background:#ecfdf5;color:#0f172a;border:4px solid #22c55e;"
            )
            check = " ✅"
        elif index == 0:
            style = "background:#dbeafe;color:#0f172a;border:2px solid #2563eb;"
            check = ""
        else:
            style = "background:#ffedd5;color:#0f172a;border:2px solid #f97316;"
            check = ""

        with column:
            st.markdown(
                f"""
                <div style="padding:1.2rem;border-radius:.8rem;min-height:280px;{style}">
                    <h3 style="color:#0f172a;">{result['display_name']}{check}</h3>
                    <h1 style="color:#0f172a;font-size:2.5rem;">{result['overall']:.1f}{
                        '<span style="color:#00AEEF;">*</span>'
                        if result.get('missing_eval')
                        else ''
                    }</h1>
                    <h2 style="color:#0f172a;">Grade {result['grade']}</h2>
                    <h3 style="color:#0f172a;">{result['treatability']}</h3>
                    <p style="color:#0f172a;"><b>MUF:</b> {
                        f"{result['muf']['muf']:.2f}"
                        if result['muf']['muf'] is not None
                        else "Not evaluable"
                    }</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if result.get("missing_eval"):
                st.markdown(
                    '<span style="color:#00AEEF;font-weight:700;">*</span> '
                    'V105% per PTV could not be evaluated due to missing eval structure(s).',
                    unsafe_allow_html=True,
                )
                with st.expander("Missing V105% eval details", expanded=False):
                    for detail in result.get("missing_eval_details", []):
                        st.write(f"- {detail}")

    st.plotly_chart(
        radar_figure(results, "Overall SPIDERplan comparison"),
        width="stretch",
    )


# Sidebar
with st.sidebar:
    st.caption("Sidebar")
    sidebar_section = st.radio(
        "Navigation",
        ["Options", "Plan scores", "Save as PDF"],
        label_visibility="collapsed",
        key="sidebar_section",
    )

    st.header("Options")
    structure_limit = st.number_input(
        "Structure calculation limit",
        min_value=20,
        max_value=500,
        value=500,
        step=10,
        help="Maximum structures processed. The default includes up to 500 contours so H&N targets and OARs are not omitted.",
    )
    require_rx = st.checkbox(
        "Require Rx for scored targets",
        value=True,
        help="Targets without a recognizable prescription remain visible but unscored.",
    )
    st.divider()
    st.caption("Upload Plan B to activate comparison mode.")


st.title("DTI – HN SPIDERplan Scorecard™")
st.caption(
    "Optional single-plan or two-plan comparison with full plan processing, "
    "SPIDER graph scorecards, detailed review, export, and interactive DVH."
)

with st.expander("Clinical / security disclaimer", expanded=False):
    st.write(
        "This application is an R. A. Corbett III creation and property under "
        "Varian, Siemens Healthineers. This tool is for research, development, "
        "and plan-review support only and does not replace physician approval, "
        "physicist QA, chart rounds, institutional policy, or clinical TPS review."
    )

col_a, col_b = st.columns(2)
with col_a:
    files_a = st.file_uploader(
        "Plan A: Upload RP + RS + RD files",
        type=["dcm", "dicom", "DCM"],
        accept_multiple_files=True,
        key="plan_a_upload",
    )
with col_b:
    files_b = st.file_uploader(
        "Plan B: Upload RP + RS + RD files (optional comparison)",
        type=["dcm", "dicom", "DCM"],
        accept_multiple_files=True,
        key="plan_b_upload",
    )

if not files_a:
    st.info(
        "Upload Plan A RP + RS + RD files to generate the scorecard. "
        "Upload Plan B to compare two plans side by side."
    )
    st.stop()

raw_results: list[dict[str, Any]] = []
upload_sets = [("Plan A", files_a)]
if files_b:
    upload_sets.append(("Plan B", files_b))

for display_name, uploads in upload_sets:
    payload = tuple((uploaded.name, uploaded.getvalue()) for uploaded in uploads)
    try:
        with st.spinner(f"Processing {display_name} DICOM and calculating DVHs..."):
            result = analyze_uploaded(payload, int(structure_limit))
            result["display_name"] = display_name
            raw_results.append(result)
    except Exception as exc:
        st.error(f"{display_name} could not be analyzed: {exc}")

if not raw_results:
    st.stop()

st.markdown("---")
st.header("Plan Processing")
st.caption(
    "Review the prescription assignments and choose which structures contribute "
    "to each plan's score. Unchecked structures remain available in the DVH."
)

processed_results: list[dict[str, Any]] = []
processing_columns = st.columns(len(raw_results))

for index, (column, result) in enumerate(zip(processing_columns, raw_results)):
    with column:
        with st.expander(f"{result['display_name']} Prescription Assignments", expanded=True):
            rx_df = pd.DataFrame(result["target_assignments"])
            if rx_df.empty:
                st.info("No target structures were recognized.")
            else:
                st.dataframe(rx_df, width="stretch", hide_index=True)

        with st.expander(f"{result['display_name']} OAR Structure Assignment", expanded=True):
            st.caption(
                "The base OAR is selected automatically. Choose an OAR-minus-target "
                "structure when clinically appropriate, such as Bladder-CTV."
            )
            assignments: dict[str, str] = {}
            for group, candidates in sorted(result.get("oar_candidates", {}).items()):
                if not candidates:
                    continue
                default_name = _default_oar_candidate(group, candidates)
                default_index = candidates.index(default_name) if default_name in candidates else 0
                assignments[group] = st.selectbox(
                    group,
                    options=candidates,
                    index=default_index,
                    key=f"oar_assignment_{index}_{normalize_name(group)}",
                    help=(
                        f"Select the structure used for all configured {group} scoring metrics."
                    ),
                )

            assigned_result = apply_oar_assignments(result, assignments)

        with st.expander(f"{result['display_name']} Score Inclusion", expanded=True):
            metric_df = _result_metrics_df(assigned_result)
            candidates = sorted(
                structure
                for structure in metric_df["structure"].dropna().unique().tolist()
                if structure != "Plan"
            )
            checklist = pd.DataFrame(
                {
                    "Include": [True] * len(candidates),
                    "Structure": candidates,
                    "Category": [
                        (
                            metric_df.loc[
                                metric_df["structure"] == structure, "category"
                            ].iloc[0]
                            if not metric_df.loc[
                                metric_df["structure"] == structure
                            ].empty
                            else ""
                        )
                        for structure in candidates
                    ],
                }
            )
            edited = st.data_editor(
                checklist,
                hide_index=True,
                width="stretch",
                disabled=["Structure", "Category"],
                key=f"score_inclusion_{index}",
            )
            included = set(
                edited.loc[edited["Include"] == True, "Structure"].astype(str).tolist()
            )
            filtered = apply_score_inclusions(assigned_result, included)
            filtered["display_name"] = result["display_name"]
            processed_results.append(filtered)

results = processed_results

with st.sidebar:
    st.markdown("---")
    st.subheader("Current scores")
    for result in results:
        st.metric(
            f"{result['display_name']} score",
            f"{result['overall']:.1f}",
        )
        st.caption(
            f"Grade {result['grade']} · {result['treatability']}"
        )

st.markdown("---")
scorecard_snapshot(results)

if len(results) == 2:
    st.markdown("---")
    st.header("Comparison SPIDERplan Graphs")
    target_tab, oar_tab = st.tabs(["Target volumes", "OARs"])

    with target_tab:
        target_fig = structure_radar_figure(
            results, "TV", "Target volumes comparison"
        )
        if target_fig is None:
            st.info("No scored target-volume rows were available.")
        else:
            st.plotly_chart(target_fig, width="stretch")

    with oar_tab:
        oar_fig = structure_radar_figure(results, "OAR", "OAR comparison")
        if oar_fig is None:
            st.info("No scored OAR rows were available.")
        else:
            st.plotly_chart(oar_fig, width="stretch")

st.markdown("---")
st.header("Final Metrics Table")
st.caption("Green = achieved, yellow = marginal, red = failed, gray = not scored.")

metric_tabs = st.tabs(
    [f"{result['display_name']} metrics" for result in results]
    + (["Side-by-side scores"] if len(results) == 2 else [])
)

for tab, result in zip(metric_tabs[: len(results)], results):
    with tab:
        df = _result_metrics_df(result)
        display = df[
            [
                "structure",
                "metric",
                "value_text",
                "goal",
                "score",
                "domain",
                "category",
                "missing_eval",
            ]
        ].copy()
        display["status"] = display.apply(
            lambda row: "Missing eval structure"
            if row.get("missing_eval", False) is True
            else _score_status(row.get("score")),
            axis=1,
        )
        display.columns = [
            "Structure",
            "Metric",
            "Result",
            "Goal",
            "Score",
            "Domain",
            "Category",
            "Missing Eval",
            "Status",
        ]
        st.dataframe(
            _style_metrics(display),
            width="stretch",
            hide_index=True,
        )

if len(results) == 2:
    with metric_tabs[-1]:
        a = _result_metrics_df(results[0]).copy()
        b = _result_metrics_df(results[1]).copy()
        for df, suffix in ((a, "A"), (b, "B")):
            df["Match"] = (
                df["structure"].astype(str)
                + " | "
                + df["metric"].astype(str)
            )
            df.rename(
                columns={
                    "value_text": f"Result {suffix}",
                    "score": f"Score {suffix}",
                },
                inplace=True,
            )
        comparison = pd.merge(
            a[["Match", "structure", "metric", "goal", "Result A", "Score A"]],
            b[["Match", "Result B", "Score B"]],
            on="Match",
            how="outer",
        ).drop(columns=["Match"])
        comparison.columns = [
            "Structure",
            "Metric",
            "Goal",
            "Plan A Result",
            "Plan A Score",
            "Plan B Result",
            "Plan B Score",
        ]
        st.dataframe(comparison, width="stretch", hide_index=True)

st.markdown("---")
st.header("Interactive Eclipse-Style Comparison DVH")
st.caption(
    "Use the controls below to display relative or absolute cumulative DVHs. "
    "Zoom, pan, hover, and click legend items to isolate individual curves."
)

all_structures: list[str] = []
for result in results:
    for structure in result["dvhs"]:
        if structure not in all_structures:
            all_structures.append(structure)

default_structures = [
    structure
    for structure in all_structures
    if any(
        token in structure.lower()
        for token in ["ptv", "ctv", "rect", "bladder", "bowel", "fem"]
    )
][:12]
if not default_structures:
    default_structures = all_structures[:10]

control_1, control_2 = st.columns(2)
with control_1:
    volume_mode = st.radio(
        "Volume display",
        ["Relative (%)", "Absolute (cc)"],
        horizontal=True,
    )
with control_2:
    dose_units = st.radio(
        "Dose display",
        ["Gy", "cGy"],
        horizontal=True,
    )

selected_structures = st.multiselect(
    "Structures shown on the DVH",
    options=all_structures,
    default=default_structures,
)

if selected_structures:
    st.plotly_chart(
        dvh_figure(results, selected_structures, volume_mode, dose_units),
        width="stretch",
        config={
            "displaylogo": False,
            "scrollZoom": True,
            "modeBarButtonsToAdd": ["drawline", "eraseshape"],
        },
    )
else:
    st.info("Choose at least one structure to display the DVH.")

st.markdown("---")
st.header("Detailed Review")

review_tabs = st.tabs([result["display_name"] for result in results])
for tab, result in zip(review_tabs, results):
    with tab:
        with st.expander("Target Rx assignment", expanded=False):
            rx_df = pd.DataFrame(result["target_assignments"])
            st.dataframe(rx_df, width="stretch", hide_index=True)

        with st.expander("Plan Summary", expanded=False):
            st.dataframe(
                pd.DataFrame(result["plan_summary"]).astype(str),
                width="stretch",
                hide_index=True,
            )
            if result.get("oar_assignments"):
                st.markdown("**OAR structures used for scoring**")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {"Configured OAR": group, "Assigned structure": structure}
                            for group, structure in result["oar_assignments"].items()
                        ]
                    ),
                    width="stretch",
                    hide_index=True,
                )

        with st.expander("DVH / Dose Metrics", expanded=False):
            metric_df = _result_metrics_df(result)
            dose_metrics = metric_df[
                [
                    "structure",
                    "metric",
                    "value_text",
                    "goal",
                    "score",
                    "domain",
                    "category",
                ]
            ].copy()
            dose_metrics.columns = [
                "Structure",
                "Metric",
                "Result",
                "Goal",
                "Score",
                "Domain",
                "Category",
            ]
            st.dataframe(dose_metrics, width="stretch", hide_index=True)

        with st.expander("DVH calculation Warnings", expanded=False):
            if result["warnings"]:
                for warning in result["warnings"]:
                    st.write(f"- {warning}")
            else:
                st.success("No DVH calculation warnings were generated.")

st.markdown("---")
st.header("Export options")

export_columns = st.columns(3)
with export_columns[0]:
    for index, result in enumerate(results):
        st.download_button(
            f"Download {result['display_name']} PDF report",
            make_pdf(result),
            file_name=f"{result['display_name'].replace(' ', '_')}_Prostate_SPIDERplan.pdf",
            mime="application/pdf",
            key=f"pdf_{index}",
            width="stretch",
        )

with export_columns[1]:
    for index, result in enumerate(results):
        st.download_button(
            f"Download {result['display_name']} Scorecard CSV",
            _csv_bytes(_result_metrics_df(result)),
            file_name=f"{result['display_name'].replace(' ', '_')}_scorecard.csv",
            mime="text/csv",
            key=f"score_csv_{index}",
            width="stretch",
        )

with export_columns[2]:
    for index, result in enumerate(results):
        st.download_button(
            f"Download {result['display_name']} DVH CSV",
            _csv_bytes(dvh_long_dataframe(result)),
            file_name=f"{result['display_name'].replace(' ', '_')}_dvh.csv",
            mime="text/csv",
            key=f"dvh_csv_{index}",
            width="stretch",
        )

st.markdown("---")
st.caption(
    "This application is an R. A. Corbett III creation and property under "
    "Varian, Siemens Healthineers. This tool is for research, development, "
    "and plan-review support only and does not replace physician approval, "
    "physicist QA, chart rounds, institutional policy, or clinical TPS review."
)
