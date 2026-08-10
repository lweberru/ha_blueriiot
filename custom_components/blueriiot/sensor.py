"""Sensor platform for BlueRiiot Bluetooth."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BlueRiiotCoordinator, BlueRiiotData
from .entity import BlueRiiotEntity

_DEVICE_CLASS_PH = getattr(SensorDeviceClass, "PH", None)


class BlueRiiotSensor(BlueRiiotEntity, SensorEntity):
    """Expose one numeric BlueRiiot measurement."""

    def __init__(
        self,
        coordinator: BlueRiiotCoordinator,
        description: SensorEntityDescription,
        value: Callable[[BlueRiiotData], Any],
        *,
        requires_salt_sensor: bool = False,
    ) -> None:
        """Initialize a measurement sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._value = value
        self._requires_salt_sensor = requires_salt_sensor

    @property
    def available(self) -> bool:
        """Return whether the required measurement is available."""
        data = self.coordinator.data
        return bool(
            super().available
            and self.coordinator.connected
            and data
            and data.reading
            and (
                not self._requires_salt_sensor
                or data.reading.has_salt_sensor
            )
        )

    @property
    def native_value(self) -> Any:
        """Return the decoded sensor value."""
        return self._value(self.coordinator.data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BlueRiiot measurement and diagnostic sensors."""
    coordinator: BlueRiiotCoordinator = entry.runtime_data
    async_add_entities(
        [
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="temperature",
                    translation_key="temperature",
                    device_class=SensorDeviceClass.TEMPERATURE,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                ),
                lambda data: data.reading.temperature,
            ),
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="ph",
                    translation_key="ph",
                    device_class=_DEVICE_CLASS_PH,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                lambda data: round(data.reading.ph, 2),
            ),
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="orp",
                    translation_key="orp",
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement="mV",
                ),
                lambda data: round(data.reading.orp, 1),
            ),
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="salt",
                    translation_key="salt",
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement="g/L",
                ),
                lambda data: round(data.reading.salt, 2),
                requires_salt_sensor=True,
            ),
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="conductivity",
                    translation_key="conductivity",
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement="uS/cm",
                ),
                lambda data: round(data.reading.conductivity, 1),
            ),
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="battery",
                    translation_key="battery",
                    device_class=SensorDeviceClass.BATTERY,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement="%",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
                lambda data: round(data.reading.battery),
            ),
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="last_success",
                    translation_key="last_success",
                    device_class=SensorDeviceClass.TIMESTAMP,
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
                lambda data: data.last_success,
            ),
            BlueRiiotSensor(
                coordinator,
                SensorEntityDescription(
                    key="rssi",
                    translation_key="rssi",
                    device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                    state_class=SensorStateClass.MEASUREMENT,
                    native_unit_of_measurement="dBm",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
                lambda data: data.rssi,
            ),
            BlueRiiotLastErrorSensor(coordinator),
        ]
    )


class BlueRiiotLastErrorSensor(BlueRiiotEntity, SensorEntity):
    """Expose the latest direct-read error as a diagnostic entity."""

    _attr_translation_key = "last_error"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: BlueRiiotCoordinator) -> None:
        """Initialize the last-error sensor."""
        super().__init__(coordinator, "last_error")

    @property
    def native_value(self) -> str | None:
        """Return the exception class from the last failed GATT read."""
        return self.coordinator.data.last_error if self.coordinator.data else None