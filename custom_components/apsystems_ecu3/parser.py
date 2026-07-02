"""HTML parser for APSystems ECU-3."""

from __future__ import annotations

import logging
import re

_LOGGER = logging.getLogger(__name__)


def _safe_float(value: str) -> float:
    """Convert string to float safely."""

    try:
        value = (
            value.replace(",", ".")
            .replace("kWh", "")
            .replace("Wh", "")
            .replace("W", "")
            .strip()
        )

        return float(value)

    except (ValueError, AttributeError):
        return 0.0


def _safe_int(value: str) -> int:
    """Convert string to int safely."""

    try:
        value = (
            value.replace(",", ".")
            .replace("W", "")
            .replace("V", "")
            .replace("C", "")
            .strip()
        )

        return int(float(value))

    except (ValueError, AttributeError):
        return 0


def parse_home(html: str) -> dict:
    """Parse ECU /cgi-bin/home page."""

    data: dict = {}

    rows = re.findall(
        r"<tr>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*</tr>",
        html,
        re.IGNORECASE | re.DOTALL,
    )

    for key, value in rows:

        key = re.sub(r"<.*?>", "", key).strip()
        value = re.sub(r"<.*?>", "", value).strip()

        if key == "ECU ID":
            data["ecu_id"] = value

        elif key == "Lifetime generation":
            data["lifetime_generation"] = _safe_float(value)

        elif key == "Generation Of Current Day":
            data["today_generation"] = _safe_float(value)

        elif key == "Last System Power":
            data["system_power"] = _safe_int(value)

        elif key == "Number of Inverters":
            data["number_of_inverters"] = _safe_int(value)

        elif key == "Last Number of Inverters Online":
            data["inverters_online"] = _safe_int(value)

        elif key == "Current Software Version":
            data["software_version"] = value

        elif key == "Current Timezone":
            data["timezone"] = value

        elif key == "ECU Mac Address":
            data["mac_address"] = value

    _LOGGER.debug(
        "Parsed home page: ecu_id=%s online=%s",
        data.get("ecu_id"),
        data.get("inverters_online"),
    )

    return data


def parse_parameters(html: str) -> dict:
    """Parse ECU /cgi-bin/parameters page."""

    html = (
        html.replace("&nbsp;", " ")
        .replace("<sup>o</sup>", "")
        .replace("°", "")
    )

    inverters: dict = {}

    row_pattern = re.compile(
        r"<tr>\s*"
        r"<td[^>]*>(.*?)</td>\s*"
        r"<td[^>]*>(.*?)</td>\s*"
        r"<td[^>]*>(.*?)</td>\s*"
        r"<td[^>]*>(.*?)</td>\s*"
        r"<td[^>]*>(.*?)</td>\s*"
        r"<td[^>]*>(.*?)</td>\s*"
        r"</tr>",
        re.IGNORECASE | re.DOTALL,
    )

    for match in row_pattern.finditer(html):

        inverter_id = (
            re.sub(r"<.*?>", "", match.group(1))
            .strip()
        )

        if "-" not in inverter_id:
            continue

        serial, channel = inverter_id.rsplit("-", 1)

        power = _safe_int(match.group(2))
        frequency = _safe_float(match.group(3))
        voltage = _safe_int(match.group(4))
        temperature = _safe_int(match.group(5))

        if serial not in inverters:
            inverters[serial] = {}

        inverters[serial][channel] = {
            "power": power,
            "voltage": voltage,
            "frequency": frequency,
            "temperature": temperature,
        }

    _LOGGER.debug(
        "Parsed %s micro-inverters",
        len(inverters),
    )

    return inverters