"""Config flow for Datacake."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .api import DatacakeAuthError, DatacakeClient, DatacakeError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_WORKSPACE_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)


class DatacakeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._token: str | None = None
        self._workspaces: list[dict[str, str]] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return DatacakeOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = DatacakeClient(
                async_get_clientsession(self.hass), user_input[CONF_API_TOKEN]
            )
            try:
                self._workspaces = await client.get_workspaces()
            except DatacakeAuthError:
                errors["base"] = "invalid_auth"
            except DatacakeError:
                errors["base"] = "cannot_connect"
            else:
                if not self._workspaces:
                    errors["base"] = "no_workspaces"
                else:
                    self._token = user_input[CONF_API_TOKEN]
                    return await self.async_step_workspace()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )

    async def async_step_workspace(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            ws_id = user_input[CONF_WORKSPACE_ID]
            await self.async_set_unique_id(ws_id)
            self._abort_if_unique_id_configured()
            name = next(w["name"] for w in self._workspaces if w["id"] == ws_id)
            return self.async_create_entry(
                title=name,
                data={CONF_API_TOKEN: self._token, CONF_WORKSPACE_ID: ws_id},
            )

        options = [SelectOptionDict(value=w["id"], label=w["name"]) for w in self._workspaces]
        return self.async_show_form(
            step_id="workspace",
            data_schema=vol.Schema(
                {vol.Required(CONF_WORKSPACE_ID): SelectSelector(SelectSelectorConfig(options=options))}
            ),
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            client = DatacakeClient(
                async_get_clientsession(self.hass), user_input[CONF_API_TOKEN]
            )
            try:
                await client.get_workspaces()
            except DatacakeAuthError:
                errors["base"] = "invalid_auth"
            except DatacakeError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_TOKEN: user_input[CONF_API_TOKEN]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_TOKEN): str}),
            errors=errors,
        )


class DatacakeOptionsFlow(OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                        int, vol.Range(min=MIN_SCAN_INTERVAL)
                    )
                }
            ),
        )
