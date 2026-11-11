# ha-fronius-peakshaving

[🇬🇧 English](README.md) · 🇩🇪 Deutsch

Ein Home-Assistant-Package, das den **Netzbezug pro Viertelstunde** (z. B. auf 500 Wh) mit einem **Fronius-Gen24-Wechselrichter und Batterie** begrenzt. Würde das Haus mehr als das Budget beziehen, entlädt die Batterie genau so viel wie nötig. Ist im Budget noch Platz, kann sie optional aus dem Netz laden.

Die Batterie wird über die Entitäten der Integration [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) (Modbus) gesteuert.

## Warum energiebasiert?

Spitzenlast-Tarife und Bezugsgrenzen sind als **Energie pro Intervall** (Wh pro 15 min) definiert, nicht als Leistung. Das Package arbeitet deshalb mit Energiezählern:

- Der bisherige Netzbezug der laufenden Viertelstunde kommt aus einem `utility_meter` auf dem Bezugszähler. Auch eine Spitze von wenigen Sekunden wird exakt mitgezählt.
- Der aktuelle Bedarf ist der Mittelwert der letzten ~60 s, berechnet aus der integrierten Leistung (Energie) für Netzbezug und Batterie-Laden/Entladen. Keine momentanen Leistungswerte, daher stören träge oder sprunghafte Leistungsmesswerte nicht.
- Hysterese in Watt statt Wartezeiten: Die Batterie reagiert sofort, springt aber nicht zwischen Laden und Entladen hin und her.
- Am Anfang jeder Viertelstunde locker, am Ende streng – damit das Budget auch genutzt wird.

## Funktionen

- Max. Netzbezug pro 15 min, zur Laufzeit einstellbar (Helfer „Max. Bezug pro 15 min“)
- Batterie entlädt nur so viel wie nötig (Entladelimit in Watt)
- Optional Netzladen im freien Budget, mit Start-/Ziel-SoC-Hysterese
- Vier Leerlaufmodi: `sperren` (Entladen blockieren), `auto` (normale Eigenverbrauchsoptimierung), `auto_mit_reserve` (Eigenverbrauch, hält aber einen Reserve-SoC für Spitzen), `auto_nach_budget` (wie `auto_mit_reserve`, aber der Reservebereich entlädt erst, wenn das 15-min-Budget aufgebraucht ist)
- Fail-safe: Fehlt ein Sensorwert, schaltet der Wechselrichter zurück auf `auto`
- Status-Helfer `input_select.fronius_zustand` zeigt, was die Regelung gerade tut

> Die Helfernamen und `name:`-Texte im YAML sind deutsch, weil das Package für eine deutschsprachige Installation geschrieben wurde. Die Entity-IDs leiten sich von Schlüsseln/Namen ab und werden in der Dokumentation verwendet. Anzeigenamen der Helfer dürfen geändert werden; die Statistik- und Template-Sensoren aber **nicht** umbenennen.

## Voraussetzungen

- Fronius Gen24 (getestet: Symo GEN24 8.0) mit Batterie und Smart Meter am Netzanschluss
- [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) (nicht das nur lesende `ha-sunspec` von CJNE) mit den Batterie-Steuerentitäten
- Modbus TCP am Wechselrichter aktiv, Steuerung erlaubt. Der Wechselrichter akzeptiert nur **eine** Modbus-Verbindung
- Home Assistant **2024.10 oder neuer** (Syntax `triggers:` / `trigger:`)

## Schnellstart

1. Packages in der `configuration.yaml` aktivieren:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. [`packages/fronius_peakshaving.yaml`](packages/fronius_peakshaving.yaml) nach `<config>/packages/` kopieren.
3. **Die 9 Entity-IDs** am Dateianfang durch die eigenen ersetzen (Suchen & Ersetzen).
4. Zähler und Bedarfssensor prüfen (siehe [Einrichtung](docs/de/einrichtung.md)), Home Assistant neu starten.
5. Helfer einstellen (Startwerte in der Einrichtungsanleitung), `Fronius: Bezugsbegrenzung aktiv` einschalten.

## Dokumentation

| | Deutsch | English |
|---|---|---|
| Funktionsweise (Formeln, Zustände) | [funktionsweise](docs/de/funktionsweise.md) | [how-it-works](docs/en/how-it-works.md) |
| Einrichtung und Prüfung | [einrichtung](docs/de/einrichtung.md) | [setup](docs/en/setup.md) |
| Feinabstimmung und Fehlersuche | [feinabstimmung-fehlersuche](docs/de/feinabstimmung-fehlersuche.md) | [tuning-troubleshooting](docs/en/tuning-troubleshooting.md) |

Ein Dashboard zum Steuern und Testen liegt in [`dashboard/`](dashboard/fronius_peakshaving_dashboard.yaml).

Eine kleine Simulation der Viertelstundenlogik liegt in [`simulation/sim_budget.py`](simulation/sim_budget.py).

## 🤖 Entstehung

Der Code und die Dokumentation in diesem Repository wurden von einem KI-Assistenten (Claude von Anthropic) erstellt. Der Maintainer hat den Code nicht selbst geschrieben, sondern auf seiner eigenen Anlage getestet und mit seinem Feedback die Gestaltung mitbestimmt. Bitte den Code vor der Nutzung selbst prüfen.

## ⚠️ Haftungsausschluss

Entwickelt und getestet auf **einer Anlage** (Symo GEN24 8.0 mit ha-sunspec2). Das Package schreibt in die Batteriesteuerung des Wechselrichters. Bitte vorsichtig testen: zuerst mit ausgeschaltetem Hauptschalter und beobachteten Entitäten, dann mit niedrigem Limit. Prüfen, ob der Rückfall über die „Battery rate revert time“ bei dir funktioniert. Nutzung auf eigene Gefahr, siehe [MIT-Lizenz](LICENSE). Unabhängiges Projekt, nicht mit Fronius verbunden.

## Danksagung

- [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) von hilman2 für die Modbus/SunSpec-Integration
- Home-Assistant-Integrationen `utility_meter` und `statistics`

## Lizenz

[MIT](LICENSE)
