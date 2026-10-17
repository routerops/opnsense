# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# Module routerops.opnsense.item: manage OPNsense items.

from __future__ import annotations

DOCUMENTATION = r"""
module: item
short_description: Manage OPNsense items through the MVC API
version_added: "0.1.0"
description:
  - Searches the items of one controller, matches each listed item by its lookup fields, then adds, updates or deletes it.
  - Compares and writes only the fields the caller names.
  - Runs the apply action once after any write, and never when nothing changed.
author:
  - routerops.opnsense contributors (@routerops)
attributes:
  check_mode:
    support: full
    description: Reads the live items and reports what would change without writing; an item that does not exist yet is reported as added.
  diff_mode:
    support: full
    description: Shows the changed fields per item before and after. Field values are printed, so personal data such as hostnames or MAC addresses can appear.
extends_documentation_fragment:
  - routerops.opnsense.connection
options:
  path:
    description: Controller base path below C(/api/), for example C(firewall/alias).
    type: str
    required: true
  key:
    description:
      - Item key in the get response and in write payloads, for example C(alias).
      - A dotted key addresses an item nested below the response's top level.
    type: str
    required: true
  items:
    description:
      - The wanted items. Lookup values must be unique among them.
      - A reference to another item is that item's UUID, taken from an earlier task's return value; the module does not resolve references.
    type: list
    elements: dict
    required: true
    suboptions:
      fields:
        description:
          - Wanted field values. Only these fields are compared and written.
          - Use V(true)/V(false) for boolean fields, integers for numeric fields, a list for multi-select fields and a nested dictionary for nested fields.
        type: dict
        required: true
      write_only:
        description:
          - Values of fields OPNsense accepts but never returns, such as passwords or keys, in the same shape as O(items[].fields).
          - They are not compared, never logged, shown in the diff or returned, and are sent when the item is added.
        type: dict
        default: {}
      state:
        description: Whether the item exists.
        type: str
        choices: [present, absent]
        default: present
  lookup:
    description:
      - Fields that identify an item; several fields form a composite key. Each must be in every item's O(items[].fields).
      - A lookup value that matches more than one existing item fails the task.
    type: list
    elements: str
    default: [description]
  actions:
    description:
      - Action names that differ from the defaults, by role. Roles are C(search), C(get), C(add), C(set) and C(del).
      - The defaults are C(search_item), C(get_item), C(add_item), C(set_item) and C(del_item).
      - Most areas need this; Dnsmasq hosts, for example, use C(searchHost), C(getHost), C(addHost), C(setHost) and C(delHost).
    type: dict
    default: {}
  apply:
    description:
      - Action path below C(/api/) that applies the configuration after a write, for example C(firewall/alias/reconfigure).
      - Omit it to skip applying.
    type: str
  purge:
    description:
      - Delete every item the search returns that no listed item matches, after handling the listed items.
      - Some areas list items the caller did not create; the firewall alias search lists the built-in aliases, so O(purge) is unusable there.
      - Run it in check mode first; RV(purged) lists what would be deleted.
      - A row OPNsense answers C(not found) for, such as a built-in entry, counts as already gone; check mode lists it in RV(purged).
    type: bool
    default: false
  update_write_only:
    description:
      - With V(on_create), write-only values are sent only when an item is added.
      - With V(always), they are also sent to every matched item, which then reports changed on every run.
    type: str
    choices: [on_create, always]
    default: on_create
  ordered_fields:
    description: Multi-select fields whose order matters. Other lists compare regardless of order.
    type: list
    elements: str
    default: []
  separators:
    description:
      - Separator per list field when it is not a comma, for example a newline for alias C(content).
      - Applies to every item; a name no item uses is ignored, so the option can come from C(module_defaults).
    type: dict
    default: {}
notes:
  - Success is the API's C(result) of C(saved) or C(deleted), never the HTTP status; a failed write shows the C(validations) returned by OPNsense.
  - The module never reorders items; set C(sequence) where order matters, such as filter rules and NAT.
  - Descriptions reject C(-); interface C(type6) must be C(none), not an empty string; numeric fields where C(0) is rejected take V(null) to unset.
  - A C(set) action the controller does not define answers C(saved) and changes nothing; override the action name in O(actions).
  - Interface assignment items are keyed by the interface name, not a UUID, and are looked up by their device field.
"""

