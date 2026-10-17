# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# Documentation fragment for the field options shared by item and settings.

from __future__ import annotations


class ModuleDocFragment:
    """Field options shared by the item and settings modules."""
    DOCUMENTATION = r"""
options:
  secret_fields:
    description:
      - Fields that hold a secret OPNsense returns on read, such as a WireGuard private key or pre-shared key.
      - They are compared and written like any other field, but their values are masked in the diff, the return values and error messages.
      - Ansible logs the module arguments, these values included, to the syslog of the host the module runs on.
      - Set C(no_log) on the task or enable C(no_target_syslog) to keep them out of that log.
      - For a secret OPNsense never returns, such as a user password, use C(write_only) instead.
    type: list
    elements: str
    default: []
    version_added: "0.1.0"
"""
