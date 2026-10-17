"""Minimal async client for the Datacake GraphQL API."""

from __future__ import annotations

from typing import Any

import aiohttp

from .const import API_URL


class DatacakeError(Exception):
    """Base error."""


class DatacakeAuthError(DatacakeError):
    """Token rejected."""


class DatacakeConnectionError(DatacakeError):
    """Network failure."""


WORKSPACES_QUERY = "query { allWorkspaces { id name } }"

DEVICES_QUERY = """
query ($ws: String!) {
  allDevices(inWorkspace: $ws) {
    id
    verboseName
    currentMeasurements(allActiveFields: true) {
      value
      modified
      field { fieldName verboseFieldName }
    }
  }
}
"""


class DatacakeClient:
    """Datacake GraphQL client."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

    async def _query(self, query: str, variables: dict | None = None) -> dict[str, Any]:
        try:
            async with self._session.post(
                API_URL,
                json={"query": query, "variables": variables or {}},
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status in (401, 403):
                    raise DatacakeAuthError("Invalid token")
                resp.raise_for_status()
                payload = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise DatacakeConnectionError(str(err)) from err

        if errors := payload.get("errors"):
            msg = "; ".join(e.get("message", "") for e in errors)
            if "permission" in msg.lower() or "authenticat" in msg.lower():
                raise DatacakeAuthError(msg)
            raise DatacakeError(msg)
        return payload["data"]

    async def get_workspaces(self) -> list[dict[str, str]]:
        return (await self._query(WORKSPACES_QUERY))["allWorkspaces"]

    async def get_devices(self, workspace_id: str) -> list[dict[str, Any]]:
        data = await self._query(DEVICES_QUERY, {"ws": workspace_id})
        return data["allDevices"]
