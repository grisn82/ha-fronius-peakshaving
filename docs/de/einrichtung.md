# Einrichtung

[English](../en/setup.md)

## 1. Wechselrichter und Integration

1. **Modbus TCP** am Wechselrichter aktivieren (Weboberfläche → Kommunikation → Modbus) und Steuerung erlauben. Der Wechselrichter unterstützt nur eine Modbus-Verbindung, es darf also kein anderer Modbus-Client verbunden sein.
2. [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) installieren und einrichten. Benötigt werden diese Batterie-Steuerentitäten (Namen je nach Gerät):
   - Select „Batterie-Betriebsart“ mit den Optionen `auto`, `discharge_limit`, `charge_from_grid`, `block_discharging`
   - Number-Entitäten: Entladelimit (W), Netzladeleistung (W), max. Ladeleistung (`WChaMax`, W)
   - Schalter „Batterieladen aus dem Netz erlaubt“
   - **Wechselrichter und Smart Meter als zwei getrennte Geräte** in ha-sunspec2 einbinden (zwei Integrationseinträge). Der Wechselrichter hat die Modbus-Unit-ID **1**, der Smart Meter die Unit-ID **200**. Das sind die Standardwerte; auf der eigenen Anlage prüfen.
   - Der Autor hat das Abfrageintervall auf **5 Sekunden** gesetzt. Ein kurzes Intervall liefert aktuellere Werte; das Package funktioniert auch mit langsamerer Abfrage (das 60-s-Statistikfenster enthält dann weniger Werte).
3. Ladepläne des Wechselrichters und die Entität „Battery plan“ von ha-sunspec2 ausschalten, sonst konkurrieren sie mit diesem Package.
4. **„Battery rate revert time“** setzen (z. B. 60 s). Sendet Home Assistant nicht mehr, soll der Wechselrichter in den Automatikmodus zurückfallen. Die Automation sendet den Modus alle 10 s neu. Den Rückfall durch einen Test prüfen, denn die Anzeige der Revert Time kann sich bei manchen Setups selbst auf 0 zurücksetzen.
5. Für Netzladen: im Wechselrichter erlauben und den ha-sunspec2-Schalter „Batterieladen aus dem Netz erlaubt“ einschalten.

## 2. Package installieren

