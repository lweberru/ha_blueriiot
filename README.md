# BlueRiiot Bluetooth for Home Assistant

[Deutsch](README.de.md)

A fully local Home Assistant integration for BlueRiiot devices. It reads measurements directly over Bluetooth Low Energy (BLE), without cloud access or dependencies on other custom integrations.

## Requirements

- A current Home Assistant release with the built-in Bluetooth integration enabled
- A BlueRiiot device within Bluetooth range
- A Bluetooth adapter connected to Home Assistant or a supported Bluetooth proxy that can make BLE connections

The integration does not require Home Assistant `2026.8.1`; that version was only used during development. It has been tested with Home Assistant `2026.8.1`. Home Assistant automatically chooses a reachable adapter or proxy. Advertisement-only scanners cannot read measurements because the integration needs to open a GATT connection.

## HACS Installation

1. Open **Integrations** in HACS.
2. Select **Custom repositories** from the three-dot menu.
3. Add `https://github.com/lweberru/ha_blueriiot` as an **Integration** repository.
4. Install **BlueRiiot Bluetooth** and restart Home Assistant.
5. Go to **Settings > Devices & services > Add integration** and search for **BlueRiiot Bluetooth**.

When a matching device is discovered, Home Assistant shows a setup dialog automatically. Discovery uses the advertised name (`Blue Connect*` or `BlueRiiot*`), the proprietary GATT service UUID, or the BlueRiiot manufacturer-data advertisement. Discovered devices can also be selected from the manual setup dialog.

## Entities

Each configured device is added as a separate Home Assistant device.

| Entity | Category |
| --- | --- |
| Water temperature | Measurement |
| pH | Measurement |
| Oxidation reduction potential | Measurement |
| Salt concentration | Measurement, when reported by the device |
| Conductivity | Measurement |
| Battery | Diagnostic |
| Directly reachable | Diagnostic |
| Bluetooth signal strength | Diagnostic |
| Last successful reading | Diagnostic |
| Last read error | Diagnostic |
| Measure now | Diagnostic button |

The polling interval can be set between 5 and 120 minutes in the integration options. **Measure now** triggers an immediate GATT request.

After setup, open **Settings > Devices & services > BlueRiiot Bluetooth > Configure** to change the polling interval or, for salt models, provide a calibration reference value.

For BlueRiiot models with a salt sensor, the default calibration divisor is `18`. To calibrate it, trigger a current reading and enter a reliable reference salt concentration in the integration options. The integration derives and stores the divisor from the latest raw value; enter `0` to keep the current calibration.

## Troubleshooting

First check the Bluetooth adapter or proxy and its distance from the BlueRiiot device. `Directly reachable` turns on only after a successful GATT request. The `Last read error` sensor reports the class of the most recent Bluetooth error.

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.blueriiot: debug
```

Restart Home Assistant and open **BlueRiiot Bluetooth** from **Add integration**. The Home Assistant log will show discovered BlueRiiot devices with their name and address. Redact the address before sharing logs.

## Development

The decoder tests do not require a Home Assistant installation:

```sh
python3 -m unittest discover -s tests -v
```

The integration only uses Home Assistant Bluetooth APIs and BLE dependencies included with Home Assistant.
