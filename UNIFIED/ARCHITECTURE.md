# DTI SPIDERplan Scorecard Architecture

## Purpose

DTI SPIDERplan Scorecard is a Streamlit application for research, development, and plan-review support. It evaluates uploaded RTPLAN, RTSTRUCT, and RTDOSE DICOM objects for Prostate and Head & Neck treatment sites, produces scored clinical metrics, compares Plan A with Plan B, displays SPIDER charts and DVHs, and exports review results.

## Application flow

1. `app.py` launches the application and selects the treatment site.
2. The active site module (`prostate_site.py` or `head_neck_site.py`) receives the uploaded DICOM files.
3. The DICOM/DVH engines identify RT objects, calculate cumulative DVHs, and sample dose-volume values.
4. Site and shared scoring functions convert the sampled values into metric rows.
5. OAR assignments and score-inclusion selections determine which rows contribute to the final score.
6. Domain scores, the overall score, grade, and treatability classification are calculated.
7. Shared UI, comparison, chart, and export components render the results.

## Primary production modules

- `app.py`: unified launcher and site selection.
- `prostate_site.py`: active Prostate analysis and presentation workflow.
- `head_neck_site.py`: active Head & Neck analysis and presentation workflow.
- `prostate_dicom_engine.py`: shared DICOM parsing and DVH helpers used by the active site workflows.
- `hn_dvh_engine.py`: Head & Neck DVH sampling support.
- `prostate_scoring_engine.py`: Prostate scoring functions.
- `hn_scorecard_engine.py`: Head & Neck metric construction and grading.
- `core/`: shared contracts, scoring utilities, runtime orchestration, comparison, exports, and future unified clinical pipeline.
- `sites/`: disease-site profiles and adapters used by the unified architecture.
- `ui/`: reusable Streamlit presentation components.

## Metric-row contract

Every metric shown in the Final Metrics Table should contain these fields:

- `structure`
- `metric`
- `value`
- `value_text`
- `goal`
- `score`
- `domain`
- `category`
- `missing_eval`

A row with a finite numeric score is considered scored. Its `value_text` must never say `Not scored`. Missing or unavailable rows must use a nonnumeric score and a clear explanation such as `Not available`, `Not determined`, or `Missing eval structure`.

## Homogeneity Index

Both treatment sites use the ICRU Homogeneity Index:

`HI = (D2% - D98%) / D50%`

The ratio is dimensionless. D2, D50, and D98 may be expressed in Gy or percent prescription as long as all three use the same units.

Scoring:

- HI <= 0.10: 100
- HI 0.10-0.15: linear 100 to 90
- HI 0.15-0.20: linear 90 to 50
- HI > 0.20: 0

SIB target selection:

- Score the highest-dose PTV directly.
- Score lower-dose levels on the matching `_eval` PTV.
- Ignore `_opti` helper structures.
- Do not score overlapping lower-dose parent PTVs when an evaluation target is required.

The shared implementation is in `core/homogeneity.py`. Site workflows append HI rows near the end of the Final Metrics Table, immediately before the plan-level MUF row, and include the HI score in the Target Dose Quality domain.

## Score calculation

Metric scores are grouped by domain. Only finite scores from included structures contribute. The final score is calculated from the active domain scores using the site-specific grading rules. Plan-level metrics, including MUF, remain included independently of contour checkboxes.

## Reliability rules

- Do not remove the existing anti-crash and guarded DVH calculation behavior.
- A failed structure calculation should generate a warning and allow the remaining structures to continue.
- Never allow missing optional metrics to stop the full scorecard.
- Maintain stable result keys so comparison and exports continue to work.
- Clear Streamlit cache after deploying changes that alter DICOM or metric calculations.

## Adding a new metric

1. Calculate the raw value in the appropriate DVH or DICOM engine.
2. Add or reuse a shared scoring function in `core/metric_engine.py` or a dedicated shared module.
3. Create a complete metric row in both active site workflows where applicable.
4. Add the score to the correct domain.
5. Confirm score-inclusion behavior.
6. Confirm the metric appears in single-plan review, Plan A/Plan B comparison, exports, and tests.
7. Add boundary and missing-data tests.

## Repository hygiene

Keep one canonical file for each module. Do not commit files with names such as `(1)`, `(2)`, or `_copy`. Do not commit ZIP packages, `__pycache__`, `.pyc` files, temporary installation guides, or generated reports.
