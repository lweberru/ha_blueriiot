"""Coordinator for BlueRiiot Bluetooth measurements."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .config_flow import CONF_UPDATE_INTERVAL
from .const import (
    CONF_SALT_DIVISOR,
    DEFAULT_SALT_DIVISOR,
    DEFAULT_UPDATE_INTERVAL_DELTA,
    DOMAIN,
)
from .decoder import BlueRiiotReading
from .protocol import BlueRiiotClient

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class BlueRiiotData:
    """Last direct measurement and diagnostics for a BlueRiiot."""

    reading: BlueRiiotReading | None
    last_success: datetime | None
    last_error: str | None
    rssi: int | None

    @property
    def connected(self) -> bool:
        """Return whether a direct GATT read recently succeeded."""
        if self.last_success is None:
            return False
        return dt_util.utcnow() - self.last_success <= timedelta(minutes=30)


class BlueRiiotCoordinator(DataUpdateCoordinator[BlueRiiotData]):
    """Coordinate direct GATT reads for one BlueRiiot device."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self.address = format_mac(entry.data[CONF_ADDRESS])
        interval = timedelta(
            minutes=int(entry.options.get(CONF_UPDATE_INTERVAL, 15))
        )
        self._salt_divisor = float(
            entry.options.get(CONF_SALT_DIVISOR, DEFAULT_SALT_DIVISOR)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{self.address}",
            update_interval=interval or DEFAULT_UPDATE_INTERVAL_DELTA,
        )
        self._client = BlueRiiotClient(hass, self.address)
        self._last_success: datetime | None = None
        self._last_error: str | None = None
        self._reading: BlueRiiotReading | None = None

    @property
    def connected(self) -> bool:
        """Return whether a direct read succeeded within two poll intervals."""
        if not self.data or self.data.last_success is None:
            return False
        return dt_util.utcnow() - self.data.last_success <= max(
            self.update_interval * 2, timedelta(minutes=30)
        )

    async def _async_update_data(self) -> BlueRiiotData:
        """Read the device and preserve the prior reading on a transient failure."""
        try:
            self._reading = await self._client.async_read(
                salt_divisor=self._salt_divisor
            )
        except Exception as err:  # Bluetooth backend errors are platform dependent.
            self._last_error = type(err).__name__
            _LOGGER.debug("Could not read BlueRiiot %s: %s", self.address, err)
        else:
            self._last_success = dt_util.utcnow()
            self._last_error = None

        return BlueRiiotData(
            reading=self._reading,
            last_success=self._last_success,
            last_error=self._last_error,
            rssi=self._rssi(),
        )

    def _rssi(self) -> int | None:
        """Return the latest RSSI provided by a local adapter or Bluetooth proxy."""
        for service_info in bluetooth.async_discovered_service_info(
            self.hass, connectable=True
        ):
            if format_mac(service_info.address) == self.address:
                return service_info.rssi
        return None