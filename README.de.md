# BlueRiiot Bluetooth for Home Assistant

[English](README.md)

Eine vollständig lokale Home-Assistant-Integration für BlueRiiot-Geräte. Sie liest die Messwerte direkt per Bluetooth Low Energy (BLE), ohne Cloud-Zugang und ohne Abhängigkeit von anderen benutzerdefinierten Integrationen.

## Voraussetzungen

- Eine aktuelle Home-Assistant-Version mit aktivierter integrierter Bluetooth-Integration
- Ein BlueRiiot-Gerät in Reichweite
- Ein Bluetooth-Adapter in Home Assistant oder ein unterstützter Bluetooth-Proxy, der BLE-Verbindungen aufbauen kann

Home Assistant wählt automatisch den erreichbaren Adapter oder Proxy. Reine Advertisement-Scanner reichen nicht aus, weil die Integration eine GATT-Verbindung aufbauen muss.

## Installation mit HACS

1. In HACS **Integrationen** öffnen.
2. Über das Drei-Punkte-Menü **Benutzerdefiniertes Repository** wählen.
3. `https://github.com/lweberru/ha_blueriiot` mit Kategorie **Integration** eintragen.
4. **BlueRiiot Bluetooth** installieren und Home Assistant neu starten.
5. Unter **Einstellungen > Geräte & Dienste > Integration hinzufügen** nach **BlueRiiot Bluetooth** suchen.

Wird ein passendes Gerät per Bluetooth erkannt, zeigt Home Assistant automatisch einen Einrichtungsdialog. Die Erkennung nutzt den beworbenen Namen (`Blue Connect*` oder `BlueRiiot*`), die proprietäre GATT-Service-UUID oder das BlueRiiot-Herstellerdaten-Advertisement. Erkannte Geräte können auch im manuellen Einrichtungsdialog ausgewählt werden.

## Bereitgestellte Entities

Jedes eingerichtete Gerät wird als eigenes Home-Assistant-Geräteobjekt angelegt.

| Entity | Kategorie |
| --- | --- |
| Wassertemperatur | Messwert |
| pH-Wert | Messwert |
| Redoxpotential | Messwert |
| Salzgehalt | Messwert, wenn das Gerät einen Salzwert meldet |
| Leitfähigkeit | Messwert |
| Batterie | Diagnose |
| Direkt erreichbar | Diagnose |
| Bluetooth-Signalstärke | Diagnose |
| Letzte erfolgreiche Messung | Diagnose |
| Letzter Lesefehler | Diagnose |
| Jetzt messen | Diagnose-Schaltfläche |

Das Abfrageintervall kann in den Optionen der Integration zwischen 5 und 120 Minuten eingestellt werden. Die Schaltfläche **Jetzt messen** löst eine sofortige GATT-Abfrage aus.

Die Optionen erreichst du nach dem Einrichten in **Einstellungen > Geräte & Dienste > BlueRiiot Bluetooth > Konfigurieren**. Dort lassen sich das Abfrageintervall und bei Salzmodellen der Referenzwert zur Kalibrierung setzen.

Bei BlueRiiot-Modellen mit Salzsensor ist der Standard-Kalibrierfaktor `18`. Für eine Kalibrierung zuerst eine aktuelle Messung auslösen und dann unter den Integrationsoptionen den Salzgehalt einer verlässlichen Referenzmessung eingeben. Die Integration berechnet den Faktor einmalig aus dem aktuellen Rohwert; mit `0` bleibt er unverändert.

## Fehlerdiagnose

Bei Problemen zuerst den Bluetooth-Adapter bzw. Proxy und die Entfernung zum BlueRiiot prüfen. `Direkt erreichbar` wird erst nach einer erfolgreichen GATT-Abfrage eingeschaltet. Der Sensor `Letzter Lesefehler` zeigt die Klasse des letzten Bluetooth-Fehlers.

Für Debug-Logs in `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.blueriiot: debug
```

Danach Home Assistant neu starten und **BlueRiiot Bluetooth** unter **Integration hinzufügen** öffnen. Im Home-Assistant-Log erscheinen erkannte BlueRiiot-Geräte mit Name und Adresse. Die Adresse kann vor dem Teilen eines Logs geschwärzt werden.

## Entwicklung

Die Decoder-Tests kommen ohne Home-Assistant-Installation aus:

```sh
python3 -m unittest discover -s tests -v
```

Die Integration verwendet ausschließlich die Home-Assistant-Bluetooth-APIs und die in Home Assistant enthaltenen BLE-Abhängigkeiten.