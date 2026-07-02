"""Config flow for APSystems ECU-3."""

from __future__ import annotations

import asyncio
import ipaddress
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .const import (
    CONF_CUSTOM_MODEL,
    CONF_HOST,
    CONF_INVERTER_MODEL,
    CONF_SCAN_INTERVAL,
    DEFAULT_INVERTER_MODEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    HOME_ENDPOINT,
    MIN_SCAN_INTERVAL,
    REQUEST_TIMEOUT,
    SUPPORTED_INVERTER_MODELS,
)
from .parser import parse_home

_LOGGER = logging.getLogger(__name__)


async def _async_fetch_ecu_id(host: str) -> str | None:
    """Connect to the ECU-3 and return its ECU ID.

    Returns None if the ECU could not be reached at all.
    Returns an empty string if the ECU replied but no ECU ID
    could be parsed from the page.
    """

    writer = None

    try:
        async with asyncio.timeout(REQUEST_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, 80)

            request = (
                f"GET {HOME_ENDPOINT} HTTP/1.0\r\n"
                f"Host: {host}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )

            writer.write(request.encode("ascii"))
            await writer.drain()

            response = await reader.read()

    except (TimeoutError, OSError) as err:
        _LOGGER.debug("Unable to connect to ECU-3 (%s): %s", host, err)
        return None

    finally:
        if writer is not None:
            writer.close()

            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass

    text = response.decode(errors="ignore")

    if "\r\n\r\n" in text:
        _, _, body = text.partition("\r\n\r\n")
    elif "\n\n" in text:
        _, _, body = text.partition("\n\n")
    else:
        body = text

    if not body.strip():
        return ""

    data = parse_home(body)

    return data.get("ecu_id", "")


class APSystemsECU3ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for APSystems ECU-3."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial setup step."""

        errors: dict[str, str] = {}
        ecu_id: str | None = None

        if user_input is not None:
            host = user_input[CONF_HOST].strip()

            try:
                ipaddress.ip_address(host)
            except ValueError:
                errors["base"] = "invalid_host"

            if not errors:
                ecu_id = await _async_fetch_ecu_id(host)

                if ecu_id is None:
                    errors["base"] = "cannot_connect"
                elif not ecu_id:
                    errors["base"] = "invalid_ecu"

            if not errors:
                inverter_model = user_input[CONF_INVERTER_MODEL]
                custom_model = user_input.get(CONF_CUSTOM_MODEL, "").strip()

                if inverter_model == "Custom" and not custom_model:
                    errors["base"] = "custom_model_required"

            if not errors:
                await self.async_set_unique_id(ecu_id)
                self._abort_if_unique_id_configured()

                user_input[CONF_HOST] = host

                return self.async_create_entry(
                    title=f"ECU-3 {ecu_id}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=DEFAULT_SCAN_INTERVAL,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL),
                    ),
                    vol.Required(
                        CONF_INVERTER_MODEL,
                        default=DEFAULT_INVERTER_MODEL,
                    ): vol.In(SUPPORTED_INVERTER_MODELS),
                    vol.Optional(CONF_CUSTOM_MODEL, default=""): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> APSystemsECU3OptionsFlow:
        """Get the options flow for this handler."""

        return APSystemsECU3OptionsFlow()


class APSystemsECU3OptionsFlow(config_entries.OptionsFlow):
    """Handle APSystems ECU-3 options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""

        errors: dict[str, str] = {}

        if user_input is not None:
            scan_interval = user_input[CONF_SCAN_INTERVAL]

            if scan_interval < MIN_SCAN_INTERVAL:
                errors["base"] = "scan_interval_too_low"

            inverter_model = user_input[CONF_INVERTER_MODEL]
            custom_model = user_input.get(CONF_CUSTOM_MODEL, "").strip()

            if inverter_model == "Custom" and not custom_model:
                errors["base"] = "custom_model_required"

            if not errors:
                return self.async_create_entry(
                    title="",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL,
                            self.config_entry.data.get(
                                CONF_SCAN_INTERVAL,
                                DEFAULT_SCAN_INTERVAL,
                            ),
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL),
                    ),
                    vol.Required(
                        CONF_INVERTER_MODEL,
                        default=self.config_entry.options.get(
                            CONF_INVERTER_MODEL,
                            self.config_entry.data.get(
                                CONF_INVERTER_MODEL,
                                DEFAULT_INVERTER_MODEL,
                            ),
                        ),
                    ): vol.In(SUPPORTED_INVERTER_MODELS),
                    vol.Optional(
                        CONF_CUSTOM_MODEL,
                        default=self.config_entry.options.get(
                            CONF_CUSTOM_MODEL,
                            self.config_entry.data.get(
                                CONF_CUSTOM_MODEL,
                                "",
                            ),
                        ),
                    ): str,
                }
            ),
            errors=errors,
        )
