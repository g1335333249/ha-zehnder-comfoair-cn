"""Constants for the Zehnder ComfoAir CN integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "zehnder_comfoair_cn"

CONF_CONNECTION_TYPE = "connection_type"
CONF_HOST = "host"
CONF_SERIAL_PORT = "serial_port"
CONF_TCP_PORT = "tcp_port"
CONF_BAUDRATE = "baudrate"
CONF_SLAVE_ID = "slave_id"
CONF_PARITY = "parity"
CONF_STOPBITS = "stopbits"
CONF_BYTESIZE = "bytesize"

CONNECTION_TYPE_SERIAL = "serial"
CONNECTION_TYPE_TCP = "tcp"

DEFAULT_CONNECTION_TYPE = CONNECTION_TYPE_TCP
DEFAULT_TCP_PORT = 502
DEFAULT_BAUDRATE = 9600
DEFAULT_SLAVE_ID = 1
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1
DEFAULT_BYTESIZE = 8
DEFAULT_SCAN_INTERVAL = 30

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.FAN,
    Platform.SENSOR,
    Platform.SWITCH,
]

MANUFACTURER = "Zehnder"
MODEL = "CA-D635EC / CA-H3-5S"

MODE_MAP = {
    0: "auto",
    1: "fresh_air",
    2: "none",
    3: "sleep",
    4: "bypass",
    5: "antifreeze",
}
MODE_VALUE = {value: key for key, value in MODE_MAP.items()}

SPEED_MAP = {
    1: 33,
    2: 66,
    3: 100,
}
PERCENTAGE_TO_SPEED = {
    33: 1,
    66: 2,
    100: 3,
}

VOC_MAP = {
    0: "excellent",
    1: "good",
    2: "light",
    3: "moderate",
    4: "heavy",
}
