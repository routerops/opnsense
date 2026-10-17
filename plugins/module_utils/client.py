# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: BSD-2-Clause

from __future__ import annotations

import http.client
import json
import time
import urllib.error

from ansible.module_utils.urls import open_url

GET_ATTEMPTS = 3
RETRY_DELAY = 1


class OPNsenseError(Exception):
    def __init__(self, msg, validations=None, status=None):
        super().__init__(msg)
        self.msg = msg
        self.validations = validations
        self.status = status


class OPNsenseClient:
    def __init__(self, url, api_key, api_secret, validate_certs=True, timeout=30):
        self.base = url.rstrip("/") + "/api/"
        self.api_key = api_key
        self.api_secret = api_secret
        self.validate_certs = validate_certs
        self.timeout = timeout

    def get(self, path):
        for attempt in range(1, GET_ATTEMPTS + 1):
            try:
                return self._request("GET", path)
            except OPNsenseError as e:
                if not self._retryable(e) or attempt == GET_ATTEMPTS:
                    raise
            time.sleep(RETRY_DELAY)

    def post(self, path, payload=None):
        return self._request("POST", path, payload if payload is not None else {})

    @staticmethod
    def _retryable(error):
        return error.status is None or error.status >= 500

    def _request(self, method, path, payload=None):
        url = self.base + path
        kwargs = dict(
            method=method,
            url_username=self.api_key,
            url_password=self.api_secret,
            force_basic_auth=True,
            validate_certs=self.validate_certs,
            timeout=self.timeout,
        )
        if payload is not None:
            kwargs["data"] = json.dumps(payload)
            kwargs["headers"] = {"Content-Type": "application/json"}
        try:
            body = open_url(url, **kwargs).read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise _not_found(path)
            raise OPNsenseError("%s %s failed with HTTP %s" % (method, url, e.code), status=e.code)
        except urllib.error.URLError as e:
            raise OPNsenseError("%s %s failed: %s" % (method, url, e.reason))
        except (OSError, http.client.HTTPException) as e:
            raise OPNsenseError("%s %s failed: %s" % (method, url, e))
        try:
            data = json.loads(body)
        except ValueError:
            raise OPNsenseError("%s %s did not return JSON" % (method, url), status=0)
        if isinstance(data, dict) and data.get("errorMessage") == "Endpoint not found":
            raise _not_found(path)
        return data


def _not_found(path):
    return OPNsenseError("endpoint '%s' not found; the area or its plugin may be missing" % path, status=404)


def require_saved(response):
    if not isinstance(response, dict):
        raise OPNsenseError("unexpected write response: %r" % (response,))
    if response.get("result") != "saved":
        raise OPNsenseError("write rejected by OPNsense: %s" % response.get("result"), validations=response.get("validations"))


def require_ok(response):
    if not isinstance(response, dict):
        raise OPNsenseError("unexpected action response: %r" % (response,))
    if str(response.get("status", "")).strip().lower() != "ok":
        raise OPNsenseError("action failed: %s %s" % (response.get("status"), response.get("status_msg", "")))
