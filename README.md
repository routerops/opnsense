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
| [dnsmasq](docs/areas/dnsmasq.md) | [Dnsmasq host](docs/areas/dnsmasq.md#dnsmasq-host) |
| [firewall](docs/areas/firewall.md) | [Firewall alias](docs/areas/firewall.md#firewall-alias), [Firewall destination NAT](docs/areas/firewall.md#firewall-destination-nat), [Firewall filter rule](docs/areas/firewall.md#firewall-filter-rule), [Firewall one-to-one NAT](docs/areas/firewall.md#firewall-one-to-one-nat), [Firewall source NAT rule](docs/areas/firewall.md#firewall-source-nat-rule), [Firewall outbound NAT mode](docs/areas/firewall.md#firewall-outbound-nat-mode) |
| [nodeexporter](docs/areas/nodeexporter.md) | [node_exporter general](docs/areas/nodeexporter.md#node_exporter-general) |
| [routes](docs/areas/routes.md) | [Static route](docs/areas/routes.md#static-route) |
| [routing](docs/areas/routing.md) | [Gateway](docs/areas/routing.md#gateway) |

All item types with plugin, version and stage: [docs/areas/README.md](docs/areas/README.md).
<!-- END areas: generated from meta/areas.yml by make docs -->

## Licence

`plugins/module_utils/` is BSD-2-Clause, everything else GPL-3.0-or-later; see `LICENSES/`.
