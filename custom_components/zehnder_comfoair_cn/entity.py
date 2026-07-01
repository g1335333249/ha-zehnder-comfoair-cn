"""Base entity for Zehnder ComfoAir CN."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZehnderDataUpdateCoordinator
from .const import DOMAIN, MANUFACTURER, MODEL


class ZehnderEntity(CoordinatorEntity[ZehnderDataUpdateCoordinator]):
    """Base class for Zehnder entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ZehnderDataUpdateCoordinator,
        key: str,
        name: str | None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name="Zehnder ComfoAir",
        )
