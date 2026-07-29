"""Current Head & Neck OAR metric definitions.

These values are transcribed from the existing `hn_scorecard_engine.py` OAR_RULES
table. The existing H&N scorecard engine remains the scoring source of truth
until the shared metric evaluator is activated in a later build.
"""

from __future__ import annotations

from sites.base import MetricDefinition, StructureDefinition


def _metric(
    metric_type: str,
    *,
    preferred: float,
    acceptable: float | None = None,
    ideal: float | None = None,
    label: str,
) -> MetricDefinition:
    return MetricDefinition(
        metric_type=metric_type,
        limit=preferred,
        preferred=preferred,
        acceptable=acceptable,
        ideal=ideal,
        label=label,
        units="%" if metric_type.endswith("_%") else "Gy",
    )


STRUCTURES: tuple[StructureDefinition, ...] = (
    StructureDefinition(
        "SpinalCord PRV",
        ("spinalcord_prv", "cord_prv", "spinal cord prv"),
        (_metric("D0.03cc_Gy", preferred=50, ideal=45, label="SpinalCord_PRV D0.03cc"),),
    ),
    StructureDefinition(
        "SpinalCord",
        ("spinalcord", "spinal cord", "cord"),
        (_metric("D0.03cc_Gy", preferred=45, ideal=40, label="SpinalCord D0.03cc"),),
    ),
    StructureDefinition(
        "Brainstem PRV",
        ("brainstem_prv", "brain stem prv"),
        (_metric("D0.03cc_Gy", preferred=58, acceptable=60, label="Brainstem_PRV D0.03cc"),),
    ),
    StructureDefinition(
        "Brainstem",
        ("brainstem", "brain stem"),
        (_metric("D0.03cc_Gy", preferred=54, acceptable=58, label="Brainstem D0.03cc"),),
    ),
    StructureDefinition(
        "Optic PRV",
        ("opticnrv_prv", "optic_chiasm_prv", "opticchiasm_prv", "optic nerve prv"),
        (_metric("D0.03cc_Gy", preferred=54, ideal=50, label="Optic PRV D0.03cc"),),
    ),
    StructureDefinition(
        "Optic Pathway",
        ("opticnrv", "optic nerve", "optic_chiasm", "opticchiasm", "chiasm"),
        (_metric("D0.03cc_Gy", preferred=50, acceptable=54, label="Optic/chiasm D0.03cc"),),
    ),
    StructureDefinition(
        "Retina",
        ("retina",),
        (_metric("D0.03cc_Gy", preferred=45, ideal=40, label="Retina D0.03cc"),),
    ),
    StructureDefinition(
        "Lens",
        ("lens",),
        (_metric("D0.03cc_Gy", preferred=10, ideal=5, label="Lens D0.03cc"),),
    ),
    StructureDefinition(
        "Brain",
        ("brain",),
        (_metric("D0.03cc_Gy", preferred=60, ideal=54, label="Brain D0.03cc"),),
    ),
    StructureDefinition(
        "Brachial Plexus",
        ("brachialplex", "brachial plexus"),
        (_metric("D0.03cc_Gy", preferred=66, ideal=60, label="Brachial plexus D0.03cc"),),
    ),
    StructureDefinition(
        "Parotid",
        ("parotid",),
        (
            _metric("Dmean_Gy", preferred=26, ideal=20, label="Parotid mean"),
            _metric("V30Gy_%", preferred=50, ideal=40, label="Parotid V30Gy"),
        ),
    ),
    StructureDefinition(
        "Submandibular Gland",
        ("glnd_submand", "submand", "submandibular"),
        (_metric("Dmean_Gy", preferred=39, ideal=30, label="Submandibular mean"),),
    ),
    StructureDefinition(
        "Cochlea",
        ("cochlea",),
        (
            _metric("Dmean_Gy", preferred=35, acceptable=45, label="Cochlea mean"),
            _metric("D5_Gy", preferred=55, ideal=50, label="Cochlea D5%"),
        ),
    ),
    StructureDefinition(
        "Constrictor",
        ("constrict",),
        (_metric("Dmean_Gy", preferred=55, ideal=45, label="Constrictor mean"),),
    ),
    StructureDefinition(
        "Esophagus",
        ("esophagus",),
        (_metric("Dmean_Gy", preferred=35, ideal=28, label="Esophagus mean"),),
    ),
    StructureDefinition(
        "Lips",
        ("lips",),
        (_metric("Dmean_Gy", preferred=20, ideal=15, label="Lips mean"),),
    ),
    StructureDefinition(
        "Oral Cavity",
        ("cavity_oral", "oralcavity", "oral_cavity", "oral cavity"),
        (_metric("Dmean_Gy", preferred=35, ideal=28, label="Oral cavity mean"),),
    ),
    StructureDefinition(
        "Mandible",
        ("bone_mandible", "mandible"),
        (_metric("D0.03cc_Gy", preferred=71, ideal=66, label="Mandible D0.03cc"),),
    ),
    StructureDefinition(
        "Eye",
        ("eyes", "eye"),
        (_metric("D0.03cc_Gy", preferred=45, ideal=40, label="Eyes D0.03cc"),),
    ),
    StructureDefinition(
        "Mouth Floor",
        ("mouth_floor", "floorofmouth", "floor of mouth"),
        (_metric("Dmean_Gy", preferred=40, ideal=32, label="Mouth floor mean"),),
    ),
    StructureDefinition(
        "Larynx",
        ("larynx",),
        (_metric("Dmean_Gy", preferred=35, ideal=28, label="Larynx mean"),),
    ),
    StructureDefinition(
        "Temporal Lobe",
        ("lobe_temporal", "temporal"),
        (_metric("D0.03cc_Gy", preferred=70, ideal=65, label="Temporal lobe D0.03cc"),),
    ),
)
