"""Treatment-site registry used by the unified launcher and future shared UI."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .base import SiteAdapter


_SITE_MODULES = {
    "prostate": "sites.prostate",
    "head_neck": "sites.head_neck",
}

_SITE_ALIASES = {
    "prostate": "prostate",
    "pros": "prostate",
    "head neck": "head_neck",
    "head and neck": "head_neck",
    "head_neck": "head_neck",
    "hn": "head_neck",
    "h n": "head_neck",
}


def normalize_site_key(site: str) -> str:
    value = str(site).strip().lower().replace("&", "and").replace("-", " ")
    value = " ".join(value.split())
    try:
        return _SITE_ALIASES[value]
    except KeyError as exc:
        supported = ", ".join(display_names())
        raise ValueError(
            f"Unsupported treatment site {site!r}. Supported sites: {supported}."
        ) from exc


def get_site(site: str) -> SiteAdapter:
    """Return the disease adapter module for a treatment-site label or key."""

    key = normalize_site_key(site)
    return import_module(_SITE_MODULES[key])


def profiles() -> tuple[Any, ...]:
    return tuple(get_site(key).PROFILE for key in _SITE_MODULES)


def display_names() -> tuple[str, ...]:
    return tuple(profile.display_name for profile in profiles())


def site_keys() -> tuple[str, ...]:
    return tuple(_SITE_MODULES)
