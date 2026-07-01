"""Button entities for Zehnder ComfoAir CN."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ZehnderDataUpdateCoordinator
from .const import DOMAIN
from .entity import ZehnderEntity


BUTTONS: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="reset_filter_alarm",
        translation_key="reset_filter_alarm",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Zehnder buttons."""
    coordinator: ZehnderDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ZehnderResetFilterButton(coordinator, description) for description in BUTTONS
    )


class ZehnderResetFilterButton(ZehnderEntity, ButtonEntity):
    """Button that resets the filter alarm."""

    entity_description: ButtonEntityDescription

    def __init__(
        self,
        coordinator: ZehnderDataUpdateCoordinator,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, description.key, None)
        self.entity_description = description

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.client.async_reset_filter_alarm()
        await self.coordinator.async_request_refresh()
