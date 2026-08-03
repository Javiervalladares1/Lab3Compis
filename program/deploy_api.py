"""Thin REST clients for the GitHub and Vercel APIs.

This is the "back end" of the compiler: once HTML has been generated it is
published by talking directly to the GitHub Contents API and the Vercel
Deployments API over HTTPS (no ``git`` and no Vercel CLI involved).

Design goals:
  * credentials are read from the caller, never hard-coded;
  * tokens are never printed or embedded in error messages;
  * every predictable HTTP/network failure becomes a clean DeploymentError
    instead of a raw traceback.
"""

import base64

import requests

GITHUB_API = "https://api.github.com"
VERCEL_API = "https://api.vercel.com"
TIMEOUT = 30  # seconds


class DeploymentError(Exception):
    """A GitHub or Vercel operation failed in a way we can explain to the user."""


def _response_message(resp):
    """Best-effort human-readable message from an API error response.

    Never returns the request token; only reads the response body.
    """
    try:
        data = resp.json()
    except ValueError:
        return (resp.text or "").strip()[:200] or "no response body"
    if isinstance(data, dict):
        if isinstance(data.get("error"), dict):  # Vercel shape
            return data["error"].get("message", "unknown error")
        if data.get("message"):  # GitHub shape
            return data["message"]
    return str(data)[:200]


class GitHubClient:
    def __init__(self, token):
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # -- low-level helpers ------------------------------------------------
    def _request(self, method, path, **kwargs):
        try:
            return requests.request(
                method, f"{GITHUB_API}{path}", headers=self._headers,
                timeout=TIMEOUT, **kwargs
            )
        except requests.RequestException as exc:
            raise DeploymentError(f"network error contacting GitHub: {exc}") from exc

    def _fail(self, resp, action):
        status = resp.status_code
        msg = _response_message(resp)
        if status == 401:
            hint = "authentication failed — check GITHUB_TOKEN"
        elif status == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            hint = "rate limit exceeded — try again later"
        elif status == 403:
            hint = "permission denied — the token needs the 'repo' scope"
        elif status == 422:
            hint = "validation error"
        else:
            hint = "unexpected response"
        raise DeploymentError(f"GitHub {action} failed ({status}, {hint}): {msg}")

    # -- public API -------------------------------------------------------
    def get_login(self):
        resp = self._request("GET", "/user")
        if resp.status_code != 200:
            self._fail(resp, "authentication")
        return resp.json()["login"]

    def create_repo(self, name, description):
        """Create a public repo, or reuse it if it already exists.

        Returns (full_name, html_url).
        """
        resp = self._request(
            "POST", "/user/repos",
            json={
                "name": name,
                "description": description,
                "private": False,
                "auto_init": False,
            },
        )
        if resp.status_code == 201:
            repo = resp.json()
            return repo["full_name"], repo["html_url"]

        # 422 with this message means the repo already exists on the account.
        if resp.status_code == 422 and "already exists" in _response_message(resp).lower():
            login = self.get_login()
            full_name = f"{login}/{name}"
            print(f"[i] Repo '{full_name}' already exists — reusing it.")
            return full_name, f"https://github.com/{full_name}"

        self._fail(resp, "repo creation")

    def _get_file_sha(self, full_name, path):
        """Return the blob sha of an existing file, or None if it does not exist."""
        resp = self._request("GET", f"/repos/{full_name}/contents/{path}")
        if resp.status_code == 200:
            return resp.json().get("sha")
        if resp.status_code == 404:
            return None
        self._fail(resp, "file lookup")

    def put_file(self, full_name, path, text, message):
        """Create or update a file via the Contents API (one commit)."""
        payload = {
            "message": message,
            "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        }
        sha = self._get_file_sha(full_name, path)
        if sha:  # updating an existing file requires its current sha
            payload["sha"] = sha
        resp = self._request(
            "PUT", f"/repos/{full_name}/contents/{path}", json=payload
        )
        if resp.status_code not in (200, 201):
            self._fail(resp, "file upload")
        return resp.json()["content"]["html_url"]


class VercelClient:
    def __init__(self, token):
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def deploy(self, name, text):
        """Create a production deployment from a single in-memory HTML file.

        Returns the full ``https://...`` URL of the deployment.
        """
        payload = {
            "name": name,
            "files": [{"file": "index.html", "data": text}],
            "projectSettings": {"framework": None},
            "target": "production",
        }
        try:
            resp = requests.post(
                f"{VERCEL_API}/v13/deployments",
                headers=self._headers, json=payload, timeout=TIMEOUT,
            )
        except requests.RequestException as exc:
            raise DeploymentError(f"network error contacting Vercel: {exc}") from exc

        if resp.status_code not in (200, 201):
            status = resp.status_code
            msg = _response_message(resp)
            if status in (401, 403):
                hint = "authentication failed — check VERCEL_TOKEN"
            elif status in (400, 422):
                hint = "validation error"
            else:
                hint = "unexpected response"
            raise DeploymentError(f"Vercel deployment failed ({status}, {hint}): {msg}")

        data = resp.json()
        url = data.get("url")
        if not url:
            aliases = data.get("alias") or []
            url = aliases[0] if aliases else None
        if not url:
            raise DeploymentError(
                "Vercel accepted the deployment but returned no URL "
                "(check your Vercel dashboard)"
            )
        return url if url.startswith("http") else f"https://{url}"
