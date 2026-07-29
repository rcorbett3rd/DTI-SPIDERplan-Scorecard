# Release checklist

Before tagging Version 1.0:

- Run the complete pytest suite.
- Run `python scripts/validate_release.py`.
- Remove all `__pycache__` folders.
- Remove temporary Build README and CHANGELOG files.
- Remove Build ZIP archives from the repository.
- Confirm `README.md`, `CHANGELOG.md`, and `LICENSE.md`.
- Confirm Streamlit launches for both treatment sites.
- Process at least one de-identified Prostate case.
- Process at least one de-identified Head & Neck case.
- Confirm Gy/cGy normalization.
- Confirm per-target prescription assignment.
- Confirm eval-only V105% handling.
- Confirm blue missing-eval behavior.
- Confirm OAR assignment selectors.
- Confirm score inclusion checklists.
- Confirm Plan A versus Plan B winner highlighting.
- Confirm TV, OAR, and global comparison graphs.
- Confirm interactive comparison DVH.
- Confirm detailed review.
- Confirm PDF, CSV, and JSON exports.
- Confirm the clinical/legal notice appears correctly.
