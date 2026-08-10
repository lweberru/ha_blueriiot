"""Button platform for BlueRiiot Bluetooth."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BlueRiiotCoordinator
from .entity import BlueRiiotEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the BlueRiiot refresh button."""
    async_add_entities([BlueRiiotRefreshButton(entry.runtime_data)])


class BlueRiiotRefreshButton(BlueRiiotEntity, ButtonEntity):
    """Request an immediate direct measurement."""

    _attr_translation_key = "refresh"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: BlueRiiotCoordinator) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator, "refresh")

    async def async_press(self) -> None:
        """Run an immediate BlueRiiot GATT read."""
        await self.coordinator.async_request_refresh()