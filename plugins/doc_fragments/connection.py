# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# Documentation fragment for the connection options.

from __future__ import annotations


class ModuleDocFragment:
    """Connection options shared by every module of the collection."""
    DOCUMENTATION = r"""
options:
  url:
    description: Base URL of the OPNsense web interface, for example C(https://fw.example). Falls back to the E(OPNSENSE_URL) environment variable.
    type: str
    required: true
  api_key:
    description: API key of the OPNsense user. Falls back to the E(OPNSENSE_API_KEY) environment variable.
    type: str
    required: true
  api_secret:
    description: API secret of the OPNsense user. Falls back to the E(OPNSENSE_API_SECRET) environment variable.
    type: str
    required: true
  validate_certs:
    description:
      - Verify the TLS certificate. Set to V(false) only for a test system with a self-signed certificate.
      - Falls back to the E(OPNSENSE_VALIDATE_CERTS) environment variable.
    type: bool
    default: true
  timeout:
    description: HTTP timeout in seconds.
    type: int
    default: 30
"""
