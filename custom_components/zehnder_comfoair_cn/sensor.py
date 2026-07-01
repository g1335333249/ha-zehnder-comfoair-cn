"""Sensor entities for Zehnder ComfoAir CN."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZehnderDataUpdateCoordinator
from .const import DOMAIN, VOC_MAP
from .entity import ZehnderEntity
from .modbus import ZehnderData


@dataclass(frozen=True, kw_only=True)
class ZehnderSensorDescription(SensorEntityDescription):
    """Describe a Zehnder sensor."""

    value_fn: Callable[[ZehnderData], int | float | str | None]


SENSORS: tuple[ZehnderSensorDescription, ...] = (
    ZehnderSensorDescription(
        key="indoor_temperature",
        translation_key="indoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.indoor_temperature,
    ),
    ZehnderSensorDescription(
        key="indoor_humidity",
        translation_key="indoor_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.indoor_humidity,
    ),
    ZehnderSensorDescription(
        key="outdoor_temperature",
        translation_key="outdoor_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.outdoor_temperature,
    ),
    ZehnderSensorDescription(
        key="pm25",
        translation_key="pm25",
        device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.pm25,
    ),
    ZehnderSensorDescription(
        key="co2",
        translation_key="co2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement="ppm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.co2,
    ),
    ZehnderSensorDescription(
        key="voc",
        translation_key="voc",
        device_class=SensorDeviceClass.ENUM,
        options=list(VOC_MAP.values()),
        value_fn=lambda data: VOC_MAP.get(data.voc) if data.voc is not None else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zehnder sensors."""
    coordinator: ZehnderDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZehnderSensor(coordinator, description) for description in SENSORS
    )


class ZehnderSensor(ZehnderEntity, SensorEntity):
    """Zehnder sensor."""

    entity_description: ZehnderSensorDescription

    def __init__(
        self,
        coordinator: ZehnderDataUpdateCoordinator,
        description: ZehnderSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key, None)
        self.entity_description = description

    @property
    def native_value(self) -> int | float | str | None:
        """Return the native value."""
        return self.entity_description.value_fn(self.coordinator.data)
