# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: BSD-2-Clause
# Internal to routerops.opnsense, not a public API; it may change in any release.
# Connection options, client construction and dotted-key helpers shared by the modules.

from __future__ import annotations

from ansible.module_utils.basic import env_fallback

from ansible_collections.routerops.opnsense.plugins.module_utils._client import OPNsenseClient

CONNECTION_ARGSPEC = dict(
    url=dict(type="str", required=True, fallback=(env_fallback, ["OPNSENSE_URL"])),
    api_key=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["OPNSENSE_API_KEY"])),
    api_secret=dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["OPNSENSE_API_SECRET"])),
    validate_certs=dict(type="bool", default=True, fallback=(env_fallback, ["OPNSENSE_VALIDATE_CERTS"])),
    timeout=dict(type="int", default=30),
)


def client_from_params(params):
    """Build an OPNsenseClient from the module's connection parameters."""
    return OPNsenseClient(
        params["url"],
        params["api_key"],
        params["api_secret"],
        validate_certs=params["validate_certs"],
        timeout=params["timeout"],
    )


def get_path(data, key):
    """Follow a dotted key through nested dicts; raise KeyError naming the key when a step is missing."""
    for part in key.split("."):
        if not isinstance(data, dict) or part not in data:
            raise KeyError(key)
        data = data[part]
    return data


def nest(key, value):
    """Wrap a value in nested dicts along a dotted key; the inverse of get_path."""
    for part in reversed(key.split(".")):
        value = {part: value}
    return value
