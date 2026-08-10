"""BlueRiiot Bluetooth integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .coordinator import BlueRiiotCoordinator

type BlueRiiotConfigEntry = ConfigEntry[BlueRiiotCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the BlueRiiot Bluetooth integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BlueRiiotConfigEntry) -> bool:
    """Set up BlueRiiot Bluetooth from a config entry."""
    coordinator = BlueRiiotCoordinator(hass, entry)
    entry.runtime_data = coordinator
    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BlueRiiotConfigEntry) -> bool:
    """Unload a BlueRiiot config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: BlueRiiotConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)