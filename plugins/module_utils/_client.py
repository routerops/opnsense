# SPDX-FileCopyrightText: routerops.opnsense contributors
# SPDX-License-Identifier: BSD-2-Clause
# Internal to routerops.opnsense, not a public API; it may change in any release.
# JSON client for the OPNsense API and checks of its write, delete and action results.

from __future__ import annotations

import http.client
import json
import time
import urllib.error

from ansible.module_utils.urls import open_url

GET_ATTEMPTS = 3
RETRY_DELAY = 1


class OPNsenseError(Exception):
    """An API request or result OPNsense rejected, with its validations and HTTP status when known."""
    def __init__(self, msg, validations=None, status=None):
        """Store the message, the validations map and the HTTP status."""
        super().__init__(msg)
        self.msg = msg
        self.validations = validations
        self.status = status


class OPNsenseClient:
    """Minimal JSON client for the OPNsense API with basic auth."""
    def __init__(self, url, api_key, api_secret, validate_certs=True, timeout=30):
        """Keep the API base URL, the credentials and the TLS and timeout settings."""
        self.base = url.rstrip("/") + "/api/"
        self.api_key = api_key
        self.api_secret = api_secret
        self.validate_certs = validate_certs
        self.timeout = timeout

    def get(self, path):
        """GET a path below /api/ and return the decoded JSON; retry connection errors and HTTP 5xx."""
        for attempt in range(1, GET_ATTEMPTS + 1):
            try:
                return self._request("GET", path)
            except OPNsenseError as e:
                if not self._retryable(e) or attempt == GET_ATTEMPTS:
                    raise
            time.sleep(RETRY_DELAY)

    def post(self, path, payload=None):
        """POST a JSON payload (an empty object by default) to a path below /api/; never retried."""
        return self._request("POST", path, payload if payload is not None else {})

    @staticmethod
    def _retryable(error):
        """Tell whether a failed GET may be retried: no HTTP status or a 5xx status."""
        return error.status is None or error.status >= 500

    def _request(self, method, path, payload=None):
        """Send one request and return the decoded JSON, turning every failure into an OPNsenseError."""
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
            msg = "%s %s failed with HTTP %s" % (method, url, e.code)
            detail = _error_message(e)
            if detail:
                msg += ": %s" % detail
            raise OPNsenseError(msg, status=e.code)
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
    """Build the error for a missing endpoint, naming the path."""
    return OPNsenseError("endpoint '%s' not found; the area or its plugin may be missing" % path, status=404)


def _error_message(http_error):
    """Return the errorMessage from an HTTP error's JSON body, or None when the body has none."""
    try:
        data = json.loads(http_error.read())
    except (ValueError, OSError, http.client.HTTPException):
        return None
    if isinstance(data, dict):
        return data.get("errorMessage")
    return None


def require_deleted(response):
    """Raise unless a delete answered 'deleted' or 'not found'."""
    if not isinstance(response, dict):
        raise OPNsenseError("unexpected delete response: %r" % (response,))
    if response.get("result") not in ("deleted", "not found"):
        raise OPNsenseError("delete rejected by OPNsense: %s" % response.get("result"))


def require_saved(response):
    """Raise with the validations unless a write answered 'saved'."""
    if not isinstance(response, dict):
        raise OPNsenseError("unexpected write response: %r" % (response,))
    if response.get("result") != "saved":
        raise OPNsenseError("write rejected by OPNsense: %s" % response.get("result"), validations=response.get("validations"))


def require_ok(response):
    """Raise unless an action answered status 'ok', ignoring case and surrounding whitespace."""
    if not isinstance(response, dict):
        raise OPNsenseError("unexpected action response: %r" % (response,))
    if str(response.get("status", "")).strip().lower() != "ok":
        raise OPNsenseError("action failed: %s %s" % (response.get("status"), response.get("status_msg", "")))
