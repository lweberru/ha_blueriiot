"""BlueRiiot Bluetooth integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CONF_DEVICE_NAME, DOMAIN, PLATFORMS
from .coordinator import BlueRiiotCoordinator

type BlueRiiotConfigEntry = ConfigEntry[BlueRiiotCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the BlueRiiot Bluetooth integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: BlueRiiotConfigEntry) -> bool:
    """Set up BlueRiiot Bluetooth from a config entry."""
    coordinator = BlueRiiotCoordinator(hass, entry)
    name = str(entry.data.get(CONF_DEVICE_NAME) or "").strip()
    suffix = coordinator.address.replace(":", "")[-6:]
    title = f"Blue Connect {name}" if name else f"Blue Connect {suffix}"
    if entry.title != title:
        hass.config_entries.async_update_entry(entry, title=title)
    entry.runtime_data = coordinator
    # An address-specific ACTIVE subscription opts AUTO-mode adapters/proxies
    # into HA's active-scan scheduler. Do not force scanner settings globally.
    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            lambda service_info, change: None,
            {"address": coordinator.address, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )
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
