# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: BSD-2-Clause
# Internal to routerops.opnsense, not a public API; it may change in any release.
# Normalisation, comparison and conversion of OPNsense field values.

from __future__ import annotations

SELECTED = (1, "1", True)


def _is_option_map(value):
    """Tell whether a read value is an OPNsense option map (a dict of dicts)."""
    return isinstance(value, dict) and all(isinstance(v, dict) for v in value.values())


def _selected_keys(option_map):
    """Return the selected, non-empty keys of an option map."""
    return [k for k, v in option_map.items() if k != "" and v.get("selected") in SELECTED]


def _as_list(read, separator):
    """Turn a read value (option map, list, separated string or empty) into a list of strings."""
    if read is None or read == [] or read == "":
        return []
    if _is_option_map(read):
        return _selected_keys(read)
    if isinstance(read, list):
        return [str(v) for v in read]
    return [v for v in str(read).split(separator) if v != ""]


def normalize(read, wanted, ordered=False, separator=","):
    """Convert a read value to the plain form of the wanted value, so the two can be compared."""
    if isinstance(wanted, bool):
        return read in SELECTED
    if isinstance(wanted, int):
        if _is_option_map(read):
            read = separator.join(_selected_keys(read))
        if read in ("", None, []):
            return None
        return int(read)
    if isinstance(wanted, list):
        values = _as_list(read, separator)
        return values if ordered else sorted(values)
    if read is None:
        return ""
    if isinstance(read, list):
        return separator.join(str(v) for v in read)
    if _is_option_map(read):
        return separator.join(_selected_keys(read))
    return str(read)


def to_api(wanted, separator=","):
    """Convert a wanted value to the strings OPNsense accepts, joining lists with the separator."""
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
    """Return the wanted value in the form normalize produces for it."""
    if wanted is None:
        return ""
    if isinstance(wanted, list):
        values = [str(v) for v in wanted]
        return values if ordered else sorted(values)
    if isinstance(wanted, (bool, int)):
        return wanted
    return str(wanted)


def field_diff(current, wanted, ordered_fields=(), separators=None, _prefix=""):
    """Return {field: (before, after)} for every wanted field whose read value differs; raise KeyError for an unknown field."""
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
        try:
            before = normalize(current[name], want, ordered, separators.get(full, ","))
        except (TypeError, ValueError):
            raise ValueError("field '%s': cannot compare %r with %r" % (full, current[name], want))
        if before != _comparable(want, ordered):
            changes[full] = (before, want)
    return changes


def nest_fields(flat):
    """Turn dotted field names into nested dicts."""
    nested = {}
    for name, value in flat.items():
        node = nested
        parts = name.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return nested


def flatten(wanted, prefix=""):
    """Turn nested dicts into dotted field names; the inverse of nest_fields."""
    flat = {}
    for name, value in wanted.items():
        if isinstance(value, dict):
            flat.update(flatten(value, prefix + name + "."))
        else:
            flat[prefix + name] = value
    return flat


def check_names(compared, write_only, ordered_fields, separators):
    """Raise ValueError for a field in both fields and write_only, or an unknown name in ordered_fields or separators."""
    names = set(flatten(compared))
    overlap = sorted(names & set(write_only))
    if overlap:
        raise ValueError("field '%s' is in both fields and write_only" % "', '".join(overlap))
    known = names | set(write_only)
    for option, given in (("ordered_fields", ordered_fields), ("separators", separators)):
        unknown = sorted(set(given) - known)
        if unknown:
            raise ValueError("unknown field '%s' in %s" % ("', '".join(unknown), option))
