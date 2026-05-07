"""
integration_connectors.py — lightweight connectivity testers for each integration type.

Each tester receives the parsed config dict and returns:
  {"success": bool, "message": str, "details": dict}

Sensitive credentials are passed in but never logged or returned to the caller.
"""

import smtplib
import ssl
from typing import Any, Dict

import httpx


def test_integration_connectivity(integration_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    testers = {
        "email": _test_email,
        "jira": _test_jira,
        "google_calendar": _test_google_calendar,
        "slack": _test_slack,
        "microsoft_teams": _test_microsoft_teams,
        "github": _test_github,
        "notion": _test_notion,
        "custom": _test_custom,
    }
    tester = testers.get(integration_type)
    if not tester:
        return {"success": False, "message": f"Unknown integration type: {integration_type}", "details": {}}
    try:
        return tester(config)
    except Exception as exc:
        return {"success": False, "message": str(exc), "details": {}}


# ---------------------------------------------------------------------------
# Email (SMTP)
# ---------------------------------------------------------------------------

def _test_email(config: Dict[str, Any]) -> Dict[str, Any]:
    host = config.get("smtp_host", "")
    port = int(config.get("smtp_port", 587))
    username = config.get("username", "")
    password = config.get("password", "")
    use_tls = config.get("use_tls", True)

    if not host or not username or not password:
        return {"success": False, "message": "smtp_host, username, and password are required.", "details": {}}

    ctx = ssl.create_default_context()
    try:
        if use_tls:
            with smtplib.SMTP(host, port, timeout=10) as server:
                server.ehlo()
                server.starttls(context=ctx)
                server.login(username, password)
        else:
            with smtplib.SMTP_SSL(host, port, context=ctx, timeout=10) as server:
                server.login(username, password)
        return {"success": True, "message": "SMTP connection successful.", "details": {"host": host, "port": port}}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "SMTP authentication failed. Check username/password.", "details": {}}
    except (smtplib.SMTPConnectError, OSError) as exc:
        return {"success": False, "message": f"Could not connect to {host}:{port} — {exc}", "details": {}}


# ---------------------------------------------------------------------------
# Jira
# ---------------------------------------------------------------------------

def _test_jira(config: Dict[str, Any]) -> Dict[str, Any]:
    base_url = config.get("base_url", "").rstrip("/")
    email = config.get("email", "")
    api_token = config.get("api_token", "")

    if not base_url or not email or not api_token:
        return {"success": False, "message": "base_url, email, and api_token are required.", "details": {}}

    url = f"{base_url}/rest/api/3/myself"
    try:
        response = httpx.get(url, auth=(email, api_token), timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "message": f"Connected as {data.get('displayName', email)}.",
                "details": {"account_id": data.get("accountId")},
            }
        return {
            "success": False,
            "message": f"Jira returned HTTP {response.status_code}.",
            "details": {},
        }
    except httpx.ConnectError as exc:
        return {"success": False, "message": f"Cannot reach Jira at {base_url}: {exc}", "details": {}}


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

def _test_google_calendar(config: Dict[str, Any]) -> Dict[str, Any]:
    api_key = config.get("api_key", "")
    if not api_key:
        return {
            "success": False,
            "message": "api_key is required (or configure OAuth service account).",
            "details": {},
        }

    url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    try:
        response = httpx.get(url, params={"key": api_key}, timeout=10)
        if response.status_code in (200, 401):
            # 401 means the key is recognized but scoped differently — counts as reachable
            return {
                "success": response.status_code == 200,
                "message": "Google Calendar API reachable." if response.status_code == 200 else "API key valid but auth scope insufficient.",
                "details": {},
            }
        return {"success": False, "message": f"Google Calendar returned HTTP {response.status_code}.", "details": {}}
    except httpx.ConnectError as exc:
        return {"success": False, "message": f"Cannot reach Google Calendar API: {exc}", "details": {}}


# ---------------------------------------------------------------------------
# Slack
# ---------------------------------------------------------------------------

