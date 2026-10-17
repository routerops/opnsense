# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

from ansible_collections.routerops.opnsense.plugins.module_utils.client import OPNsenseClient

CONNECTION_ARGSPEC = dict(
    url=dict(type="str", required=True),
    api_key=dict(type="str", required=True, no_log=True),
    api_secret=dict(type="str", required=True, no_log=True),
    validate_certs=dict(type="bool", default=True),
    timeout=dict(type="int", default=30),
)


def client_from_params(params):
    return OPNsenseClient(
        params["url"],
        params["api_key"],
        params["api_secret"],
        validate_certs=params["validate_certs"],
        timeout=params["timeout"],
    )


def get_path(data, key):
    for part in key.split("."):
        if not isinstance(data, dict) or part not in data:
            raise KeyError(key)
        data = data[part]
    return data


def nest(key, value):
    for part in reversed(key.split(".")):
        value = {part: value}
    return value
