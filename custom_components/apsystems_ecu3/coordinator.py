"""Data coordinator for APSystems ECU-3."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    DATA_HOME,
    DATA_INVERTERS,
    DOMAIN,
    HOME_ENDPOINT,
    PARAMETERS_ENDPOINT,
    REQUEST_TIMEOUT,
)

from .parser import (
    parse_home,
    parse_parameters,
)

_LOGGER = logging.getLogger(__name__)


class APSystemsECU3Coordinator(
    DataUpdateCoordinator[dict[str, Any]]
):
    """Coordinator for APSystems ECU-3."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""

        self.host: str = entry.data[CONF_HOST]

        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=scan_interval,
            ),
        )

    async def _fetch_page(
        self,
        endpoint: str,
    ) -> str:
        """Fetch a page from the ECU using raw TCP."""

        writer = None

        try:
            async with asyncio.timeout(
                REQUEST_TIMEOUT,
            ):
                reader, writer = await asyncio.open_connection(
                    self.host,
                    80,
                )

                request = (
                    f"GET {endpoint} HTTP/1.0\r\n"
                    f"Host: {self.host}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )

                _LOGGER.debug(
                    "Requesting %s",
                    endpoint,
                )

                writer.write(
                    request.encode("ascii")
                )

                await writer.drain()

                response = await reader.read()

        except asyncio.TimeoutError as err:
            raise UpdateFailed(
                f"Timeout while fetching {endpoint}"
            ) from err

        except OSError as err:
            raise UpdateFailed(
                f"Unable to connect to ECU-3 ({self.host}): {err}"
            ) from err

        finally:
            if writer is not None:
                writer.close()

                try:
                    await writer.wait_closed()
                except Exception:
                    pass

        text = response.decode(
            errors="ignore",
        )

        _LOGGER.debug(
            "Raw response from %s:\n%s",
            endpoint,
            text[:500],
        )

        #
        # Split HTTP headers from body.
        # Older ECU firmwares may only use LF.
        #
        if "\r\n\r\n" in text:
            header, _, body = text.partition(
                "\r\n\r\n"
            )
        elif "\n\n" in text:
            header, _, body = text.partition(
                "\n\n"
            )
        else:
            header = ""
            body = text

        #
        # Validate HTTP status if headers are present.
        #
        if header:
            status_line = header.splitlines()[0]

            if "200" not in status_line:
                raise UpdateFailed(
                    f"Unexpected HTTP status: {status_line}"
                )

        if not body.strip():
            raise UpdateFailed(
                f"Empty response from {endpoint}"
            )

        _LOGGER.debug(
            "%s returned %d bytes",
            endpoint,
            len(body),
        )

        return body

    async def _async_update_data(
        self,
    ) -> dict[str, Any]:
        """Fetch latest ECU data."""

        try:

            home_html = await self._fetch_page(
                HOME_ENDPOINT,
            )

            parameters_html = await self._fetch_page(
                PARAMETERS_ENDPOINT,
            )

            home = parse_home(
                home_html,
            )

            inverters = parse_parameters(
                parameters_html,
            )

            home[
                "integration_profile"
            ] = (
                "ECU-3 Legacy Web Interface"
            )

            _LOGGER.debug(
                "Update successful (ECU=%s, inverters=%d)",
                home.get("ecu_id"),
                len(inverters),
            )

            return {
                DATA_HOME: home,
                DATA_INVERTERS: inverters,
            }

        except asyncio.CancelledError:
            raise

        except UpdateFailed:
            raise

        except Exception as err:
            _LOGGER.exception(
                "Unexpected error while updating ECU-3"
            )

            raise UpdateFailed(
                str(err)
            ) from err