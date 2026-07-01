"""Config flow for Zehnder ComfoAir CN."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_CONNECTION_TYPE,
    CONF_HOST,
    CONF_PARITY,
    CONF_SERIAL_PORT,
    CONF_SLAVE_ID,
    CONF_STOPBITS,
    CONF_TCP_PORT,
    CONNECTION_TYPE_SERIAL,
    CONNECTION_TYPE_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_CONNECTION_TYPE,
    DEFAULT_PARITY,
    DEFAULT_SLAVE_ID,
    DEFAULT_STOPBITS,
    DEFAULT_TCP_PORT,
    DOMAIN,
)
from .modbus import ZehnderModbusClient, ZehnderModbusError

_LOGGER = logging.getLogger(__name__)

BAUDRATE_OPTIONS = ["4800", "9600", "14400", "19200", "38400"]
PARITY_OPTIONS = [
    {"value": "N", "label": "无校验"},
    {"value": "E", "label": "偶校验"},
    {"value": "O", "label": "奇校验"},
]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zehnder ComfoAir CN."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._connection_type = DEFAULT_CONNECTION_TYPE

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Choose connection type."""
        if user_input is not None:
            self._connection_type = user_input[CONF_CONNECTION_TYPE]
            if self._connection_type == CONNECTION_TYPE_TCP:
                return await self.async_step_tcp()
            return await self.async_step_serial()

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_CONNECTION_TYPE, default=DEFAULT_CONNECTION_TYPE
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": CONNECTION_TYPE_TCP, "label": "TCP/IP RS485 网关"},
                            {"value": CONNECTION_TYPE_SERIAL, "label": "本地 USB-RS485 串口"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_tcp(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure a TCP/IP Modbus gateway."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = self._normalize_common_data(user_input)
            data[CONF_CONNECTION_TYPE] = CONNECTION_TYPE_TCP
            data[CONF_TCP_PORT] = int(data[CONF_TCP_PORT])
            await self.async_set_unique_id(
                f"tcp-{data[CONF_HOST]}-{data[CONF_TCP_PORT]}-{data[CONF_SLAVE_ID]}"
            )
            self._abort_if_unique_id_configured()

            errors = await self._async_validate_connection(data)
            if not errors:
                return self.async_create_entry(
                    title=f"Zehnder CA-H3 ({data[CONF_HOST]}:{data[CONF_TCP_PORT]})",
                    data=data,
                )

        return self.async_show_form(
            step_id="tcp",
            data_schema=_tcp_schema(),
            errors=errors,
        )

    async def async_step_serial(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Configure a local serial Modbus RTU adapter."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = self._normalize_common_data(user_input)
            data[CONF_CONNECTION_TYPE] = CONNECTION_TYPE_SERIAL
            await self.async_set_unique_id(
                f"serial-{data[CONF_SERIAL_PORT]}-{data[CONF_SLAVE_ID]}"
            )
            self._abort_if_unique_id_configured()

            errors = await self._async_validate_connection(data)
            if not errors:
                return self.async_create_entry(
                    title=f"Zehnder CA-H3 ({data[CONF_SERIAL_PORT]})",
                    data=data,
                )

        return self.async_show_form(
            step_id="serial",
            data_schema=_serial_schema(),
            errors=errors,
        )

    async def _async_validate_connection(self, data: dict[str, Any]) -> dict[str, str]:
        """Validate connection settings against the controller."""
        client = ZehnderModbusClient(data)
        try:
            await client.async_test_connection()
        except ZehnderModbusError:
            _LOGGER.exception("Failed to connect to Zehnder controller")
            return {"base": "cannot_connect"}
        finally:
            await client.close()
        return {}

    @staticmethod
    def _normalize_common_data(user_input: dict[str, Any]) -> dict[str, Any]:
        """Normalize selector strings into runtime values."""
        data = dict(user_input)
        data[CONF_SLAVE_ID] = int(data[CONF_SLAVE_ID])
        data[CONF_BAUDRATE] = int(data[CONF_BAUDRATE])
        data[CONF_STOPBITS] = int(data[CONF_STOPBITS])
        data[CONF_BYTESIZE] = int(data[CONF_BYTESIZE])
        return data

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options updates."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage connection options."""
        current = {**self._config_entry.data, **self._config_entry.options}
        connection_type = current.get(CONF_CONNECTION_TYPE, DEFAULT_CONNECTION_TYPE)

        if user_input is not None:
            data = ConfigFlow._normalize_common_data(user_input)
            if connection_type == CONNECTION_TYPE_TCP:
                data[CONF_TCP_PORT] = int(data[CONF_TCP_PORT])
            return self.async_create_entry(title="", data=data)

        if connection_type == CONNECTION_TYPE_TCP:
            schema = _tcp_schema(current)
        else:
            schema = _serial_schema(current)
        return self.async_show_form(step_id="init", data_schema=schema)


def _common_schema_fields(current: dict[str, Any] | None = None) -> dict:
    """Return fields shared by serial and TCP gateway setup."""
    current = current or {}
    return {
        vol.Required(
            CONF_SLAVE_ID, default=current.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=1,
                max=247,
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Required(
            CONF_BAUDRATE, default=str(current.get(CONF_BAUDRATE, DEFAULT_BAUDRATE))
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=BAUDRATE_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_PARITY, default=current.get(CONF_PARITY, DEFAULT_PARITY)
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=PARITY_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_STOPBITS, default=current.get(CONF_STOPBITS, DEFAULT_STOPBITS)
        ): vol.All(vol.Coerce(int), vol.In([1, 2])),
        vol.Required(
            CONF_BYTESIZE, default=current.get(CONF_BYTESIZE, DEFAULT_BYTESIZE)
        ): vol.All(vol.Coerce(int), vol.In([7, 8])),
    }


def _tcp_schema(current: dict[str, Any] | None = None) -> vol.Schema:
    """Return TCP/IP gateway setup schema."""
    current = current or {}
    fields = {
        vol.Required(CONF_HOST, default=current.get(CONF_HOST, "")): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
        vol.Required(
            CONF_TCP_PORT, default=current.get(CONF_TCP_PORT, DEFAULT_TCP_PORT)
        ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
    }
    fields.update(_common_schema_fields(current))
    return vol.Schema(fields)


def _serial_schema(current: dict[str, Any] | None = None) -> vol.Schema:
    """Return local serial setup schema."""
    current = current or {}
    fields = {
        vol.Required(
            CONF_SERIAL_PORT, default=current.get(CONF_SERIAL_PORT, "")
        ): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
    }
    fields.update(_common_schema_fields(current))
    return vol.Schema(fields)
