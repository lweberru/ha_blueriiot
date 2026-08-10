"""Tests for the dependency-free BlueRiiot packet decoder."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


DECODER_PATH = Path(__file__).parents[1] / "custom_components/blueriiot/decoder.py"
SPEC = importlib.util.spec_from_file_location("blueriiot_decoder", DECODER_PATH)
assert SPEC and SPEC.loader
DECODER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DECODER
SPEC.loader.exec_module(DECODER)


class BlueRiiotDecoderTest(unittest.TestCase):
    """Verify the binary frame formulas and salt capability inference."""

    def test_decodes_measurement_frame(self) -> None:
        """A complete frame is decoded using the BlueRiiot formulas."""
        payload = bytes([0]) + (2534).to_bytes(2, "little", signed=True)
        payload += (2048).to_bytes(2, "little", signed=True)
        payload += (386).to_bytes(2, "little", signed=True)
        payload += (115).to_bytes(2, "little", signed=True)
        payload += (4134).to_bytes(2, "little", signed=True)
        payload += bytes([16])

        reading = DECODER.decode_reading(payload)

        self.assertEqual(reading.temperature, 25.34)
        self.assertEqual(reading.ph, 7.0)
        self.assertAlmostEqual(reading.orp, 78.42, places=2)
        self.assertAlmostEqual(reading.salt, 115 / 18)
        self.assertEqual(reading.raw_salt, 115)
        self.assertAlmostEqual(reading.conductivity, 1000.0)
        self.assertAlmostEqual(reading.battery, 16 / 36 * 100)
        self.assertTrue(reading.has_salt_sensor)

    def test_uses_custom_salt_calibration(self) -> None:
        """A calibrated divisor is applied without changing other measurements."""
        payload = bytes([0]) + (2500).to_bytes(2, "little", signed=True)
        payload += (2048).to_bytes(2, "little", signed=True)
        payload += (0).to_bytes(2, "little", signed=True)
        payload += (100).to_bytes(2, "little", signed=True)
        payload += (0).to_bytes(2, "little", signed=True)
        payload += bytes([36])

        reading = DECODER.decode_reading(payload, salt_divisor=20)

        self.assertEqual(reading.salt, 5.0)
        self.assertEqual(reading.battery, 100.0)

    def test_rejects_incomplete_frame(self) -> None:
        """A short notification cannot be interpreted as a measurement."""
        with self.assertRaisesRegex(ValueError, "incomplete_payload_11"):
            DECODER.decode_reading(bytes(11))

    def test_detects_device_without_salt_measurement(self) -> None:
        """Zero salt and conductivity mean no usable salt measurement."""
        payload = bytes([0]) + (2500).to_bytes(2, "little", signed=True)
        payload += (2048).to_bytes(2, "little", signed=True)
        payload += (0).to_bytes(2, "little", signed=True) * 3
        payload += bytes([90])

        self.assertFalse(DECODER.decode_reading(payload).has_salt_sensor)
