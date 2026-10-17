# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# Module routerops.opnsense.settings: manage an OPNsense settings singleton.

from __future__ import annotations

DOCUMENTATION = r"""
module: settings
short_description: Manage an OPNsense settings singleton through the MVC API
version_added: "0.1.0"
description:
  - Reads a settings singleton with its C(get) action, compares the named fields and writes only the fields that differ with its C(set) action.
  - Runs the apply action once after a write, and never when nothing changed.
  - Works on every OPNsense model controller, because the controller base class provides C(get) and C(set).
author:
  - routerops.opnsense contributors (@routerops)
attributes:
  check_mode:
    support: full
    description: Reads the live settings and reports what would change without writing.
  diff_mode:
    support: full
    description: Shows the changed fields before and after. Field values are printed, so personal data such as hostnames or MAC addresses can appear.
extends_documentation_fragment:
  - routerops.opnsense.connection
  - routerops.opnsense.fields
options:
  path:
    description: Controller base path below C(/api/), for example C(nodeexporter/general).
    type: str
    required: true
  key:
    description:
      - JSON wrapper key of the settings in the C(get) response, for example C(general).
      - A dotted key such as C(unbound.general) addresses settings nested below the model's top level.
    type: str
    required: true
  fields:
    description:
      - Wanted field values. Only these fields are compared and written.
      - Use V(true)/V(false) for boolean fields, integers for numeric fields, a list for multi-select fields and a nested dictionary for nested fields.
    type: dict
    required: true
  actions:
    description: Action names that differ from the defaults C(get) and C(set).
    type: dict
    default: {}
  apply:
    description:
      - Action path below C(/api/) that applies the configuration after a write, for example C(nodeexporter/service/reconfigure).
      - Omit it to skip applying.
    type: str
  write_only:
    description:
      - Values of fields OPNsense accepts but never returns, such as passwords, in the same shape as O(fields).
      - They are not compared, never logged, shown in the diff or returned, and are sent along with any write.
      - Every name must exist in the C(get) response; OPNsense returns update-only fields as empty strings, so a misspelled name fails the task.
      - A name must not appear in both O(fields) and O(write_only).
    type: dict
    default: {}
  update_write_only:
    description:
      - A settings singleton is never created, so with V(on_create) the write-only values are only sent along when another field in O(fields) changes.
      - Use V(always) to set a write-only value for the first time or to rotate it; the task then writes and reports changed on every run.
    type: str
    choices: [on_create, always]
    default: on_create
  ordered_fields:
    description: Multi-select fields whose order matters. Other lists compare regardless of order.
    type: list
    elements: str
    default: []
  separators:
    description: Separator per list field when it is not a comma, for example a newline for alias C(content).
    type: dict
    default: {}
notes:
  - Success is the API's C(result) of C(saved), never the HTTP status; a failed write shows the C(validations) returned by OPNsense.
  - Descriptions reject C(-); interface C(type6) must be C(none), not an empty string; numeric fields where C(0) is rejected take V(null) to unset.
  - Settings configured through legacy PHP pages (system general settings, NTP, PPPoE) have no MVC API and cannot be managed.
"""

# BEGIN EXAMPLES: generated from meta/areas.yml by make docs
EXAMPLES = r"""
- name: Enable node_exporter on port 9100
  routerops.opnsense.settings:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "nodeexporter/general"
    key: "general"
    apply: "nodeexporter/service/reconfigure"
    fields:
      enabled: true
      listenport: 9100
"""
# END EXAMPLES: generated from meta/areas.yml by make docs

