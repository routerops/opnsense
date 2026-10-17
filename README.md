# routerops.opnsense

Ansible collection with two generic modules for the OPNsense MVC API: `routerops.opnsense.settings` for settings singletons and `routerops.opnsense.item` for items. The caller names the API path and the fields, so a field change in a new OPNsense release needs a playbook change, not a new collection release.

Status: in development, not released yet.

## Requirements and versions

The collection needs ansible-core 2.20 or later; CI tests 2.20 and 2.21. Releases follow SemVer: a patch release only fixes bugs, a minor release may add features and deprecations, and only a major release breaks compatibility. Until 1.0 a breaking change bumps the minor version.

## Licence

`plugins/module_utils/` is BSD-2-Clause, everything else GPL-3.0-or-later; see `LICENSES/`.
