#!/usr/bin/env python3
"""Compare the live 24SevenOffice OpenAPI spec with the snapshot in openapi/openapi.json.

Reports added/removed operations, query parameters and schema properties, so API
changes can be picked up in the wrapper. Exits 1 when anything changed.

Usage:
    python scripts/check_spec.py            # report differences
    python scripts/check_spec.py --update   # also overwrite the snapshot
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Set

import httpx

SPEC_URL = "https://rest.api.24sevenoffice.com/v1/openapi.json"
SNAPSHOT = Path(__file__).resolve().parent.parent / "openapi" / "openapi.json"
METHODS = {"get", "post", "put", "patch", "delete"}


def operations(spec: Dict[str, Any]) -> Dict[str, Set[str]]:
    """Map "METHOD /path" to its query parameter names."""
    result = {}
    for path, item in spec.get("paths", {}).items():
        shared = item.get("parameters", [])
        for method, op in item.items():
            if method not in METHODS:
                continue
            params = {
                p["name"]
                for p in shared + op.get("parameters", [])
                if isinstance(p, dict) and p.get("in") == "query"
            }
            result[f"{method.upper()} {path}"] = params
    return result


def schema_properties(spec: Dict[str, Any]) -> Dict[str, Set[str]]:
    schemas = spec.get("components", {}).get("schemas", {})

    def props(schema: Dict[str, Any]) -> Set[str]:
        found = set(schema.get("properties", {}))
        for key in ("allOf", "oneOf", "anyOf"):
            for sub in schema.get(key, []):
                if "$ref" in sub:
                    sub = schemas.get(sub["$ref"].rsplit("/", 1)[-1], {})
                found |= props(sub)
        return found

    return {name: props(schema) for name, schema in schemas.items()}


def diff(label: str, old: Dict[str, Set[str]], new: Dict[str, Set[str]]) -> int:
    changes = 0
    for key in sorted(new.keys() - old.keys()):
        print(f"+ {label} {key}")
        changes += 1
    for key in sorted(old.keys() - new.keys()):
        print(f"- {label} {key}")
        changes += 1
    for key in sorted(old.keys() & new.keys()):
        added, removed = new[key] - old[key], old[key] - new[key]
        if added or removed:
            changes += 1
            details = [f"+{p}" for p in sorted(added)] + [f"-{p}" for p in sorted(removed)]
            print(f"~ {label} {key}: {' '.join(details)}")
    return changes


def main() -> int:
    live = httpx.get(SPEC_URL, timeout=30).raise_for_status().json()
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    print(f"snapshot version {snapshot['info']['version']}, live version {live['info']['version']}")

    changes = diff("operation", operations(snapshot), operations(live))
    changes += diff("schema", schema_properties(snapshot), schema_properties(live))
    print("no changes" if not changes else f"{changes} change(s)")

    if "--update" in sys.argv[1:]:
        SNAPSHOT.write_text(json.dumps(live, indent=2) + "\n", encoding="utf-8")
        print(f"updated {SNAPSHOT}")
    return 1 if changes else 0


if __name__ == "__main__":
    sys.exit(main())
