from __future__ import annotations

from pathlib import Path
import json
import sys

from core.release import release_health
from core.release_validation import validate_repository


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    items = validate_repository(root)
    health = release_health(root)

    print(json.dumps(health.as_dict(), indent=2))
    for item in items:
        print(f"[{item.level.upper()}] {item.code}: {item.message}")

    return 0 if health.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