Einmalig in die `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

`packages/fronius_peakshaving.yaml` nach `<config>/packages/` kopieren.

## 3. Entity-IDs anpassen

Diese 8 IDs in der Datei ersetzen (Suchen & Ersetzen):

| Zweck | ID des Autors (ersetzen) |
|---|---|
| Batteriemodus (Select) | `select.symo_gen24_8_0_storage_batterie_betriebsart` |
| Entladelimit (W) | `number.symo_gen24_8_0_storage_batterie_entladelimit` |
| Netzladeleistung (W) | `number.symo_gen24_8_0_storage_batterie_netzladeleistung` |
| max. Batterieleistung (W) | `number.symo_gen24_8_0_storage_batterie_ladeleistung_max` |
| Batterie-SoC (%) | `sensor.sunspecfronius_storage_chastate` |
| Netzbezugszähler (Wh) | `sensor.sunspecfronius_sm_meter_three_phase_wye_total_watt_hours_imported` |
| Batterie-**Ladeleistung** (W) | `sensor.sunspecfronius_mppt_module_2_dc_power` |
| Batterie-**Entladeleistung** (W) | `sensor.sunspecfronius_mppt_module_3_dc_power` |

⚠️ Die beiden Batteriesensoren sind die DC-Leistung zweier Kanäle (MPPT-„Module“), in W und positiv. Beim Autor ist Modul 2 die Batterieladung und Modul 3 die Entladung. **Bei dir kann es umgekehrt sein.** Prüfen, welcher Sensor einen Wert zeigt, während die Batterie lädt bzw. entlädt.

Das Package integriert diese Leistungen zu Energie (`sensor.fronius_batterie_ladeenergie` / `..._entladeenergie`). Die `lifetime_energy`-Zähler derselben Module werden bewusst **nicht** verwendet: Sie aktualisieren sich nur etwa alle 5 Minuten und verursachten falsche Bedarfsspitzen.

Hinweis: Der Bezugszähler kommt in der Datei mehrfach vor (utility_meter, Statistik-Sensor, Automation).

## 4. Vor dem Einschalten prüfen

1. Entwicklerwerkzeuge → Zustände: Der Netzbezugszähler muss eine Zahl sein und beim Netzbezug steigen. Nach einem Neustart beginnen die Integralsensoren `sensor.fronius_batterie_ladeenergie` und `sensor.fronius_batterie_entladeenergie` zu zählen: der erste steigt beim Laden, der zweite beim Entladen.
2. Nach einem Neustart 1–2 Minuten warten. Dann muss `sensor.fronius_bedarf_energie` den **Hausverbrauch minus PV** in Watt zeigen. Mit dem realen Wert in drei Situationen vergleichen:
   - Batterie im Leerlauf
   - Batterie lädt
   - Batterie entlädt

   Der Wert muss in allen drei Fällen ungefähr gleich sein. Springt er beim Richtungswechsel der Batterie um die doppelte Batterieleistung, sind Lade- und Entladezähler vertauscht.
3. Falls dein Netzbezugszähler in kWh statt Wh misst, im Bedarfssensor für den Bezugsterm `3600` durch `3600000` ersetzen. Die Batterieleistungssensoren müssen in W messen (bei kW wäre das Integral in kWh).
4. `sensor.fronius_bezug_viertelstunde` muss bei :00, :15, :30, :45 zurückgesetzt werden und den Bezug in Wh zählen.

## 5. Startwerte

| Helfer | Startwert |
|---|---|
| Max. Bezug pro 15 min | 500 Wh |
| Sicherheitsreserve | 50 Wh |
| Mindest-SoC für Entladen | 15 % |
| Reserve-SoC für Spitzen | 25 % |
| Netzladen startet unter SoC | 20 % |
| Netzladen endet bei SoC | 25 % |
| Prognosegewicht am Anfang | 0,6 (1 = streng) |
| Leerlaufmodus | `auto_mit_reserve` |
| Netzladen im freien Budget erlaubt | zunächst aus |

Den Reserve-SoC nach den eigenen Spitzen wählen: Eine kurze Spitze von einigen hundert Wh braucht nur wenige Prozent der Batterie.

## 6. Dashboard (optional)

[`dashboard/fronius_peakshaving_dashboard.yaml`](../../dashboard/fronius_peakshaving_dashboard.yaml) ist ein Dashboard zum Steuern und Testen: Schalter (Regelung, Netzladen, Leerlaufmodus), alle Konfigurationshelfer, der Zustandsverlauf und Live-Werte. Es verwendet Entitäten der Anlage des Autors; die anzupassenden Entitäten stehen am Dateianfang. Neues Dashboard anlegen, den Raw-Konfigurationseditor öffnen und die Datei einfügen. `sensor.leistung_verbrauch` ist ein eigener Verbrauchssensor des Autors und nicht Teil des Packages; Kachel und Graphzeile löschen oder ersetzen, falls du keinen solchen Sensor hast.

## 7. Optional: Batterie-Gesundheitszustand

[`packages/fronius_byd_soh.yaml`](../../packages/fronius_byd_soh.yaml) ergänzt einen REST-Sensor `sensor.byd_batterie_state_of_health` (SoH der Batterie in %), der im Dashboard angezeigt wird. Er liest einmal am Tag die Weboberfläche des Wechselrichters. `[Gen24-IP]` durch die IP-Adresse des Wechselrichters ersetzen. Diese Schnittstelle ist inoffiziell und undokumentiert und wurde nur mit einer BYD-Batterie getestet; sie kann sich mit Firmware-Updates ändern, und der Sensor bleibt leer, wenn die Batterie den SoH-Kanal nicht meldet. Die Regelung hängt nicht davon ab.

## 8. Einschalten

1. Home Assistant neu starten (die neuen `statistics`- und `utility_meter`-Plattformen brauchen einen Neustart).
2. Mit eingeschaltetem `Fronius: Bezugsbegrenzung aktiv` `input_select.fronius_zustand` und den Wechselrichtermodus beobachten.
3. Mit niedrigem Limit (z. B. 100 Wh) und einer bekannten Last testen und prüfen, dass die Batterie entlädt.
4. Den Rückfall testen: Hauptschalter ausschalten und prüfen, dass der Modus auf `auto` zurückgeht.
