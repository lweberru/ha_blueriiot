"""Decode BlueRiiot measurement frames without Bluetooth dependencies."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BlueRiiotReading:
    """Measurements decoded from one BlueRiiot GATT notification."""

    temperature: float
    ph: float
    orp: float
    salt: float
    raw_salt: int
    conductivity: float
    battery: float

    @property
    def has_salt_sensor(self) -> bool:
        """Return whether the device reports a salt measurement."""
        return self.raw_salt > 0


def decode_reading(payload: bytes, *, salt_divisor: float = 18.0) -> BlueRiiotReading:
    """Decode the documented 12-byte BlueRiiot measurement frame."""
    if len(payload) < 12:
        raise ValueError(f"incomplete_payload_{len(payload)}")
    if salt_divisor <= 0:
        raise ValueError("invalid_salt_divisor")

    def int16(offset: int) -> int:
        return int.from_bytes(payload[offset : offset + 2], "little", signed=True)

    raw_ph = float(int16(3))
    raw_salt = int16(7)
    return BlueRiiotReading(
        temperature=int16(1) / 100.0,
        ph=(2048.0 - raw_ph) / 232.0 + 7.0,
        orp=int16(5) / 3.86 - 21.57826,
        salt=raw_salt / salt_divisor,
        raw_salt=raw_salt,
        conductivity=int16(9) / 4.134,
        battery=min(100.0, max(0.0, payload[11] / 36.0 * 100.0)),
    )
