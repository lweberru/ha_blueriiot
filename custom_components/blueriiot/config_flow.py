"""Config flow for BlueRiiot Bluetooth."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.device_registry import format_mac

from .const import (
    CONF_SALT_DIVISOR,
    CONF_SALT_REFERENCE,
    CONF_DEVICE_NAME,
    DEFAULT_SALT_DIVISOR,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
    SERVICE_UUID,
)

CONF_UPDATE_INTERVAL = "update_interval"
_DISCOVERY_NAME_PREFIXES = ("blue connect", "blueriiot")
_MANUFACTURER_ID = 305
_MANUFACTURER_DATA_PREFIX = bytes([0x19, 0x01])
_LOGGER = logging.getLogger(__name__)


def _is_blueriiot_device(service_info: BluetoothServiceInfoBleak) -> bool:
    """Return whether advertisement data identifies a BlueRiiot device."""
    service_uuids = {
        str(service_uuid).lower()
        for service_uuid in (service_info.service_uuids or [])
    }
    name = (service_info.name or "").lower()
    manufacturer_data = service_info.manufacturer_data.get(_MANUFACTURER_ID, b"")
    return (
        SERVICE_UUID.lower() in service_uuids
        or name.startswith(_DISCOVERY_NAME_PREFIXES)
        or manufacturer_data.startswith(_MANUFACTURER_DATA_PREFIX)
    )


def _discovered_devices(hass) -> list[selector.SelectOptionDict]:
    """Return BlueRiiot devices known to Home Assistant Bluetooth."""
    devices: dict[str, selector.SelectOptionDict] = {}
    for service_info in bluetooth.async_discovered_service_info(hass, connectable=True):
        if not _is_blueriiot_device(service_info):
            continue
        _LOGGER.debug(
            "Discovered BlueRiiot advertisement: name=%r address=%s",
            service_info.name,
            format_mac(service_info.address),
        )
        address = format_mac(service_info.address)
        name = service_info.name or "BlueRiiot"
        devices[address] = {"value": address, "label": f"{name} ({address})"}
    return sorted(devices.values(), key=lambda device: device["label"].lower())


def _address_schema(hass) -> vol.Schema:
    """Build the address selection schema from the current Bluetooth cache."""
    return vol.Schema(
        {
            vol.Required(CONF_ADDRESS): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_discovered_devices(hass),
                    custom_value=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _normalized_address(address: str) -> str:
    """Return the Bluetooth address in Home Assistant cache format."""
    return format_mac(address).upper()


def _entry_title(name: str | None, address: str) -> str:
    """Build a recognizable product name from BLE advertisement data."""
    suffix = address.replace(":", "")[-6:]
    return f"Blue Connect {name}" if name else f"Blue Connect {suffix}"


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the polling options schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_UPDATE_INTERVAL,
                default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_UPDATE_INTERVAL,
                    max=MAX_UPDATE_INTERVAL,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="min",
                )
            ),
            vol.Optional(CONF_SALT_REFERENCE, default=0.0): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=20,
                    step=0.01,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="g/L",
                )
            ),
        }
    )


class BlueRiiotConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle setup of a BlueRiiot Bluetooth device."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> BlueRiiotOptionsFlow:
        """Return the options flow for an existing BlueRiiot entry."""
        return BlueRiiotOptionsFlow()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle a device found by Home Assistant Bluetooth."""
        address = _normalized_address(discovery_info.address)
        await self.async_set_unique_id(address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": _entry_title(discovery_info.name, address)
        }
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm setup of a discovered BlueRiiot."""
        if user_input is not None:
            address = _normalized_address(self._discovery_info.address)
            return self.async_create_entry(
                title=_entry_title(self._discovery_info.name, address),
                data={
                    CONF_ADDRESS: address,
                    CONF_DEVICE_NAME: self._discovery_info.name or "",
                },
                options={CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL},
            )
        return self.async_show_form(step_id="bluetooth_confirm")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Allow selecting a known Bluetooth device manually."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                address = _normalized_address(user_input[CONF_ADDRESS])
            except ValueError:
                errors["base"] = "invalid_address"
            else:
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=_entry_title(None, address),
                    data={CONF_ADDRESS: address},
                    options={CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL},
                )

        return self.async_show_form(
            step_id="user", data_schema=_address_schema(self.hass), errors=errors
        )


class BlueRiiotOptionsFlow(OptionsFlow):
    """Manage BlueRiiot options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure polling and optionally calibrate a salt sensor."""
        errors: dict[str, str] = {}
        if user_input is not None:
            options = dict(user_input)
            reference = float(options.pop(CONF_SALT_REFERENCE, 0))
            if reference > 0:
                reading = self.config_entry.runtime_data.data.reading
                if reading is None or reading.raw_salt <= 0:
                    errors[CONF_SALT_REFERENCE] = "no_salt_measurement"
                else:
                    options[CONF_SALT_DIVISOR] = reading.raw_salt / reference
            else:
                options[CONF_SALT_DIVISOR] = self.config_entry.options.get(
                    CONF_SALT_DIVISOR, DEFAULT_SALT_DIVISOR
                )
            if not errors:
                return self.async_create_entry(data=options)
        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self.config_entry.options)),
            errors=errors,
        )