RETURN = r"""
settings:
  description: The named fields as read before any write, normalised; write-only fields are left out.
  returned: success
  type: dict
  sample: {"enabled": false, "listenport": 9100}
validations:
  description: Field errors reported by OPNsense when a write fails.
  returned: failure
  type: dict
  sample: {"general.listenport": "Please provide a valid port number."}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.routerops.opnsense.plugins.module_utils._client import (
    OPNsenseError,
    require_ok,
    require_saved,
)
from ansible_collections.routerops.opnsense.plugins.module_utils._common import (
    CONNECTION_ARGSPEC,
    client_from_params,
    get_path,
    nest,
)
from ansible_collections.routerops.opnsense.plugins.module_utils._fields import (
    check_names,
    field_diff,
    flatten,
    mask_secrets,
    nest_fields,
    normalize,
    secret_values,
    stored_secret_values,
    to_api,
)

DEFAULT_ACTIONS = {"get": "get", "set": "set"}


def snapshot(current, wanted, ordered_fields, separators, prefix=""):
    """Return the wanted fields' current values, normalised and nested like the wanted fields."""
    values = {}
    for name, want in wanted.items():
        full = prefix + name
        if isinstance(want, dict):
            values[name] = snapshot(current[name], want, ordered_fields, separators, full + ".")
        else:
            values[name] = normalize(current[name], want, full in ordered_fields, separators.get(full, ","))
    return values


ARGUMENT_SPEC = dict(
    CONNECTION_ARGSPEC,
    path=dict(type="str", required=True),
    key=dict(type="str", required=True, no_log=False),
    fields=dict(type="dict", required=True),
    actions=dict(type="dict", default={}),
    apply=dict(type="str"),
    write_only=dict(type="dict", default={}, no_log=True),
    update_write_only=dict(type="str", choices=["on_create", "always"], default="on_create"),
    ordered_fields=dict(type="list", elements="str", default=[]),
    separators=dict(type="dict", default={}),
    secret_fields=dict(type="list", elements="str", default=[], no_log=False),
)


def main():
    """Compare the settings singleton with the wanted fields, write the differences and apply."""
    module = AnsibleModule(argument_spec=ARGUMENT_SPEC, supports_check_mode=True)
    p = module.params
    actions = dict(DEFAULT_ACTIONS, **p["actions"])
    write_only = flatten(p["write_only"])
    compared = p["fields"]
    secrets = set(p["secret_fields"])
    module.no_log_values.update(secret_values(flatten(compared), secrets))
    nested = sorted(s for s in secrets if any(n.startswith(s + ".") for n in flatten(compared)))
    if nested:
        module.fail_json(msg="secret field '%s' holds nested fields; name each nested secret field" % "', '".join(nested))
    separators = p["separators"]
    ordered = tuple(p["ordered_fields"])
    try:
        check_names(compared, write_only, ordered, separators)
    except ValueError as e:
        module.fail_json(msg=str(e))

    client = client_from_params(p)
    saved = False
    try:
        response = client.get("%s/%s" % (p["path"], actions["get"]))
        try:
            section = get_path(response, p["key"])
        except KeyError:
            module.fail_json(msg="key '%s' not found in response" % p["key"])
        module.no_log_values.update(stored_secret_values(section, secrets))
        for name in write_only:
            try:
                get_path(section, name)
            except KeyError:
                module.fail_json(msg="field '%s' not found in '%s'" % (name, p["key"]))
        try:
            changes = field_diff(section, compared, ordered, separators, secrets=secrets)
            current = snapshot(section, compared, ordered, separators)
            module.no_log_values.update(secret_values(flatten(current), secrets))
        except KeyError as e:
            module.fail_json(msg="field '%s' not found in '%s'" % (e.args[0], p["key"]))
        except ValueError as e:
            module.fail_json(msg=str(e))

        write_needed = bool(changes) or bool(write_only and p["update_write_only"] == "always")
        if write_needed and not module.check_mode:
            flat_wanted = flatten(compared)
            payload = {name: to_api(flat_wanted[name], separators.get(name, ",")) for name in changes}
            payload.update({k: to_api(v, separators.get(k, ",")) for k, v in write_only.items()})
            require_saved(client.post("%s/%s" % (p["path"], actions["set"]), nest(p["key"], nest_fields(payload))))
            saved = True
            if p["apply"]:
                require_ok(client.post(p["apply"]))
    except OPNsenseError as e:
        msg = e.msg + "; saved but not applied" if saved else e.msg
        module.fail_json(msg=msg, validations=e.validations, changed=saved)

    module.exit_json(
        changed=write_needed,
        settings=mask_secrets(current, secrets),
        diff=dict(
            before=mask_secrets({k: v[0] for k, v in changes.items()}, secrets),
            after=mask_secrets({k: v[1] for k, v in changes.items()}, secrets),
        ),
    )


if __name__ == "__main__":
    main()
