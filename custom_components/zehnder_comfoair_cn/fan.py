"""Fan entity for Zehnder ComfoAir CN."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZehnderDataUpdateCoordinator
from .const import DOMAIN, MODE_MAP, MODE_VALUE, SPEED_MAP
from .entity import ZehnderEntity

ORDERED_SPEEDS = ["low", "medium", "high"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Zehnder fan."""
    coordinator: ZehnderDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZehnderFan(coordinator)])


class ZehnderFan(ZehnderEntity, FanEntity):
    """Fan control for a Zehnder CA-H3 controller."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_preset_modes = list(MODE_VALUE)
    _attr_speed_count = len(ORDERED_SPEEDS)
    _attr_percentage_step = 33

    def __init__(self, coordinator: ZehnderDataUpdateCoordinator) -> None:
        """Initialize the fan."""
        super().__init__(coordinator, "fan", None)

    @property
    def is_on(self) -> bool:
        """Return true when the unit is on."""
        return self.coordinator.data.power

    @property
    def percentage(self) -> int | None:
        """Return current fan percentage."""
        speed = self.coordinator.data.speed
        if speed not in SPEED_MAP:
            return None
        return SPEED_MAP[speed]

    @property
    def preset_mode(self) -> str | None:
        """Return current ventilation mode."""
        mode = self.coordinator.data.mode
        return MODE_MAP.get(mode) if mode is not None else None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs,
    ) -> None:
        """Turn the unit on."""
        await self.coordinator.client.async_set_power(True)
        if percentage is not None:
            await self.async_set_percentage(percentage)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the unit off."""
        await self.coordinator.client.async_set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set fan speed from Home Assistant percentage."""
        if percentage <= 0:
            await self.async_turn_off()
            return
        if percentage <= 33:
            speed = 1
        elif percentage <= 66:
            speed = 2
        else:
            speed = 3
        await self.coordinator.client.async_set_speed(speed)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set ventilation mode."""
        if preset_mode not in MODE_VALUE:
            return
        await self.coordinator.client.async_set_mode(MODE_VALUE[preset_mode])
        await self.coordinator.async_request_refresh()
