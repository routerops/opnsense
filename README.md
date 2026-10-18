# routerops.opnsense

Ansible collection with two generic modules for the OPNsense MVC API: `routerops.opnsense.settings` for settings singletons and `routerops.opnsense.item` for items. The caller names the API path and the fields, so a field change in a new OPNsense release needs a playbook change, not a new collection release.

Status: in development, not released yet.

## Requirements and versions

The collection needs ansible-core 2.20 or later; CI tests 2.20 and 2.21. Releases follow SemVer: a patch release only fixes bugs, a minor release may add features and deprecations, and only a major release breaks compatibility. Until 1.0 a breaking change bumps the minor version.

## Areas

Each area page lists the path, key, actions, lookup and apply path a call needs, the fields the OPNsense model accepts, and example tasks that run in the integration tests.

<!-- BEGIN areas: generated from meta/areas.yml by make docs -->
| Area | Item types |
|---|---|
| [dnsmasq](docs/areas/dnsmasq.md) | [Dnsmasq domain override](docs/areas/dnsmasq.md#dnsmasq-domain-override), [Dnsmasq general](docs/areas/dnsmasq.md#dnsmasq-general), [Dnsmasq host](docs/areas/dnsmasq.md#dnsmasq-host), [Dnsmasq DHCP option](docs/areas/dnsmasq.md#dnsmasq-dhcp-option), [Dnsmasq DHCP range](docs/areas/dnsmasq.md#dnsmasq-dhcp-range) |
| [firewall](docs/areas/firewall.md) | [Firewall alias](docs/areas/firewall.md#firewall-alias), [Firewall destination NAT](docs/areas/firewall.md#firewall-destination-nat), [Firewall filter rule](docs/areas/firewall.md#firewall-filter-rule), [Firewall one-to-one NAT](docs/areas/firewall.md#firewall-one-to-one-nat), [Firewall source NAT rule](docs/areas/firewall.md#firewall-source-nat-rule), [Firewall outbound NAT mode](docs/areas/firewall.md#firewall-outbound-nat-mode) |
| [interfaces](docs/areas/interfaces.md) | [Assignment](docs/areas/interfaces.md#assignment), [Virtual IP](docs/areas/interfaces.md#virtual-ip), [VLAN](docs/areas/interfaces.md#vlan) |
| [kea](docs/areas/kea.md) | [Kea DHCPv4 general](docs/areas/kea.md#kea-dhcpv4-general), [DHCPv4 reservation](docs/areas/kea.md#dhcpv4-reservation), [DHCPv4 subnet](docs/areas/kea.md#dhcpv4-subnet) |
| [nodeexporter](docs/areas/nodeexporter.md) | [node_exporter general](docs/areas/nodeexporter.md#node_exporter-general) |
| [routes](docs/areas/routes.md) | [Static route](docs/areas/routes.md#static-route) |
| [routing](docs/areas/routing.md) | [Gateway](docs/areas/routing.md#gateway) |
| [unbound](docs/areas/unbound.md) | [ACL](docs/areas/unbound.md#acl), [Query forward](docs/areas/unbound.md#query-forward), [Unbound general](docs/areas/unbound.md#unbound-general), [Host alias](docs/areas/unbound.md#host-alias), [Host override](docs/areas/unbound.md#host-override) |

All item types with plugin, version and stage: [docs/areas/README.md](docs/areas/README.md).
<!-- END areas: generated from meta/areas.yml by make docs -->

## Licence

`plugins/module_utils/` is BSD-2-Clause, everything else GPL-3.0-or-later; see `LICENSES/`.
