# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json

import pytest

from ansible.module_utils.testing import patch_module_args


class FakeClient:
    def __init__(self, get_response, post_responses=None, get_by_path=None):
        self.get_response = get_response
        self.post_responses = post_responses or {}
        self.get_by_path = get_by_path or {}
        self.calls = []

    def get(self, path):
        self.calls.append(("GET", path, None))
        return self.get_by_path.get(path, self.get_response)

    def post(self, path, payload=None):
        self.calls.append(("POST", path, payload))
        response = self.post_responses.get(path, {"result": "saved", "status": "ok"})
        if isinstance(response, list):
            return response.pop(0)
        return response


@pytest.fixture
def run_module(monkeypatch, capsys):
    def run(module, args, fake, check_mode=False):
        monkeypatch.setattr(module, "client_from_params", lambda params: fake)
        full = dict(args, _ansible_check_mode=check_mode, _ansible_diff=True)
        with patch_module_args(full):
            with pytest.raises(SystemExit):
                module.main()
        return json.loads(capsys.readouterr().out)

    return run
