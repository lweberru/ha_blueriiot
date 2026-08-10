# BlueRiiot Bluetooth for Home Assistant

Eine vollstandig lokale Home-Assistant-Integration fur BlueRiiot-Gerate. Sie liest die Messwerte direkt per Bluetooth Low Energy (BLE), ohne Cloud-Zugang und ohne Abhangigkeit von anderen benutzerdefinierten Integrationen.

## Voraussetzungen

- Home Assistant `2026.8.1` oder neuer
- Ein BlueRiiot-Gerat in Reichweite
- Ein Bluetooth-Adapter in Home Assistant oder ein unterstutzter Bluetooth Proxy

Home Assistant wahlt automatisch den erreichbaren Adapter oder Proxy. Der Proxy muss die Verbindung zu BLE-Geraten unterstutzen; reine Advertisement-Scanner reichen nicht aus.

## Installation mit HACS

1. In HACS **Integrationen** offnen.
2. Uber das Drei-Punkte-Menu **Benutzerdefiniertes Repository** wahlen.
3. `https://github.com/lweberru/ha_blueriiot` mit Kategorie **Integration** eintragen.
4. **BlueRiiot Bluetooth** installieren und Home Assistant neu starten.
5. Unter **Einstellungen > Gerate & Dienste > Integration hinzufugen** nach **BlueRiiot Bluetooth** suchen.

Wird ein passendes Gerat per Bluetooth erkannt, zeigt Home Assistant automatisch einen Einrichtungsdialog. Die Erkennung nutzt den beworbenen Namen (`Blue Connect*` oder `BlueRiiot*`) und, falls vorhanden, die proprietare GATT-Service-UUID. Alternativ konnen erkannte Gerate im Dialog ausgewahlt oder ihre Bluetooth-Adresse manuell eingetragen werden.

## Bereitgestellte Entities

Jedes eingerichtete Gerat wird als eigenes Home-Assistant-Gerateobjekt angelegt.

| Entity | Kategorie |
| --- | --- |
| Wassertemperatur | Messwert |
| pH-Wert | Messwert |
| Redoxpotential | Messwert |
| Salzgehalt | Messwert, wenn das Gerat einen Salzwert meldet |
| Leitfahigkeit | Messwert |
| Batterie | Diagnose |
| Direkt erreichbar | Diagnose |
| Bluetooth-Signalstarke | Diagnose |
| Letzte erfolgreiche Messung | Diagnose |
| Letzter Lesefehler | Diagnose |
| Jetzt messen | Diagnose-Schaltflache |

Das Abfrageintervall kann in den Optionen der Integration zwischen 5 und 120 Minuten eingestellt werden. Die Schaltflache **Jetzt messen** lost eine sofortige GATT-Abfrage aus.

Bei BlueRiiot-Modellen mit Salzsensor ist der Standard-Kalibrierfaktor `18`. Fur eine Kalibrierung zuerst eine aktuelle Messung auslosen und dann unter den Integrationsoptionen den Salzgehalt einer verlasslichen Referenzmessung eingeben. Die Integration berechnet den Faktor einmalig aus dem aktuellen Rohwert; mit `0` bleibt er unverandert.

## Fehlerdiagnose

Bei Problemen zuerst den Bluetooth-Adapter bzw. Proxy und die Entfernung zum BlueRiiot prufen. `Direkt erreichbar` wird erst nach einer erfolgreichen GATT-Abfrage eingeschaltet. Der Sensor `Letzter Lesefehler` zeigt die Klasse des letzten Bluetooth-Fehlers.

Fur Debug-Logs in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.blueriiot: debug
```

Danach Home Assistant neu starten und **BlueRiiot Bluetooth** unter **Integration hinzufugen** offnen. Im Home-Assistant-Log erscheinen die vom Bluetooth-Scanner bekannten Geraete mit Name, Adresse, Service-UUIDs und Herstellerdaten. Die Adresse kann vor dem Teilen eines Logs geschwarzt werden.

## Entwicklung

Die Decoder-Tests kommen ohne Home-Assistant-Installation aus:

```sh
python3 -m unittest discover -s tests -v
```

Die Integration verwendet ausschliesslich die Home-Assistant-Bluetooth-APIs und die in Home Assistant enthaltenen BLE-Abhangigkeiten.