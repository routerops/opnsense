# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

SELECTED = (1, "1", True)


def _is_option_map(value):
    return isinstance(value, dict) and all(isinstance(v, dict) for v in value.values())


def _selected_keys(option_map):
    return [k for k, v in option_map.items() if k != "" and v.get("selected") in SELECTED]


def _as_list(read, separator):
    if read is None or read == [] or read == "":
        return []
    if _is_option_map(read):
        return _selected_keys(read)
    if isinstance(read, list):
        return [str(v) for v in read]
    return [v for v in str(read).split(separator) if v != ""]


def normalize(read, wanted, ordered=False, separator=","):
    if isinstance(wanted, bool):
        return read in SELECTED
    if isinstance(wanted, int):
        if read in ("", None):
            return None
        return int(read)
    if isinstance(wanted, list):
        values = _as_list(read, separator)
        return values if ordered else sorted(values)
    if read is None or read == []:
        return ""
    if _is_option_map(read):
        return separator.join(_selected_keys(read))
    return str(read)


def to_api(wanted, separator=","):
    if isinstance(wanted, dict):
        return {k: to_api(v, separator) for k, v in wanted.items()}
    if isinstance(wanted, bool):
        return "1" if wanted else "0"
    if isinstance(wanted, list):
        return separator.join(str(v) for v in wanted)
    if wanted is None:
        return ""
    return str(wanted)


def _comparable(wanted, ordered):
    if wanted is None:
        return ""
    if isinstance(wanted, list):
        values = [str(v) for v in wanted]
        return values if ordered else sorted(values)
    return wanted


def field_diff(current, wanted, ordered_fields=(), separators=None, _prefix=""):
    separators = separators or {}
    changes = {}
    for name, want in wanted.items():
        full = _prefix + name
        if not isinstance(current, dict) or name not in current:
            raise KeyError(full)
        if isinstance(want, dict):
            changes.update(field_diff(current[name], want, ordered_fields, separators, full + "."))
            continue
        ordered = full in ordered_fields
        before = normalize(current[name], want, ordered, separators.get(full, ","))
        if before != _comparable(want, ordered):
            changes[full] = (before, want)
    return changes


def nest_fields(flat):
    nested = {}
    for name, value in flat.items():
        node = nested
        parts = name.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return nested
