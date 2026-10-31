"""Verify retry scheduling and connectivity with a simulated HA coordinator."""

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).parents[1] / "custom_components/blueriiot"
NOW = datetime(2026, 10, 31, 12, tzinfo=timezone.utc)


class CoordinatorTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        class Coordinator:
            def __class_getitem__(cls, item):
                return cls

            def __init__(self, hass, logger, **kwargs):
                self.hass = hass
                self.update_interval = kwargs["update_interval"]
                self.data = None

        package = ModuleType("retry_blueriiot")
        package.__path__ = [str(ROOT)]
        modules = {"retry_blueriiot": package}
        definitions = {
            "homeassistant": {},
            "homeassistant.components": {"bluetooth": NS(async_discovered_service_info=lambda *a, **kw: [])},
            "homeassistant.config_entries": {"ConfigEntry": object},
            "homeassistant.const": {"CONF_ADDRESS": "address"},
            "homeassistant.core": {"HomeAssistant": object},
            "homeassistant.helpers": {},
            "homeassistant.helpers.device_registry": {"format_mac": lambda value: value},
            "homeassistant.helpers.update_coordinator": {"DataUpdateCoordinator": Coordinator},
            "homeassistant.util": {"dt": NS(utcnow=lambda: NOW)},
            "retry_blueriiot.config_flow": {"CONF_UPDATE_INTERVAL": "update_interval"},
            "retry_blueriiot.protocol": {"BlueRiiotClient": lambda *a: NS(async_read=AsyncMock())},
        }
        for name, attrs in definitions.items():
            modules[name] = ModuleType(name)
            modules[name].__dict__.update(attrs)
        self.patch = patch.dict(sys.modules, modules)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        spec = importlib.util.spec_from_file_location("retry_blueriiot.coordinator", ROOT / "coordinator.py")
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.module
        spec.loader.exec_module(self.module)
        self.entry = NS(data={"address": "AA:BB:CC:DD:EE:FF"}, options={})
        self.coordinator = self.module.BlueRiiotCoordinator(NS(), self.entry)

    async def refresh(self):
        self.coordinator.data = await self.coordinator._async_update_data()
        return self.coordinator.data

    async def test_timeout_preserves_reading_then_recovers_after_fast_retry(self):
        c = self.coordinator
        reading = object()
        c._client.async_read.side_effect = [reading, TimeoutError(), reading]
        await self.refresh()
        success = c.data.last_success
        await self.refresh()
        self.assertIs(c.data.reading, reading)
        self.assertEqual(c.data.last_success, success)
        self.assertEqual(c.data.last_error, "TimeoutError")
        self.assertEqual(c.update_interval, timedelta(minutes=1))
        self.assertTrue(c.connected)
        await self.refresh()
        self.assertIsNone(c.data.last_error)
        self.assertEqual(c.update_interval, timedelta(minutes=15))
        # A new isolated failure receives a fresh retry budget.
        c._client.async_read.side_effect = TimeoutError()
        await self.refresh()
        self.assertEqual(c.update_interval, timedelta(minutes=1))

    async def test_persistent_failure_limits_fast_retries_and_remains_disconnected(self):
        c = self.coordinator
        c._client.async_read.side_effect = TimeoutError()
        for minutes in (1, 1, 15, 1):
            await self.refresh()
            self.assertEqual(c.update_interval, timedelta(minutes=minutes))
            self.assertFalse(c.connected)
            self.assertIsNone(c.data.reading)

    async def test_grace_uses_configured_interval_during_fast_retries(self):
        self.entry.options["update_interval"] = 60
        c = self.module.BlueRiiotCoordinator(NS(), self.entry)
        c._last_success = NOW - timedelta(minutes=124)
        c._client.async_read.side_effect = TimeoutError()
        c.data = await c._async_update_data()
        self.assertEqual(c.update_interval, timedelta(minutes=1))
        self.assertTrue(c.connected)
        self.assertEqual(c.data.maximum_age, timedelta(minutes=125))

    def test_connectivity_boundaries(self):
        c = self.coordinator
        for age, expected in ((-1, False), (30, True), (34, True), (35, True), (36, False)):
            with self.subTest(age=age):
                c.data = self.module.BlueRiiotData(None, NOW - timedelta(minutes=age), None, None)
                self.assertEqual(c.connected, expected)