EXAMPLES = r"""
- name: Add a Dnsmasq host
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: dnsmasq/settings
    key: host
    lookup: [host, domain]
    actions:
      search: searchHost
      get: getHost
      add: addHost
      set: setHost
      del: delHost
    apply: dnsmasq/service/reconfigure
    items:
      - fields:
          host: printer
          domain: example.test
          ip: 192.0.2.10

- name: Keep a host alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: firewall/alias
    key: alias
    lookup: [name]
    separators:
      content: "\n"
    apply: firewall/alias/reconfigure
    items:
      - fields:
          name: web_servers
          type: host
          content: [192.0.2.21, 192.0.2.22]
          description: Web servers
"""

RETURN = r"""
outcomes:
  description: One entry per listed item, in the order given.
  returned: success
  type: list
  elements: dict
  contains:
    uuid:
      description: The item's identifier; null for an item added in check mode or absent and not found.
      type: str
    lookup:
      description: The item's lookup fields as given.
      type: dict
    action:
      description: What happened to the item.
      type: str
      choices: [added, updated, deleted, unchanged]
  sample: [{"uuid": "5e5b5c62-7a7b-4e0e-9e4c-0a1b2c3d4e5f", "lookup": {"name": "web_servers"}, "action": "added"}]
purged:
  description: UUIDs of the items O(purge) deleted or, in check mode, would delete.
  returned: success
  type: list
  elements: str
validations:
  description: Field errors reported by OPNsense when a write fails.
  returned: failure
  type: dict
  sample: {"alias.name": "An alias with this name already exists."}
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.routerops.opnsense.plugins.module_utils._client import (
    OPNsenseError,
    require_deleted,
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
    nest_fields,
    to_api,
)

DEFAULT_ACTIONS = {"search": "search_item", "get": "get_item", "add": "add_item", "set": "set_item", "del": "del_item"}

ARGUMENT_SPEC = dict(
    CONNECTION_ARGSPEC,
    path=dict(type="str", required=True),
    key=dict(type="str", required=True, no_log=False),
    items=dict(
        type="list",
        elements="dict",
        required=True,
        options=dict(
            fields=dict(type="dict", required=True),
            write_only=dict(type="dict", default={}, no_log=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
        ),
    ),
    lookup=dict(type="list", elements="str", default=["description"]),
    actions=dict(type="dict", default={}),
    apply=dict(type="str"),
    purge=dict(type="bool", default=False),
    update_write_only=dict(type="str", choices=["on_create", "always"], default="on_create"),
    ordered_fields=dict(type="list", elements="str", default=[]),
    separators=dict(type="dict", default={}),
)


class Run:
    """One module run: look up the listed items, then add, update or delete them and apply once."""
    def __init__(self, module, client):
        """Keep the module, the client and the options, and start with nothing written."""
        self.module = module
        self.client = client
        p = module.params
        self.path = p["path"]
        self.key = p["key"]
        self.lookup = p["lookup"]
        self.ordered = tuple(p["ordered_fields"])
        self.separators = p["separators"]
        self.actions = dict(DEFAULT_ACTIONS, **p["actions"])
        self.wrote = False
        self.purged = []
        self.saved = []
        self.before = {}
        self.after = {}

    def fail(self, msg):
        """Fail the task with a message."""
        self.module.fail_json(msg=msg)

    def sep(self, name):
        """Return the list separator of a field."""
        return self.separators.get(name, ",")

    def wanted_lookup(self, entry):
        """Return the lookup fields and their wanted values of an item."""
        flat = flatten(entry["fields"])
        return {name: flat[name] for name in self.lookup}

    def label(self, values):
        """Return the 'field=value' label of lookup values used in the diff and in messages."""
        return ",".join("%s=%s" % (name, to_api(values[name], self.sep(name))) for name in self.lookup)

    def matches(self, current, wanted):
        """Tell whether stored values match wanted ones; values that cannot be compared do not match."""
        try:
            return not field_diff(current, wanted, self.ordered, self.separators)
        except ValueError:
            return False

    def payload(self, values):
        """Build a write payload nested under the item key from flat field values."""
        return nest(self.key, nest_fields({name: to_api(v, self.sep(name)) for name, v in values.items()}))

    def section(self, response, uuid=None):
        """Return the item part of a get response; fail when it is missing."""
        try:
            return get_path(response, self.key)
        except KeyError:
            if uuid:
                self.fail("item %s disappeared during the run" % uuid)
            self.fail("key '%s' not found in response" % self.key)

    def check_fields(self, current, entry, write_only):
        """Fail on an unknown field or write-only name, else return the changed fields."""
        for name in write_only:
            try:
                get_path(current, name)
            except KeyError:
                self.fail("field '%s' not found in '%s'" % (name, self.key))
        try:
            return field_diff(current, entry["fields"], self.ordered, self.separators)
        except KeyError as e:
            self.fail("field '%s' not found in '%s'" % (e.args[0], self.key))
        except ValueError as e:
            self.fail(str(e))

    def check_options(self, entries):
        """Fail on bad options before any request: unknown action roles, field overlaps, missing or duplicate lookup values."""
        unknown = sorted(set(self.module.params["actions"]) - set(DEFAULT_ACTIONS))
        if unknown:
            self.fail("unknown action role '%s' in actions; roles are search, get, add, set, del" % "', '".join(unknown))
        for entry in entries:
            try:
                check_names(entry["fields"], flatten(entry["write_only"]), [], {})
            except ValueError as e:
                self.fail(str(e))
            missing = [name for name in self.lookup if name not in flatten(entry["fields"])]
            if missing:
                self.fail("lookup field '%s' missing from the fields of an item" % "', '".join(missing))
        for i, entry in enumerate(entries):
            wanted = self.wanted_lookup(entry)
            for other in entries[i + 1:]:
                stored = {name: to_api(v, self.sep(name)) for name, v in self.wanted_lookup(other).items()}
                if self.matches(stored, wanted):
                    self.fail("duplicate lookup value '%s' in items" % self.label(wanted))

    def check_row(self, row):
        """Fail when a search row lacks a lookup field."""
        for name in self.lookup:
            if name not in row:
                self.fail("lookup field '%s' not in the search results of '%s'" % (name, self.path))

    def find(self, rows, entry):
        """Return the one search row matching an item's lookup values, None for no match; fail on several."""
        wanted = self.wanted_lookup(entry)
        found = []
        for row in rows:
            self.check_row(row)
            try:
                if not field_diff(row, wanted, self.ordered, self.separators):
                    found.append(row)
            except ValueError as e:
                self.fail("lookup %s" % e)
        if len(found) > 1:
            self.fail("lookup '%s' matches several items: %s" % (self.label(wanted), ", ".join(r["uuid"] for r in found)))
        return found[0] if found else None

    def read_changes(self, entry, uuid):
        """Read a matched item and return its changed fields."""
        current = self.section(self.client.get("%s/%s/%s" % (self.path, self.actions["get"], uuid)), uuid)
        return self.check_fields(current, entry, flatten(entry["write_only"]))

    def update(self, entry, uuid, label, changes):
        """Write the changed fields and write-only values of a matched item; return its action."""
        write_only = flatten(entry["write_only"])
        if not changes and not (write_only and self.module.params["update_write_only"] == "always"):
            return "unchanged"
        flat = flatten(entry["fields"])
        values = {name: flat[name] for name in changes}
        values.update(write_only)
        if not self.module.check_mode:
            require_saved(self.client.post("%s/%s/%s" % (self.path, self.actions["set"], uuid), self.payload(values)))
            self.saved.append(label)
        self.wrote = True
        if changes:
            self.before[label] = {name: change[0] for name, change in changes.items()}
            self.after[label] = {name: change[1] for name, change in changes.items()}
        return "updated"

    def add(self, entry, label):
        """Add an item with all its fields and write-only values; return its UUID (None in check mode)."""
        values = flatten(entry["fields"])
        values.update(flatten(entry["write_only"]))
        uuid = None
        if not self.module.check_mode:
            response = self.client.post("%s/%s" % (self.path, self.actions["add"]), self.payload(values))
            require_saved(response)
            uuid = response.get("uuid")
            self.saved.append(label)
        self.wrote = True
        self.after[label] = entry["fields"]
        return uuid

    def delete(self, uuid, label, lookup):
        """Delete an item; return False when OPNsense answered 'not found'."""
        if not self.module.check_mode:
            response = self.client.post("%s/%s/%s" % (self.path, self.actions["del"], uuid))
            require_deleted(response)
            if response["result"] == "not found":
                return False
            self.saved.append(label)
        self.wrote = True
        self.before[label] = lookup
        return True

    def run(self):
        """Run the whole flow and return one outcome per listed item."""
        p = self.module.params
        entries = p["items"]
        self.check_options(entries)
        search = self.client.get("%s/%s?rowCount=-1" % (self.path, self.actions["search"]))
        if not isinstance(search, dict) or not isinstance(search.get("rows"), list):
            self.fail("unexpected search response from '%s'" % self.path)
        matched = [self.find(search["rows"], entry) for entry in entries]
        to_add = [entry for entry, row in zip(entries, matched) if row is None and entry["state"] == "present"]
        if to_add:
            template = self.section(self.client.get("%s/%s" % (self.path, self.actions["get"])))
            for entry in to_add:
                self.check_fields(template, entry, flatten(entry["write_only"]))
        changes = [
            self.read_changes(entry, row["uuid"]) if row is not None and entry["state"] == "present" else None
            for entry, row in zip(entries, matched)
        ]
        results = []
        for entry, row, change in zip(entries, matched, changes):
            wanted = self.wanted_lookup(entry)
            label = self.label(wanted)
            if entry["state"] == "absent":
                uuid, action = None, "unchanged"
                if row is not None:
                    uuid = row["uuid"]
                    if self.delete(uuid, label, wanted):
                        action = "deleted"
            elif row is None:
                uuid, action = self.add(entry, label), "added"
            else:
                uuid = row["uuid"]
                action = self.update(entry, uuid, label, change)
            results.append({"uuid": uuid, "lookup": wanted, "action": action})
        if p["purge"]:
            listed = set(row["uuid"] for row in matched if row is not None)
            for row in search["rows"]:
                if row["uuid"] not in listed:
                    self.check_row(row)
                    lookup = {name: row[name] for name in self.lookup}
                    if self.delete(row["uuid"], "%s (%s)" % (self.label(lookup), row["uuid"]), lookup):
                        self.purged.append(row["uuid"])
        if self.wrote and p["apply"] and not self.module.check_mode:
            require_ok(self.client.post(p["apply"]))
        return results


def main():
    """Run the item module."""
    module = AnsibleModule(argument_spec=ARGUMENT_SPEC, supports_check_mode=True)
    run = Run(module, client_from_params(module.params))
    try:
        results = run.run()
    except OPNsenseError as e:
        msg = e.msg
        if run.saved:
            msg += "; already saved but not applied: %s" % "; ".join(run.saved)
        module.fail_json(msg=msg, validations=e.validations)
    module.exit_json(changed=run.wrote, outcomes=results, purged=run.purged, diff=dict(before=run.before, after=run.after))


if __name__ == "__main__":
    main()
