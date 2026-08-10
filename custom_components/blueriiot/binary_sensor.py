"""Binary sensor platform for BlueRiiot Bluetooth."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BlueRiiotCoordinator
from .entity import BlueRiiotEntity


async def async_setup_entry(
    hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the BlueRiiot connectivity sensor."""
    async_add_entities([BlueRiiotConnectivitySensor(entry.runtime_data)])


class BlueRiiotConnectivitySensor(BlueRiiotEntity, BinarySensorEntity):
    """Report whether a direct BlueRiiot read recently succeeded."""

    _attr_translation_key = "connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: BlueRiiotCoordinator) -> None:
        """Initialize the connectivity sensor."""
        super().__init__(coordinator, "connected")

    @property
    def is_on(self) -> bool:
        """Return direct GATT reachability."""
        return self.coordinator.connected