def _test_slack(config: Dict[str, Any]) -> Dict[str, Any]:
    webhook_url = config.get("webhook_url", "")
    bot_token = config.get("bot_token", "")

    if bot_token:
        try:
            response = httpx.get(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {bot_token}"},
                timeout=10,
            )
            data = response.json()
            if data.get("ok"):
                return {
                    "success": True,
                    "message": f"Connected to Slack as {data.get('user')} in {data.get('team')}.",
                    "details": {"team": data.get("team"), "user": data.get("user")},
                }
            return {"success": False, "message": data.get("error", "Slack auth failed."), "details": {}}
        except httpx.ConnectError as exc:
            return {"success": False, "message": f"Cannot reach Slack: {exc}", "details": {}}

    if webhook_url:
        try:
            response = httpx.post(webhook_url, json={"text": "VaultMind connectivity test."}, timeout=10)
            if response.status_code == 200:
                return {"success": True, "message": "Slack webhook is reachable.", "details": {}}
            return {"success": False, "message": f"Slack webhook returned HTTP {response.status_code}.", "details": {}}
        except httpx.ConnectError as exc:
            return {"success": False, "message": f"Cannot reach Slack webhook: {exc}", "details": {}}

    return {"success": False, "message": "Either bot_token or webhook_url is required.", "details": {}}


# ---------------------------------------------------------------------------
# Microsoft Teams
# ---------------------------------------------------------------------------

def _test_microsoft_teams(config: Dict[str, Any]) -> Dict[str, Any]:
    webhook_url = config.get("webhook_url", "")
    if not webhook_url:
        return {"success": False, "message": "webhook_url is required.", "details": {}}

    try:
        response = httpx.post(
            webhook_url,
            json={"text": "VaultMind connectivity test."},
            timeout=10,
        )
        if response.status_code in (200, 202):
            return {"success": True, "message": "Microsoft Teams webhook is reachable.", "details": {}}
        return {"success": False, "message": f"Teams webhook returned HTTP {response.status_code}.", "details": {}}
    except httpx.ConnectError as exc:
        return {"success": False, "message": f"Cannot reach Teams webhook: {exc}", "details": {}}


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def _test_github(config: Dict[str, Any]) -> Dict[str, Any]:
    token = config.get("token", "")
    if not token:
        return {"success": False, "message": "token (personal access token or GitHub App token) is required.", "details": {}}

    try:
        response = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "message": f"Connected to GitHub as {data.get('login')}.",
                "details": {"login": data.get("login"), "id": data.get("id")},
            }
        return {"success": False, "message": f"GitHub returned HTTP {response.status_code}.", "details": {}}
    except httpx.ConnectError as exc:
        return {"success": False, "message": f"Cannot reach GitHub API: {exc}", "details": {}}


# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------

def _test_notion(config: Dict[str, Any]) -> Dict[str, Any]:
    token = config.get("token", "")
    if not token:
        return {"success": False, "message": "token (Notion integration token) is required.", "details": {}}

    try:
        response = httpx.get(
            "https://api.notion.com/v1/users/me",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28",
            },
            timeout=10,
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "message": f"Connected to Notion as {data.get('name', 'unknown')}.",
                "details": {"type": data.get("type")},
            }
        return {"success": False, "message": f"Notion returned HTTP {response.status_code}.", "details": {}}
    except httpx.ConnectError as exc:
        return {"success": False, "message": f"Cannot reach Notion API: {exc}", "details": {}}


# ---------------------------------------------------------------------------
# Custom / Generic
# ---------------------------------------------------------------------------

def _test_custom(config: Dict[str, Any]) -> Dict[str, Any]:
    """For custom integrations, optionally ping a health/test URL if provided."""
    test_url = config.get("test_url", "")
    if not test_url:
        return {
            "success": True,
            "message": "Custom integration saved. No test_url configured — assumed valid.",
            "details": {},
        }

    try:
        response = httpx.get(test_url, timeout=10)
        if response.is_success:
            return {"success": True, "message": f"Custom endpoint {test_url} returned {response.status_code}.", "details": {}}
        return {"success": False, "message": f"Custom endpoint returned HTTP {response.status_code}.", "details": {}}
    except httpx.ConnectError as exc:
        return {"success": False, "message": f"Cannot reach custom endpoint: {exc}", "details": {}}
