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
  - routerops.opnsense.fields
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
        description:
          - Whether the item exists.
          - V(query) only looks the item up and never writes; its outcome reports C(queried), with C(uuid) null when no item matches.
          - V(query) also matches search rows whose C(uuid) is not a UUID, such as the built-in alias C(bogons).
          - O(return_fields) fails on such a row when OPNsense cannot read it.
          - A queried item counts as listed for O(purge).
        type: str
        choices: [present, absent, query]
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
      - Search rows whose C(uuid) is not a UUID, such as automatic filter rules or generated gateways, are not MVC items.
      - O(purge) and the lookup for V(present) and V(absent) ignore them.
      - Run it in check mode first; RV(purged) lists what would be deleted.
      - O(purge) cannot be combined with O(id_format=name).
      - A row OPNsense answers C(not found) for, such as a built-in entry, counts as already gone; check mode lists it in RV(purged).
    type: bool
    default: false
  id_format:
    description:
      - How the search names its items.
      - V(uuid) takes only rows whose C(uuid) is a UUID.
      - V(name) takes every row and suits areas keyed by name, such as interface assignment (C(lan), C(opt1)).
    type: str
    choices: [uuid, name]
    default: uuid
    version_added: "0.1.0"
  update_write_only:
    description:
      - With V(on_create), write-only values are sent only when an item is added.
      - With V(always), they are also sent to every matched item, which then reports changed on every run.
    type: str
    choices: [on_create, always]
    default: on_create
  return_fields:
    description:
      - Fields whose current values each outcome returns under C(fields).
      - For example the C(refid) of a certificate authority that an OpenVPN instance refers to.
      - Every name must be a single field of the item; name a nested field with dots, such as C(source.network).
    type: list
    elements: str
    default: []
    version_added: "0.1.0"
  always_send:
    description:
      - Fields sent with their wanted values on every update of an item, next to the changed fields; they never cause a write on their own.
      - For controllers that read a sibling field from the request on every set, such as the Dnsmasq DHCP option C(type).
      - Every present item must list these fields in O(items[].fields).
    type: list
    elements: str
    default: []
    version_added: "0.1.0"
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
  - Descriptions reject C(-); interface C(type6) takes an empty string, not C(none), for no IPv6; numeric fields where C(0) is rejected take V(null) to unset.
  - A C(set) action the controller does not define answers C(saved) and changes nothing; override the action name in O(actions).
  - Interface assignment items are keyed by the interface name, not a UUID; set O(id_format=name).
"""

# BEGIN EXAMPLES: generated from meta/areas.yml by make docs
EXAMPLES = r"""
- name: Add a Dnsmasq host
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "host"
    lookup: ["host", "domain"]
    actions:
      add: "addHost"
      del: "delHost"
      get: "getHost"
      search: "searchHost"
      set: "setHost"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          host: "printer"
          domain: "example.test"
          ip: "192.0.2.10"

- name: Keep only the listed Dnsmasq hosts
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "host"
    lookup: ["host", "domain"]
    actions:
      add: "addHost"
      del: "delHost"
      get: "getHost"
      search: "searchHost"
      set: "setHost"
    apply: "dnsmasq/service/reconfigure"
    purge: true
    items:
      - fields:
          host: "printer"
          domain: "example.test"
          ip: "192.0.2.10"
      - fields:
          host: "scanner"
          domain: "example.test"
          ip: "192.0.2.11"

- name: Remove a Dnsmasq host
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "dnsmasq/settings"
    key: "host"
    lookup: ["host", "domain"]
    actions:
      add: "addHost"
      del: "delHost"
      get: "getHost"
      search: "searchHost"
      set: "setHost"
    apply: "dnsmasq/service/reconfigure"
    items:
      - fields:
          host: "scanner"
          domain: "example.test"
        state: "absent"

- name: Keep a host alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/alias"
    key: "alias"
    lookup: ["name"]
    separators:
      content: "\n"
    secret_fields: ["password"]
    apply: "firewall/alias/reconfigure"
    items:
      - fields:
          name: "web_servers"
          type: "host"
          content: ["192.0.2.21", "192.0.2.22"]
          description: "Web servers"

- name: Keep a port alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/alias"
    key: "alias"
    lookup: ["name"]
    separators:
      content: "\n"
    secret_fields: ["password"]
    apply: "firewall/alias/reconfigure"
    items:
      - fields:
          name: "web_ports"
          type: "port"
          content: ["80", "443"]
          description: "Web ports"

