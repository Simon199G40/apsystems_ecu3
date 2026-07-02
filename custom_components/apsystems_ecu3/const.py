"""Constants for APSystems ECU-3."""

from __future__ import annotations

DOMAIN = "apsystems_ecu3"

MANUFACTURER = "APSystems"
MODEL = "ECU-3"

# Config
CONF_HOST = "host"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_INVERTER_MODEL = "inverter_model"
CONF_CUSTOM_MODEL = "custom_model"

# Defaults
DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 60

DEFAULT_INVERTER_MODEL = "YC500"

SUPPORTED_INVERTER_MODELS = [
    "YC500",
    "YC500A",
    "YC600",
    "QS1",
    "Custom",
]

# HTTP
HOME_ENDPOINT = "/cgi-bin/home"
PARAMETERS_ENDPOINT = "/cgi-bin/parameters"

REQUEST_TIMEOUT = 10

# Coordinator data
DATA_HOME = "home"
DATA_INVERTERS = "inverters"

# Diagnostics
PARSER_VERSION = 1