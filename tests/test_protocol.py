"""Verify active discovery and cleanup using simulated Bluetooth backends."""

import asyncio
import ast
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).parents[1] / "custom_components/blueriiot"


class ProtocolTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bluetooth = NS(
            async_ble_device_from_address=Mock(return_value="device"),
            async_process_advertisements=AsyncMock(),
            BluetoothScanningMode=NS(ACTIVE="active"),
        )
        components = ModuleType("homeassistant.components")
        components.bluetooth = self.bluetooth
        core = ModuleType("homeassistant.core")
        core.HomeAssistant = object
        bleak = ModuleType("bleak_retry_connector")
        bleak.BleakClientWithServiceCache = object
        self.client = NS(start_notify=AsyncMock(), write_gatt_char=AsyncMock(), disconnect=AsyncMock())
        bleak.establish_connection = AsyncMock(return_value=self.client)
        self.establish = bleak.establish_connection
        package = ModuleType("test_blueriiot")
        package.__path__ = [str(ROOT)]
        modules = {"homeassistant": ModuleType("homeassistant"), "homeassistant.components": components,
                   "homeassistant.core": core, "bleak_retry_connector": bleak, "test_blueriiot": package}
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        self.addCleanup(self.modules.stop)
        spec = importlib.util.spec_from_file_location("test_blueriiot.protocol", ROOT / "protocol.py")
        self.protocol = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.protocol)
        self.reader = self.protocol.BlueRiiotClient(NS(loop=asyncio.get_running_loop()), "AA:BB:CC:DD:EE:FF")

    async def measure(self):
        def notify(uuid, callback):
            self.notify = callback

        async def write(*args, **kwargs):
            self.notify(0, bytearray(12))

        self.client.start_notify.side_effect = notify
        self.client.write_gatt_char.side_effect = write
        return await self.reader.async_read(salt_divisor=18)

    async def test_missing_device_requests_active_discovery_then_reads(self):
        self.bluetooth.async_ble_device_from_address.side_effect = [None, "device"]
        await self.measure()
        self.bluetooth.async_process_advertisements.assert_awaited_once()
        args, kwargs = self.bluetooth.async_process_advertisements.await_args
        self.assertEqual(args[2], {"address": "AA:BB:CC:DD:EE:FF", "connectable": True})
        self.assertEqual(args[3], "active")
        self.client.disconnect.assert_awaited_once()

    async def test_known_device_does_not_wait_for_another_scan(self):
        await self.measure()
        self.bluetooth.async_process_advertisements.assert_not_called()

    async def test_scan_timeout_does_not_open_a_connection(self):
        self.bluetooth.async_ble_device_from_address.return_value = None
        self.bluetooth.async_process_advertisements.side_effect = TimeoutError
        with self.assertRaises(self.protocol.BlueRiiotDeviceNotFoundError):
            await self.measure()
        self.establish.assert_not_called()

    async def test_unresolvable_device_after_scan_does_not_connect(self):
        self.bluetooth.async_ble_device_from_address.return_value = None
        with self.assertRaises(self.protocol.BlueRiiotDeviceNotFoundError):
            await self.measure()
        self.establish.assert_not_called()

    async def test_failed_notification_setup_disconnects(self):
        self.client.start_notify.side_effect = RuntimeError("notify failed")
        with self.assertRaises(RuntimeError):
            await self.reader.async_read(salt_divisor=18)
        self.client.disconnect.assert_awaited_once()

    async def test_setup_registers_active_interest_before_first_refresh(self):
        unsubscribe = Mock()
        self.bluetooth.async_register_callback = Mock(return_value=unsubscribe)

        async def first_refresh():
            self.bluetooth.async_register_callback.assert_called_once()

        coordinator = NS(address="AA:BB:CC:DD:EE:FF", async_config_entry_first_refresh=first_refresh)
        entry = NS(data={}, title="Blue Connect DDEEFF", runtime_data=None,
                   async_on_unload=Mock(), add_update_listener=Mock())
        hass = NS(config_entries=NS(async_forward_entry_setups=AsyncMock()))
        tree = ast.parse((ROOT / "__init__.py").read_text())
        tree.body = [node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry"]
        namespace = {"HomeAssistant": object, "BlueRiiotConfigEntry": object,
                     "BlueRiiotCoordinator": lambda hass, entry: coordinator,
                     "CONF_DEVICE_NAME": "device_name", "PLATFORMS": [],
                     "bluetooth": self.bluetooth, "_async_update_listener": Mock()}
        exec(compile(tree, "__init__.py", "exec"), namespace)
        await namespace["async_setup_entry"](hass, entry)
        args = self.bluetooth.async_register_callback.call_args.args
        self.assertEqual(args[2], {"address": "AA:BB:CC:DD:EE:FF", "connectable": True})
        self.assertEqual(args[3], "active")
        entry.async_on_unload.assert_any_call(unsubscribe)


if __name__ == "__main__":
    unittest.main()
