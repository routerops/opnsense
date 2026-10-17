# routerops.opnsense

Ansible collection with two generic modules for the OPNsense MVC API: `routerops.opnsense.settings` for settings singletons and `routerops.opnsense.item` for items. The caller names the API path and the fields, so a field change in a new OPNsense release needs a playbook change, not a new collection release.

Status: in development, not released yet.

## Licence

`plugins/module_utils/` is BSD-2-Clause, everything else GPL-3.0-or-later; see `LICENSES/`.
