"""Minimal async client for the Datacake GraphQL API."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import API_URL

_LOGGER = logging.getLogger(__name__)


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
      field { fieldName verboseFieldName %s }
    }
  }
}
"""

# `unit` is a documented field setting in Datacake but not in the public GraphQL
# docs; fall back to the plain query if the schema rejects it.
EXTRA_FIELD_ATTRS = "unit"


class DatacakeClient:
    """Datacake GraphQL client."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self._with_unit = True
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
        extra = EXTRA_FIELD_ATTRS if self._with_unit else ""
        try:
            data = await self._query(DEVICES_QUERY % extra, {"ws": workspace_id})
        except DatacakeAuthError:
            raise
        except DatacakeError as err:
            if self._with_unit and "Cannot query field" in str(err):
                _LOGGER.warning("Datacake schema has no field unit; continuing without")
                self._with_unit = False
                return await self.get_devices(workspace_id)
            raise
        return data["allDevices"]
