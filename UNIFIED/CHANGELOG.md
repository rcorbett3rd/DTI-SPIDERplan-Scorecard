# Changelog

## 1.0.0-rc.2

### Added

- ICRU 83 Homogeneity Index: `HI = (D2% - D98%) / D50%`.
- HI scoring for both Prostate and Head & Neck plan evaluations.
- SIB-aware target selection: highest-dose PTV directly; lower-dose matching `*_eval` PTVs only.
- D50 sampling and transparent D2/D50/D98 display values.
- Shared HI calculation/scoring module and regression tests.

### Preserved

- Existing coverage, V105%, hotspot, OAR, MUF, comparison, DVH, export, and score-inclusion behavior.
- Existing `_opti` exclusion and blue missing-eval handling.


## 1.0.0-rc.1

### Added

- Unified Prostate and Head & Neck treatment-site registry.
- Shared DICOM and DVH engine façades.
- Shared result contract.
- Shared OAR assignment and score-inclusion systems.
- Shared prescription and target-assignment logic.
- Shared clinical metric pipeline.
- Shared single-plan and plan-comparison runtime.
- Shared SPIDERplan comparison calculations.
- Shared interactive crosshair DVH components.
- Shared detailed-review components.
- Shared CSV and JSON export preparation.
- Runtime repository and result validation.
- Release health script and release-candidate tests.

### Preserved

- Finalized Prostate interface and workflow.
- Corrected Gy/cGy DVH calculations.
- Prostate target and OAR clinical behavior.
- Head & Neck disease-specific scoring logic.
- Eval-only V105% handling for lower-dose targets.
- Blue missing-eval handling.
- User-selectable score inclusion.
- Configurable OAR assignment.
- Plan comparison, detailed review, and export workflows.

### Release note

The active `prostate_site.py` and `head_neck_site.py` workflow modules are
preserved in this release candidate to avoid changing validated behavior while
the shared architecture is introduced.
