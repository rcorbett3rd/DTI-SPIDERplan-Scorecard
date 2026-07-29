# DTI SPIDERplan Scorecard™

DTI SPIDERplan Scorecard™ is a local Streamlit plan-review application for
DICOM RT plan analysis. The current release candidate supports:

- Prostate
- Head & Neck
- Single-plan review
- Plan A versus Plan B comparison
- Target and OAR scoring
- Configurable score inclusion
- Configurable OAR assignment
- SPIDERplan snapshots and radar comparisons
- Interactive crosshair DVH review
- Detailed metric review
- CSV, JSON, and PDF-ready export workflows

## Canonical interface

The finalized Prostate application is the canonical interface. Head & Neck
contributes disease-specific clinical logic, including structure recognition,
prescription handling, target rules, OAR aliases, scoring metrics, and
constraints.

## Application structure

```text
app.py
core/
sites/
  prostate/
  head_neck/
ui/
tests/
```

The active site workflow modules remain:

```text
prostate_site.py
head_neck_site.py
```

Shared infrastructure is located under `core/`, `sites/`, and `ui/`.

## Installation

Create a Python environment and install the runtime dependencies:

```bash
pip install -r requirements.txt
```

For development and test execution:

```bash
pip install -r requirements-dev.txt
```

Launch the application:

```bash
streamlit run app.py
```

Run the complete test suite:

```bash
python -m pytest
```

Run the release validation:

```bash
python scripts/validate_release.py
```

## Clinical notice

This application is an R. A. Corbett III creation and property under Varian,
Siemens Healthineers. This tool is for research, development, and plan-review
support only and does not replace physician approval, physicist QA, chart
rounds, institutional policy, or clinical TPS review.

## Release status

Current version: `1.0.0-rc.1`

This is a release candidate and should undergo representative de-identified
Prostate and Head & Neck regression testing before any expanded use.
