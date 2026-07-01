"""Switch entities for Zehnder ComfoAir CN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZehnderDataUpdateCoordinator
from .const import DOMAIN
from .entity import ZehnderEntity


@dataclass(frozen=True, kw_only=True)
class ZehnderSwitchDescription(SwitchEntityDescription):
    """Describe a Zehnder switch."""

    is_on_fn: Callable
    set_fn: Callable[[object, bool], Awaitable[None]]


SWITCHES: tuple[ZehnderSwitchDescription, ...] = (
    ZehnderSwitchDescription(
        key="boost_relay",
        translation_key="boost_relay",
        is_on_fn=lambda data: data.boost_relay,
        set_fn=lambda client, enabled: client.async_set_boost_relay(enabled),
    ),
    ZehnderSwitchDescription(
        key="mixed_air_relay",
        translation_key="mixed_air_relay",
        is_on_fn=lambda data: data.mixed_air_relay,
        set_fn=lambda client, enabled: client.async_set_mixed_air_relay(enabled),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zehnder switches."""
    coordinator: ZehnderDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZehnderSwitch(coordinator, description) for description in SWITCHES
    )


class ZehnderSwitch(ZehnderEntity, SwitchEntity):
    """Zehnder switch."""

    entity_description: ZehnderSwitchDescription

    def __init__(
        self,
        coordinator: ZehnderDataUpdateCoordinator,
        description: ZehnderSwitchDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, description.key, None)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self.entity_description.set_fn(self.coordinator.client, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self.entity_description.set_fn(self.coordinator.client, False)
        await self.coordinator.async_request_refresh()
