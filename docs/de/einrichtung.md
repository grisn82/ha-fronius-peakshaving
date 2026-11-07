# Einrichtung

[English](../en/setup.md)

## 1. Wechselrichter und Integration

1. **Modbus TCP** am Wechselrichter aktivieren (Weboberfläche → Kommunikation → Modbus) und Steuerung erlauben. Der Wechselrichter unterstützt nur eine Modbus-Verbindung, es darf also kein anderer Modbus-Client verbunden sein.
2. [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) installieren und einrichten. Benötigt werden diese Batterie-Steuerentitäten (Namen je nach Gerät):
   - Select „Batterie-Betriebsart“ mit den Optionen `auto`, `discharge_limit`, `charge_from_grid`, `block_discharging`
   - Number-Entitäten: Entladelimit (W), Netzladeleistung (W), max. Ladeleistung (`WChaMax`, W)
   - Schalter „Batterieladen aus dem Netz erlaubt“
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
| Batterie **geladene** Energie (Wh) | `sensor.sunspecfronius_mppt_module_2_lifetime_energy` |
| Batterie **entladene** Energie (Wh) | `sensor.sunspecfronius_mppt_module_3_lifetime_energy` |

⚠️ Die beiden Batteriezähler sind die Lifetime-Energien zweier DC-Kanäle (MPPT-„Module“). Beim Autor ist Modul 2 die Batterieladung und Modul 3 die Entladung. **Bei dir kann es umgekehrt sein.** Prüfen, welcher Zähler steigt, während die Batterie lädt bzw. entlädt.

Hinweis: Der Bezugszähler kommt in der Datei mehrfach vor (utility_meter, Statistik-Sensor, Automation).

## 4. Vor dem Einschalten prüfen

1. Entwicklerwerkzeuge → Zustände: Alle drei Zähler müssen Zahlen sein und steigen (Bezugszähler beim Netzbezug, Ladezähler beim Laden, Entladezähler beim Entladen).
2. Nach einem Neustart 1–2 Minuten warten. Dann muss `sensor.fronius_bedarf_energie` den **Hausverbrauch minus PV** in Watt zeigen. Mit dem realen Wert in drei Situationen vergleichen:
   - Batterie im Leerlauf
   - Batterie lädt
   - Batterie entlädt

   Der Wert muss in allen drei Fällen ungefähr gleich sein. Springt er beim Richtungswechsel der Batterie um die doppelte Batterieleistung, sind Lade- und Entladezähler vertauscht.
3. Falls deine Zähler in kWh statt Wh messen, im Bedarfssensor `3600` durch `3600000` ersetzen.
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

## 6. Einschalten

1. Home Assistant neu starten (die neuen `statistics`- und `utility_meter`-Plattformen brauchen einen Neustart).
2. Mit eingeschaltetem `Fronius: Bezugsbegrenzung aktiv` `input_select.fronius_zustand` und den Wechselrichtermodus beobachten.
3. Mit niedrigem Limit (z. B. 100 Wh) und einer bekannten Last testen und prüfen, dass die Batterie entlädt.
4. Den Rückfall testen: Hauptschalter ausschalten und prüfen, dass der Modus auf `auto` zurückgeht.
