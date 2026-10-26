"""BlueRiiot Bluetooth Low Energy GATT protocol."""

from __future__ import annotations

import asyncio

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import COMMAND_CHARACTERISTIC_UUID, NOTIFY_CHARACTERISTIC_UUID
from .decoder import BlueRiiotReading, decode_reading


class BlueRiiotClient:
    """Read a BlueRiiot through Home Assistant Bluetooth adapters or proxies."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self._hass = hass
        self._address = address

    async def async_read(self, *, salt_divisor: float) -> BlueRiiotReading:
        """Request and decode one measurement notification."""
        device = bluetooth.async_ble_device_from_address(
            self._hass, self._address, connectable=True
        )
        if device is None:
            # After startup or a long disconnection, AUTO scanners may only
            # have passive data. Wait for an active advertisement before GATT.
            try:
                await bluetooth.async_process_advertisements(
                    self._hass,
                    lambda service_info: True,
                    {"address": self._address, "connectable": True},
                    bluetooth.BluetoothScanningMode.ACTIVE,
                    timeout=20,
                )
            except TimeoutError as err:
                raise BlueRiiotDeviceNotFoundError(self._address) from err
            device = bluetooth.async_ble_device_from_address(
                self._hass, self._address, connectable=True
            )
            if device is None:
                raise BlueRiiotDeviceNotFoundError(self._address)

        notification = self._hass.loop.create_future()

        def handle_notification(_: int, payload: bytearray) -> None:
            if not notification.done():
                notification.set_result(bytes(payload))

        client = await establish_connection(
            BleakClientWithServiceCache,
            device,
            "BlueRiiot Bluetooth",
        )
        try:
            await client.start_notify(NOTIFY_CHARACTERISTIC_UUID, handle_notification)
            await client.write_gatt_char(
                COMMAND_CHARACTERISTIC_UUID, b"\x01", response=True
            )
            payload = await asyncio.wait_for(notification, timeout=20)
            return decode_reading(payload, salt_divisor=salt_divisor)
        finally:
            await client.disconnect()


class BlueRiiotDeviceNotFoundError(Exception):
    """Raised when the discovered device is not currently connectable."""