- name: Read a built-in alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/alias"
    key: "alias"
    lookup: ["name"]
    separators:
      content: "\n"
    secret_fields: ["password"]
    apply: "firewall/alias/reconfigure"
    return_fields: ["type"]
    items:
      - fields:
          name: "bogons"
        state: "query"

- name: Forward port 8080 on WAN to a LAN web server
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/d_nat"
    key: "rule"
    lookup: ["descr"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/d_nat/apply"
    items:
      - fields:
          interface: "wan"
          protocol: "tcp"
          destination:
            network: "wanip"
            port: "8080"
          target: "10.250.1.50"
          local-port: "80"
          descr: "routerops example web"

- name: Remove a port forward
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/d_nat"
    key: "rule"
    lookup: ["descr"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/d_nat/apply"
    items:
      - fields:
          descr: "routerops example web"
        state: "absent"

- name: Allow HTTPS to the firewall from LAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/filter"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/filter/apply"
    items:
      - fields:
          interface: "lan"
          protocol: "TCP"
          source_net: "lan"
          destination_net: "(self)"
          destination_port: "443"
          description: "routerops example https"

- name: Block a host on LAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/filter"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/filter/apply"
    items:
      - fields:
          action: "block"
          source_net: "10.250.1.99"
          description: "routerops example block"

- name: Remove a filter rule
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/filter"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/filter/apply"
    items:
      - fields:
          description: "routerops example block"
        state: "absent"

- name: Map a LAN host to a WAN address
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/one_to_one"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/one_to_one/apply"
    items:
      - fields:
          source_net: "10.250.1.50"
          external: "10.250.0.50"
          description: "routerops example one"

- name: Keep only the listed one-to-one rules
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/one_to_one"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/one_to_one/apply"
    purge: true
    items:
      - fields:
          source_net: "10.250.1.50"
          external: "10.250.0.50"
          description: "routerops example one"
      - fields:
          source_net: "10.250.1.51"
          external: "10.250.0.51"
          description: "routerops example two"

- name: Remove a one-to-one rule
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/one_to_one"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/one_to_one/apply"
    items:
      - fields:
          description: "routerops example two"
        state: "absent"

- name: Translate a LAN subnet on WAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/source_nat"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/source_nat/apply"
    items:
      - fields:
          interface: "wan"
          source_net: "10.250.1.0/24"
          description: "routerops example lan"

- name: Remove a source NAT rule
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "firewall/source_nat"
    key: "rule"
    lookup: ["description"]
    actions:
      add: "addRule"
      del: "delRule"
      get: "getRule"
      search: "searchRule"
      set: "setRule"
    apply: "firewall/source_nat/apply"
    items:
      - fields:
          description: "routerops example lan"
        state: "absent"

- name: Assign a VLAN with a static address
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/assignment"
    key: "interface"
    lookup: ["descr"]
    id_format: "name"
    apply: "interfaces/assignment/reconfigure"
    items:
      - fields:
          if: "vlan0.4009"
          descr: "rt_example"
          enable: true
          lock: false
          type4: "staticv4"
          ipaddr: "10.250.49.1/24"
          type6: ""

- name: Remove an assignment
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/assignment"
    key: "interface"
    lookup: ["descr"]
    id_format: "name"
    apply: "interfaces/assignment/reconfigure"
    items:
      - fields:
          descr: "rt_example"
        state: "absent"

- name: Add an IP alias on LAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vip_settings"
    key: "vip"
    lookup: ["descr"]
    secret_fields: ["password"]
    apply: "interfaces/vip_settings/reconfigure"
    items:
      - fields:
          mode: "ipalias"
          interface: "lan"
          network: "10.250.1.250/24"
          descr: "routerops example"

- name: Remove a virtual IP
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vip_settings"
    key: "vip"
    lookup: ["descr"]
    secret_fields: ["password"]
    apply: "interfaces/vip_settings/reconfigure"
    items:
      - fields:
          descr: "routerops example"
        state: "absent"

- name: Add a VLAN on the LAN port
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vlan_settings"
    key: "vlan"
    lookup: ["descr"]
    apply: "interfaces/vlan_settings/reconfigure"
    items:
      - fields:
          if: "vtnet1"
          tag: 4009
          vlanif: "vlan0.4009"
          descr: "routerops example"

- name: Remove a VLAN
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "interfaces/vlan_settings"
    key: "vlan"
    lookup: ["descr"]
    apply: "interfaces/vlan_settings/reconfigure"
    items:
      - fields:
          descr: "routerops example"
        state: "absent"

- name: Reserve an address
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "reservation"
    lookup: ["subnet", "hw_address", "client_id"]
    actions:
      add: "addReservation"
      del: "delReservation"
      get: "getReservation"
      search: "searchReservation"
      set: "setReservation"
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "EXAMPLE_SUBNET_UUID"
          hw_address: "02:00:00:00:69:01"
          client_id: ""
          ip_address: "10.250.69.10"
          hostname: "rt-example"
          description: "routerops example"

- name: Remove a reservation
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "reservation"
    lookup: ["subnet", "hw_address", "client_id"]
    actions:
      add: "addReservation"
      del: "delReservation"
      get: "getReservation"
      search: "searchReservation"
      set: "setReservation"
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "EXAMPLE_SUBNET_UUID"
          hw_address: "02:00:00:00:69:01"
          client_id: ""
        state: "absent"

- name: Add a subnet
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "subnet4"
    lookup: ["subnet"]
    actions:
      add: "addSubnet"
      del: "delSubnet"
      get: "getSubnet"
      search: "searchSubnet"
      set: "setSubnet"
    separators:
      pools: "\n"
    secret_fields: ["ddns_domain_key_secret"]
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "10.250.69.0/24"
          pools: ["10.250.69.100-10.250.69.199"]
          description: "routerops example"

- name: Remove a subnet
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "kea/dhcpv4"
    key: "subnet4"
    lookup: ["subnet"]
    actions:
      add: "addSubnet"
      del: "delSubnet"
      get: "getSubnet"
      search: "searchSubnet"
      set: "setSubnet"
    separators:
      pools: "\n"
    secret_fields: ["ddns_domain_key_secret"]
    apply: "kea/service/reconfigure"
    items:
      - fields:
          subnet: "10.250.69.0/24"
        state: "absent"

- name: Route a remote network through a LAN gateway
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routes/routes"
    key: "route"
    lookup: ["network"]
    actions:
      add: "addroute"
      del: "delroute"
      get: "getroute"
      search: "searchroute"
      set: "setroute"
    apply: "routes/routes/reconfigure"
    items:
      - fields:
          network: "10.99.0.0/24"
          gateway: "RT_EXAMPLE_GW"
          descr: "routerops example"

- name: Keep only the listed static routes
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routes/routes"
    key: "route"
    lookup: ["network"]
    actions:
      add: "addroute"
      del: "delroute"
      get: "getroute"
      search: "searchroute"
      set: "setroute"
    apply: "routes/routes/reconfigure"
    purge: true
    items:
      - fields:
          network: "10.99.0.0/24"
          gateway: "RT_EXAMPLE_GW"
          descr: "routerops example"
      - fields:
          network: "10.99.1.0/24"
          gateway: "RT_EXAMPLE_GW"
          descr: "routerops example"

- name: Remove a static route
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routes/routes"
    key: "route"
    lookup: ["network"]
    actions:
      add: "addroute"
      del: "delroute"
      get: "getroute"
      search: "searchroute"
      set: "setroute"
    apply: "routes/routes/reconfigure"
    items:
      - fields:
          network: "10.99.1.0/24"
        state: "absent"

- name: Add a LAN gateway
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routing/settings"
    key: "gateway_item"
    lookup: ["name"]
    actions:
      add: "addGateway"
      del: "delGateway"
      get: "getGateway"
      search: "searchGateway"
      set: "setGateway"
    apply: "routing/settings/reconfigure"
    items:
      - fields:
          name: "RT_EXAMPLE_GW"
          interface: "lan"
          gateway: "10.250.1.254"
          descr: "routerops example"

- name: Remove a gateway
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "routing/settings"
    key: "gateway_item"
    lookup: ["name"]
    actions:
      add: "addGateway"
      del: "delGateway"
      get: "getGateway"
      search: "searchGateway"
      set: "setGateway"
    apply: "routing/settings/reconfigure"
    items:
      - fields:
          name: "RT_EXAMPLE_GW"
        state: "absent"

- name: Allow a network
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "acl"
    lookup: ["name"]
    actions:
      add: "addAcl"
      del: "delAcl"
      get: "getAcl"
      search: "searchAcl"
      set: "setAcl"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          name: "routerops_example"
          action: "allow"
          networks: ["10.250.72.0/24"]
          description: "routerops example"

- name: Remove an ACL
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "acl"
    lookup: ["name"]
    actions:
      add: "addAcl"
      del: "delAcl"
      get: "getAcl"
      search: "searchAcl"
      set: "setAcl"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          name: "routerops_example"
        state: "absent"

- name: Forward a domain
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "dot"
    lookup: ["domain", "server"]
    actions:
      add: "addForward"
      del: "delForward"
      get: "getForward"
      search: "searchForward"
      set: "setForward"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          domain: "routerops.test"
          server: "10.250.1.53"
          description: "routerops example"

- name: Remove a forward
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "dot"
    lookup: ["domain", "server"]
    actions:
      add: "addForward"
      del: "delForward"
      get: "getForward"
      search: "searchForward"
      set: "setForward"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          domain: "routerops.test"
          server: "10.250.1.53"
        state: "absent"

- name: Add an alias for the example host
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "alias"
    lookup: ["host", "hostname", "domain"]
    actions:
      add: "addHostAlias"
      del: "delHostAlias"
      get: "getHostAlias"
      search: "searchHostAlias"
      set: "setHostAlias"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          host: "EXAMPLE_HOST_UUID"
          hostname: "rt-example-alias"
          domain: ""
          description: "routerops example"

- name: Remove the alias
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "alias"
    lookup: ["host", "hostname", "domain"]
    actions:
      add: "addHostAlias"
      del: "delHostAlias"
      get: "getHostAlias"
      search: "searchHostAlias"
      set: "setHostAlias"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          host: "EXAMPLE_HOST_UUID"
          hostname: "rt-example-alias"
          domain: ""
        state: "absent"

- name: Add a host override
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "host"
    lookup: ["hostname", "domain", "rr"]
    actions:
      add: "addHostOverride"
      del: "delHostOverride"
      get: "getHostOverride"
      search: "searchHostOverride"
      set: "setHostOverride"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          hostname: "rt-example"
          domain: "routerops.test"
          rr: "A"
          server: "10.250.1.30"
          description: "routerops example"

- name: Remove a host override
  routerops.opnsense.item:
    url: https://fw.example
    api_key: "{{ opnsense_api_key }}"
    api_secret: "{{ opnsense_api_secret }}"
    path: "unbound/settings"
    key: "host"
    lookup: ["hostname", "domain", "rr"]
    actions:
      add: "addHostOverride"
      del: "delHostOverride"
      get: "getHostOverride"
      search: "searchHostOverride"
      set: "setHostOverride"
    apply: "unbound/service/reconfigure"
    items:
      - fields:
          hostname: "rt-example"
          domain: "routerops.test"
          rr: "A"
        state: "absent"
"""
# END EXAMPLES: generated from meta/areas.yml by make docs

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
      choices: [added, updated, deleted, unchanged, queried]
    fields:
      description:
        - The values of O(return_fields) in the form OPNsense stores them, after any write.
        - A select gives its selected key, several keys joined by the field's separator (O(separators), default a comma).
        - Empty when O(return_fields) is empty, for an absent item, for an item added in check mode and for a query that matched nothing.
        - Values of O(secret_fields) are masked.
      type: dict
      version_added: "0.1.0"
  sample: [{"uuid": "5e5b5c62-7a7b-4e0e-9e4c-0a1b2c3d4e5f", "lookup": {"name": "web_servers"}, "action": "added", "fields": {}}]
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

import re

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
    is_container,
    mask_secrets,
    nest_fields,
    normalize,
    secret_values,
    stored_secret_values,
    to_api,
)

MVC_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
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
            state=dict(type="str", choices=["present", "absent", "query"], default="present"),
        ),
    ),
    lookup=dict(type="list", elements="str", default=["description"]),
    actions=dict(type="dict", default={}),
    apply=dict(type="str"),
    purge=dict(type="bool", default=False),
    id_format=dict(type="str", choices=["uuid", "name"], default="uuid"),
    update_write_only=dict(type="str", choices=["on_create", "always"], default="on_create"),
    always_send=dict(type="list", elements="str", default=[]),
    secret_fields=dict(type="list", elements="str", default=[], no_log=False),
    return_fields=dict(type="list", elements="str", default=[]),
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
        self.secrets = set(p["secret_fields"])
        self.returns = p["return_fields"]
        self.actions = dict(DEFAULT_ACTIONS, **p["actions"])
        self.by_name = p["id_format"] == "name"
        self.wrote = False
        self.purged = []
        self.saved = []
        self.before = {}
        self.after = {}

    def fail(self, msg):
        """Fail the task with a message that names the items already saved, and report changed when there are any."""
        if self.saved:
            msg += "; already saved but not applied: %s" % "; ".join(self.saved)
        self.module.fail_json(msg=msg, changed=bool(self.saved))

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
            if uuid and not self.by_name and not MVC_UUID.match(uuid):
                self.fail("search row '%s' is not an MVC item; its fields cannot be read" % uuid)
            if uuid:
                self.fail("item %s disappeared during the run" % uuid)
            self.fail("key '%s' not found in response" % self.key)

    def check_fields(self, current, entry, write_only):
        """Fail on an unknown field or write-only name, else return the changed fields."""
        self.module.no_log_values.update(stored_secret_values(current, self.secrets))
        for name in write_only:
            try:
                get_path(current, name)
            except KeyError:
                self.fail("field '%s' not found in '%s'" % (name, self.key))
        try:
            return field_diff(current, entry["fields"], self.ordered, self.separators, secrets=self.secrets)
        except KeyError as e:
            self.fail("field '%s' not found in '%s'" % (e.args[0], self.key))
        except ValueError as e:
            self.fail(str(e))

    def check_options(self, entries):
        """Fail on bad options before any request: unknown action roles, field overlaps, missing or duplicate lookup values."""
        if self.by_name and self.module.params["purge"]:
            self.fail("purge cannot be combined with id_format name")
        unknown = sorted(set(self.module.params["actions"]) - set(DEFAULT_ACTIONS))
        if unknown:
            self.fail("unknown action role '%s' in actions; roles are search, get, add, set, del" % "', '".join(unknown))
        for entry in entries:
            self.module.no_log_values.update(secret_values(flatten(entry["fields"]), self.secrets))
            nested = sorted(s for s in self.secrets if any(n.startswith(s + ".") for n in flatten(entry["fields"])))
            if nested:
                self.fail("secret field '%s' holds nested fields; name each nested secret field" % "', '".join(nested))
            try:
                check_names(entry["fields"], flatten(entry["write_only"]), [], {})
            except ValueError as e:
                self.fail(str(e))
            missing = [name for name in self.lookup if name not in flatten(entry["fields"])]
            if missing:
                self.fail("lookup field '%s' missing from the fields of an item" % "', '".join(missing))
            unsent = [name for name in self.module.params["always_send"] if name not in flatten(entry["fields"])]
            if unsent and entry["state"] == "present":
                self.fail("always_send field '%s' missing from the fields of an item" % "', '".join(unsent))
        for i, entry in enumerate(entries):
            wanted = self.wanted_lookup(entry)
            for other in entries[i + 1:]:
                stored = {name: to_api(v, self.sep(name)) for name, v in self.wanted_lookup(other).items()}
                if self.matches(stored, wanted):
                    self.fail("duplicate lookup value '%s' in items" % self.label(wanted))

    def is_item(self, row):
        """Tell whether a search row is an item of the area: a UUID row, or with id_format name any row with a uuid."""
        if not isinstance(row, dict):
            return False
        uuid = row.get("uuid")
        if self.by_name:
            return isinstance(uuid, str) and uuid != ""
        return bool(MVC_UUID.match(str(uuid or "")))

    def item_rows(self, rows):
        """Return the search rows that are items, leaving out rows such as automatic rules whose uuid is not a UUID."""
        return [row for row in rows if self.is_item(row)]

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
                if not field_diff(row, wanted, self.ordered, self.separators, secrets=self.secrets):
                    found.append(row)
            except ValueError as e:
                self.fail("lookup %s" % e)
        if len(found) > 1:
            self.fail("lookup '%s' matches several items: %s" % (self.label(wanted), ", ".join(r["uuid"] for r in found)))
        return found[0] if found else None

    def read(self, uuid):
        """Read one item by its UUID and return its fields."""
        return self.section(self.client.get("%s/%s/%s" % (self.path, self.actions["get"], uuid)), uuid)

    def returned(self, current, entry=None, changes=None):
        """Return the return_fields of an item in the form OPNsense stores them, with written values applied and secrets masked."""
        values = {name: normalize(get_path(current, name), "", separator=self.sep(name)) for name in self.returns}
        if entry is not None and changes:
            flat = flatten(entry["fields"])
            values.update({name: to_api(flat[name], self.sep(name)) for name in self.returns if name in changes})
        self.module.no_log_values.update(secret_values(values, self.secrets))
        return mask_secrets(values, self.secrets)

    def update(self, entry, uuid, label, changes):
        """Write the changed fields and write-only values of a matched item; return its action."""
        write_only = flatten(entry["write_only"])
        if not changes and not (write_only and self.module.params["update_write_only"] == "always"):
            return "unchanged"
        flat = flatten(entry["fields"])
        values = {name: flat[name] for name in changes}
        values.update({name: flat[name] for name in self.module.params["always_send"]})
        values.update(write_only)
        if not self.module.check_mode:
            require_saved(self.client.post("%s/%s/%s" % (self.path, self.actions["set"], uuid), self.payload(values)))
            self.saved.append(label)
        self.wrote = True
        if changes:
            self.module.no_log_values.update(secret_values({name: change[0] for name, change in changes.items()}, self.secrets))
            self.before[label] = mask_secrets({name: change[0] for name, change in changes.items()}, self.secrets)
            self.after[label] = mask_secrets({name: change[1] for name, change in changes.items()}, self.secrets)
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
        self.after[label] = mask_secrets(entry["fields"], self.secrets)
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
        rows = self.item_rows(search["rows"])
        other_rows = [
            row for row in search["rows"]
            if isinstance(row, dict) and not self.is_item(row) and all(name in row for name in self.lookup)
        ]
        matched = [
            (self.find(rows, entry) or self.find(other_rows, entry)) if entry["state"] == "query" else self.find(rows, entry)
            for entry in entries
        ]
        to_add = [entry for entry, row in zip(entries, matched) if row is None and entry["state"] == "present"]
        if to_add or self.returns:
            template = self.section(self.client.get("%s/%s" % (self.path, self.actions["get"])))
            for name in self.returns:
                try:
                    value = get_path(template, name)
                except KeyError:
                    self.fail("return field '%s' not found in '%s'" % (name, self.key))
                if is_container(value):
                    self.fail("return field '%s' holds nested fields; name each field, for example '%s.%s'" % (name, name, sorted(value)[0]))
            for entry in to_add:
                self.check_fields(template, entry, flatten(entry["write_only"]))
        currents = [
            self.read(row["uuid"])
            if row is not None and (entry["state"] == "present" or (entry["state"] == "query" and self.returns))
            else None
            for entry, row in zip(entries, matched)
        ]
        changes = [
            self.check_fields(current, entry, flatten(entry["write_only"])) if row is not None and entry["state"] == "present" else None
            for entry, row, current in zip(entries, matched, currents)
        ]
        results = []
        for entry, row, current, change in zip(entries, matched, currents, changes):
            wanted = self.wanted_lookup(entry)
            label = self.label(wanted)
            fields = {}
            if entry["state"] == "query":
                uuid, action = (row["uuid"] if row is not None else None), "queried"
                if row is not None:
                    fields = self.returned(current)
            elif entry["state"] == "absent":
                uuid, action = None, "unchanged"
                if row is not None:
                    uuid = row["uuid"]
                    if self.delete(uuid, label, wanted):
                        action = "deleted"
            elif row is None:
                uuid, action = self.add(entry, label), "added"
                if uuid and self.returns:
                    fields = self.returned(self.read(uuid))
            else:
                uuid = row["uuid"]
                action = self.update(entry, uuid, label, change)
                fields = self.returned(current, entry, change)
            results.append({"uuid": uuid, "lookup": wanted, "action": action, "fields": fields})
        if p["purge"]:
            listed = set(row["uuid"] for row in matched if row is not None)
            for row in rows:
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
        module.fail_json(msg=msg, validations=e.validations, changed=bool(run.saved))
    module.exit_json(changed=run.wrote, outcomes=results, purged=run.purged, diff=dict(before=run.before, after=run.after))


if __name__ == "__main__":
    main()
