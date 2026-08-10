"""Shared entity support for BlueRiiot Bluetooth."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import BlueRiiotCoordinator


class BlueRiiotEntity(CoordinatorEntity[BlueRiiotCoordinator]):
    """Base entity attached to one BlueRiiot device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BlueRiiotCoordinator, key: str) -> None:
        """Initialize the entity with a stable device-scoped identifier."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            identifiers={(DOMAIN, coordinator.config_entry.unique_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=coordinator.config_entry.title,
        )
