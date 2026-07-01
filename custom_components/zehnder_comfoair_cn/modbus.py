"""Modbus API for Zehnder CA-H3 controllers."""

from __future__ import annotations

from dataclasses import dataclass

from pymodbus.client import AsyncModbusSerialClient, AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

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
    CONNECTION_TYPE_TCP,
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_PARITY,
    DEFAULT_SLAVE_ID,
    DEFAULT_STOPBITS,
    DEFAULT_TCP_PORT,
)


class ZehnderModbusError(Exception):
    """Raised when the Zehnder controller cannot be reached or returns an error."""


@dataclass(slots=True)
class ZehnderData:
    """Latest values read from the controller."""

    indoor_temperature: float | None
    indoor_humidity: float | None
    outdoor_temperature: float | None
    pm25: int | None
    co2: int | None
    voc: int | None
    filter_alarm: bool
    antifreeze_alarm: bool
    mode: int | None
    speed: int | None
    power: bool
    boost_relay: bool
    mixed_air_relay: bool


class ZehnderModbusClient:
    """Small async wrapper around the CA-H3 Modbus register map."""

    def __init__(self, data: dict) -> None:
        """Initialize the client from a Home Assistant config entry."""
        self._connection_type: str = data.get(CONF_CONNECTION_TYPE, CONNECTION_TYPE_TCP)
        self._host: str | None = data.get(CONF_HOST)
        self._serial_port: str | None = data.get(CONF_SERIAL_PORT)
        self._tcp_port: int = data.get(CONF_TCP_PORT, DEFAULT_TCP_PORT)
        self._slave_id: int = data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)
        if self._connection_type == CONNECTION_TYPE_TCP:
            self._client = AsyncModbusTcpClient(
                host=self._host,
                port=self._tcp_port,
                timeout=3,
                retries=2,
            )
        else:
            self._client = AsyncModbusSerialClient(
                port=self._serial_port,
                baudrate=data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE),
                parity=data.get(CONF_PARITY, DEFAULT_PARITY),
                stopbits=data.get(CONF_STOPBITS, DEFAULT_STOPBITS),
                bytesize=data.get(CONF_BYTESIZE, DEFAULT_BYTESIZE),
                timeout=3,
                retries=2,
            )

    async def close(self) -> None:
        """Close the serial client."""
        self._client.close()

    async def async_test_connection(self) -> None:
        """Verify that the controller answers at least one request."""
        await self._ensure_connected()
        await self._read_input_registers(0x0000, 1)

    async def async_read_data(self) -> ZehnderData:
        """Read all protocol registers used by Home Assistant entities."""
        input_regs = await self._read_input_registers(0x0000, 8)
        holding_regs = await self._read_holding_registers(0x0001, 5)

        return ZehnderData(
            indoor_temperature=_signed_scale_optional(input_regs[0], 10),
            indoor_humidity=_scale_optional(input_regs[1], 10),
            outdoor_temperature=_signed_int_optional(input_regs[2]),
            pm25=_int_optional(input_regs[3]),
            co2=_int_optional(input_regs[4]),
            voc=_int_optional(input_regs[5]),
            filter_alarm=bool(input_regs[6]),
            antifreeze_alarm=bool(input_regs[7]),
            mode=_int_optional(holding_regs[0]),
            speed=_int_optional(holding_regs[1]),
            power=bool(holding_regs[2]),
            boost_relay=bool(holding_regs[3]),
            mixed_air_relay=bool(holding_regs[4]),
        )

    async def async_reset_filter_alarm(self) -> None:
        """Reset the filter alarm."""
        await self._write_register(0x0000, 1)

    async def async_set_mode(self, value: int) -> None:
        """Set ventilation mode."""
        await self._write_register(0x0001, value)

    async def async_set_speed(self, value: int) -> None:
        """Set fan speed: 1 low, 2 medium, 3 high."""
        await self._write_register(0x0002, value)

    async def async_set_power(self, enabled: bool) -> None:
        """Turn the unit on or off."""
        await self._write_register(0x0003, int(enabled))

    async def async_set_boost_relay(self, enabled: bool) -> None:
        """Set the boost relay."""
        await self._write_register(0x0004, int(enabled))

    async def async_set_mixed_air_relay(self, enabled: bool) -> None:
        """Set the mixed-air relay."""
        await self._write_register(0x0005, int(enabled))

    async def _ensure_connected(self) -> None:
        if self._client.connected:
            return
        try:
            if await self._client.connect():
                return
        except ModbusException as err:
            raise ZehnderModbusError(str(err)) from err
        if self._connection_type == CONNECTION_TYPE_TCP:
            target = f"{self._host}:{self._tcp_port}"
        else:
            target = str(self._serial_port)
        raise ZehnderModbusError(f"Unable to connect to {target}")

    async def _read_input_registers(self, address: int, count: int) -> list[int]:
        await self._ensure_connected()
        try:
            result = await self._client.read_input_registers(
                address=address,
                count=count,
                slave=self._slave_id,
            )
        except ModbusException as err:
            raise ZehnderModbusError(str(err)) from err
        return _registers_or_raise(result)

    async def _read_holding_registers(self, address: int, count: int) -> list[int]:
        await self._ensure_connected()
        try:
            result = await self._client.read_holding_registers(
                address=address,
                count=count,
                slave=self._slave_id,
            )
        except ModbusException as err:
            raise ZehnderModbusError(str(err)) from err
        return _registers_or_raise(result)

    async def _write_register(self, address: int, value: int) -> None:
        await self._ensure_connected()
        try:
            result = await self._client.write_register(
                address=address,
                value=value,
                slave=self._slave_id,
            )
        except ModbusException as err:
            raise ZehnderModbusError(str(err)) from err
        if result.isError():
            raise ZehnderModbusError(f"Modbus write failed: {result}")


def _registers_or_raise(result) -> list[int]:
    if result.isError():
        raise ZehnderModbusError(f"Modbus read failed: {result}")
    registers = getattr(result, "registers", None)
    if registers is None:
        raise ZehnderModbusError(f"Modbus response has no registers: {result}")
    return list(registers)


def _scale_optional(value: int, divisor: int) -> float | None:
    return None if value == 0xFFFF else value / divisor


def _signed_scale_optional(value: int, divisor: int) -> float | None:
    signed = _signed_int_optional(value)
    return None if signed is None else signed / divisor


def _int_optional(value: int) -> int | None:
    return None if value == 0xFFFF else value


def _signed_int_optional(value: int) -> int | None:
    if value == 0xFFFF:
        return None
    return value - 0x10000 if value & 0x8000 else value
