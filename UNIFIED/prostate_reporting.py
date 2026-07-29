from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def make_pdf(plan_result: dict[str, Any]) -> bytes:
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph("DTI – Prostate SPIDERplan Scorecard", styles["Title"]), Spacer(1, 0.15 * inch)]
    story.append(Paragraph(f"Plan: {plan_result['label']}", styles["Heading2"]))
    story.append(Paragraph(f"Overall score: {plan_result['overall']:.1f} ({plan_result['grade']})", styles["BodyText"]))
    story.append(Paragraph(f"Treatability: {plan_result['treatability']}", styles["BodyText"]))
    story.append(Spacer(1, 0.15 * inch))
    rows = [["Domain", "Score"]] + [[k, f"{v:.1f}"] for k, v in plan_result["domains"].items()]
    table = Table(rows, colWidths=[3.5 * inch, 1.25 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))
    story += [table, Spacer(1, 0.2 * inch)]
    metric_rows = [["Structure", "Metric", "Value", "Goal", "Score"]]
    for row in plan_result["metrics"]:
        metric_rows.append([row["structure"], row["metric"], row["value_text"], row["goal"], f"{row['score']:.1f}" if row["score"] == row["score"] else "N/E"])
    table2 = Table(metric_rows, repeatRows=1, colWidths=[1.4*inch, 1.25*inch, 1.0*inch, 1.35*inch, 0.65*inch])
    table2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story += [table2, Spacer(1, 0.2 * inch)]
    story.append(Paragraph("Research/development and plan-review support only. This report does not replace physician approval, physicist QA, chart rounds, institutional policy, or clinical TPS review.", styles["Italic"]))
    doc.build(story)
    return out.getvalue()
