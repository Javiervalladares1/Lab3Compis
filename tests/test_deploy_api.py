import unittest
from unittest import mock

import _support
_support.add_program_to_path()

import requests
import deploy_api
from deploy_api import GitHubClient, VercelClient, DeploymentError

SECRET = "super-secret-token-value"


def fake_response(status, json_data=None, text="", headers=None):
    resp = mock.Mock()
    resp.status_code = status
    resp.headers = headers or {}
    resp.text = text
    if json_data is None:
        resp.json.side_effect = ValueError("no json")
    else:
        resp.json.return_value = json_data
    return resp


class TestGitHubClient(unittest.TestCase):
    def test_create_repo_success(self):
        gh = GitHubClient(SECRET)
        resp = fake_response(201, {
            "full_name": "user/repo", "html_url": "https://github.com/user/repo"
        })
        with mock.patch.object(deploy_api.requests, "request", return_value=resp):
            full_name, url = gh.create_repo("repo", "desc")
        self.assertEqual(full_name, "user/repo")
        self.assertEqual(url, "https://github.com/user/repo")

    def test_create_repo_already_exists_is_reused(self):
        gh = GitHubClient(SECRET)
        exists = fake_response(422, {"message": "name already exists on this account"})
        user = fake_response(200, {"login": "user"})
        with mock.patch.object(deploy_api.requests, "request",
                               side_effect=[exists, user]):
            full_name, url = gh.create_repo("repo", "desc")
        self.assertEqual(full_name, "user/repo")

    def test_create_repo_bad_token_raises_clean_error(self):
        gh = GitHubClient(SECRET)
        resp = fake_response(401, {"message": "Bad credentials"})
        with mock.patch.object(deploy_api.requests, "request", return_value=resp):
            with self.assertRaises(DeploymentError) as ctx:
                gh.create_repo("repo", "desc")
        message = str(ctx.exception)
        self.assertIn("401", message)
        self.assertNotIn(SECRET, message)  # token must never leak

    def test_network_error_becomes_deployment_error(self):
        gh = GitHubClient(SECRET)
        with mock.patch.object(deploy_api.requests, "request",
                               side_effect=requests.RequestException("boom")):
            with self.assertRaises(DeploymentError) as ctx:
                gh.create_repo("repo", "desc")
        self.assertIn("network error", str(ctx.exception))

    def test_put_file_creates_new_file(self):
        gh = GitHubClient(SECRET)
        missing = fake_response(404, {"message": "Not Found"})
        created = fake_response(201, {"content": {"html_url": "https://gh/blob"}})
        with mock.patch.object(deploy_api.requests, "request",
                               side_effect=[missing, created]) as req:
            url = gh.put_file("user/repo", "index.html", "<html></html>", "msg")
        self.assertEqual(url, "https://gh/blob")
        # New file -> no sha in the PUT payload.
        put_kwargs = req.call_args_list[1].kwargs
        self.assertNotIn("sha", put_kwargs["json"])

    def test_put_file_updates_existing_file_with_sha(self):
        gh = GitHubClient(SECRET)
        existing = fake_response(200, {"sha": "abc123"})
        updated = fake_response(200, {"content": {"html_url": "https://gh/blob"}})
        with mock.patch.object(deploy_api.requests, "request",
                               side_effect=[existing, updated]) as req:
            gh.put_file("user/repo", "index.html", "<html></html>", "msg")
        put_kwargs = req.call_args_list[1].kwargs
        self.assertEqual(put_kwargs["json"]["sha"], "abc123")


class TestVercelClient(unittest.TestCase):
    def test_deploy_success_returns_https_url(self):
        vc = VercelClient(SECRET)
        resp = fake_response(200, {"url": "my-app-abc.vercel.app"})
        with mock.patch.object(deploy_api.requests, "post", return_value=resp):
            url = vc.deploy("my-app", "<html></html>")
        self.assertEqual(url, "https://my-app-abc.vercel.app")

    def test_deploy_auth_error_is_clean_and_hides_token(self):
        vc = VercelClient(SECRET)
        resp = fake_response(403, {"error": {"message": "Not authorized"}})
        with mock.patch.object(deploy_api.requests, "post", return_value=resp):
            with self.assertRaises(DeploymentError) as ctx:
                vc.deploy("my-app", "<html></html>")
        message = str(ctx.exception)
        self.assertIn("403", message)
        self.assertNotIn(SECRET, message)

    def test_deploy_without_url_raises(self):
        vc = VercelClient(SECRET)
        resp = fake_response(200, {})
        with mock.patch.object(deploy_api.requests, "post", return_value=resp):
            with self.assertRaises(DeploymentError):
                vc.deploy("my-app", "<html></html>")


if __name__ == "__main__":
    unittest.main()
