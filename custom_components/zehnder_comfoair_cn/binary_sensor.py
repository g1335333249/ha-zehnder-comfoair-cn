"""Binary sensor entities for Zehnder ComfoAir CN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZehnderDataUpdateCoordinator
from .const import DOMAIN
from .entity import ZehnderEntity
from .modbus import ZehnderData


@dataclass(frozen=True, kw_only=True)
class ZehnderBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a Zehnder binary sensor."""

    value_fn: Callable[[ZehnderData], bool]


BINARY_SENSORS: tuple[ZehnderBinarySensorDescription, ...] = (
    ZehnderBinarySensorDescription(
        key="filter_alarm",
        translation_key="filter_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.filter_alarm,
    ),
    ZehnderBinarySensorDescription(
        key="antifreeze_alarm",
        translation_key="antifreeze_alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.antifreeze_alarm,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zehnder binary sensors."""
    coordinator: ZehnderDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZehnderBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class ZehnderBinarySensor(ZehnderEntity, BinarySensorEntity):
    """Zehnder binary sensor."""

    entity_description: ZehnderBinarySensorDescription

    def __init__(
        self,
        coordinator: ZehnderDataUpdateCoordinator,
        description: ZehnderBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key, None)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        """Return true if the alarm is active."""
        return self.entity_description.value_fn(self.coordinator.data)
