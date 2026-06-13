"""VAW-based attribute plausibility filter.

Loads the pre-built table from data/processed/vaw_object_attributes.json
and provides a single function to narrow an attribute pool to plausible
values for a given object.

If the table file is missing or an object is not in the table, the pool
is returned unchanged (graceful fallback to concept_library defaults).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

_TABLE_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "vaw_object_attributes.json"
_table: dict[str, dict[str, list[str]]] | None = None


def _load() -> dict[str, dict[str, list[str]]]:
    global _table
    if _table is not None:
        return _table
    if not _TABLE_PATH.exists():
        _table = {}
        return _table
    with open(_TABLE_PATH) as f:
        _table = json.load(f)
    return _table


def filter_pool(
    object_name: str,
    attr_type: str,
    pool: Sequence[str],
) -> tuple[str, ...]:
    """Return the subset of *pool* that is plausible for *object_name*.

    *attr_type* is one of "color", "material", "pattern".

    Falls back to the full pool when the object or attribute type has no
    VAW data, ensuring the sampler always has at least the original pool.
    """
    table = _load()
    base = object_name.lower().strip()
    for word in base.split():
        entry = table.get(word)
        if entry is not None:
            break
    else:
        return tuple(pool)

    plausible = entry.get(attr_type)
    if not plausible:
        return tuple(pool)

    filtered = tuple(v for v in pool if v in plausible)
    if not filtered:
        return tuple(pool)
    return filtered
