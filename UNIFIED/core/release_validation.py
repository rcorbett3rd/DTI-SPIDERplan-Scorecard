"""Runtime and release-candidate validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .result_contract import validate_result


@dataclass(frozen=True)
class ValidationItem:
    level: str
    code: str
    message: str


REQUIRED_REPOSITORY_FILES = (
    "app.py",
    "README.md",
    "CHANGELOG.md",
    "LICENSE.md",
    "requirements.txt",
    "prostate_config.json",
    "hn_scoring_config.json",
)

REQUIRED_PACKAGES = (
    "core",
    "sites",
    "ui",
    "tests",
)


def validate_repository(root: str | Path) -> list[ValidationItem]:
    root_path = Path(root)
    items: list[ValidationItem] = []

    for name in REQUIRED_REPOSITORY_FILES:
        if not (root_path / name).exists():
            items.append(
                ValidationItem("error", "missing_file", f"Missing required file: {name}")
            )

    for name in REQUIRED_PACKAGES:
        package = root_path / name
        if not package.is_dir():
            items.append(
                ValidationItem("error", "missing_package", f"Missing package: {name}/")
            )
        elif not (package / "__init__.py").exists() and name != "tests":
            items.append(
                ValidationItem(
                    "error",
                    "missing_initializer",
                    f"Missing package initializer: {name}/__init__.py",
                )
            )

    for name in ("prostate_site.py", "head_neck_site.py"):
        if not (root_path / name).exists():
            items.append(
                ValidationItem(
                    "error",
                    "missing_site_workflow",
                    f"Missing active site workflow: {name}",
                )
            )

    cache_paths = list(root_path.rglob("__pycache__"))
    if cache_paths:
        items.append(
            ValidationItem(
                "warning",
                "python_cache",
                f"Remove {len(cache_paths)} __pycache__ folder(s) before packaging.",
            )
        )

    temporary_build_docs = [
        path
        for path in root_path.iterdir()
        if path.is_file()
        and (
            path.name.startswith("README_BUILD")
            or path.name.startswith("CHANGELOG_BUILD")
        )
    ]
    if temporary_build_docs:
        items.append(
            ValidationItem(
                "warning",
                "temporary_build_docs",
                "Remove temporary Build README/CHANGELOG files.",
            )
        )

    duplicate_build_archives = [
        path for path in root_path.iterdir()
        if path.is_file() and "Build" in path.name and path.suffix.lower() == ".zip"
    ]
    if duplicate_build_archives:
        items.append(
            ValidationItem(
                "warning",
                "build_archives",
                "Remove Build ZIP archives from the production repository.",
            )
        )

    return items


def validate_plan_result(result: Mapping[str, Any]) -> list[ValidationItem]:
    items = [
        ValidationItem("error", "result_contract", message)
        for message in validate_result(result)
    ]

    if result.get("missing_eval"):
        items.append(
            ValidationItem(
                "warning",
                "missing_eval",
                "One or more required evaluation target structures are missing.",
            )
        )

    if not result.get("metrics"):
        items.append(
            ValidationItem(
                "warning",
                "no_metrics",
                "No configured scoring metrics were generated.",
            )
        )

    if not result.get("dvhs"):
        items.append(
            ValidationItem(
                "info",
                "no_dvh",
                "No DVH curves are attached to this result.",
            )
        )

    return items
