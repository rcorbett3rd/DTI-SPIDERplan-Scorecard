# Architecture

The application uses four principal layers.

## Application launcher

`app.py` owns Streamlit page configuration, treatment-site selection, release
status, and site workflow routing.

## Shared core

`core/` contains result contracts, assignment logic, prescription logic,
clinical scoring orchestration, comparison calculations, export preparation,
runtime preparation, and release validation.

## Disease packages

`sites/prostate/` and `sites/head_neck/` contain disease-specific recognition,
aliases, prescriptions, metric definitions, and thin clinical adapters.

## Interface components

`ui/` contains reusable Prostate-style cards, tables, DVH plots, comparison
views, review sections, workflow controls, and export controls.

The root site workflow modules are retained as the validated rendering layer in
Release Candidate 1.
