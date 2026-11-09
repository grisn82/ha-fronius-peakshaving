# Setup

[Deutsch](../de/einrichtung.md)

## 1. Inverter and integration

1. Enable **Modbus TCP** on the inverter (web interface → Communication → Modbus) and allow control. The inverter supports only one Modbus connection, so no other Modbus client may be connected.
2. Install and configure [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2). You need these battery control entities (names depend on your device):
   - select "Batterie-Betriebsart" with the options `auto`, `discharge_limit`, `charge_from_grid`, `block_discharging`
   - number entities: discharge limit (W), grid charge power (W), max. charge power (`WChaMax`, W)
   - switch "Battery charging from grid allowed"
3. Turn off inverter charge schedules and the "Battery plan" entity of ha-sunspec2, otherwise they compete with this package.
4. Set **"Battery rate revert time"** (e.g. 60 s). If Home Assistant stops sending, the inverter should fall back to automatic mode. The automation resends the mode every 10 s. Verify the fallback by a test, as the revert time display may reset itself to 0 on some setups.
5. For grid charging: allow it in the inverter settings and turn on the ha-sunspec2 switch "Battery charging from grid allowed".

## 2. Install the package

Add to `configuration.yaml` (once):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Copy `packages/fronius_peakshaving.yaml` into `<config>/packages/`.

## 3. Adjust the entity IDs

Replace these 8 IDs in the file (search & replace):

| Purpose | Author's ID (replace) |
|---|---|
| battery mode (select) | `select.symo_gen24_8_0_storage_batterie_betriebsart` |
| discharge limit (W) | `number.symo_gen24_8_0_storage_batterie_entladelimit` |
| grid charge power (W) | `number.symo_gen24_8_0_storage_batterie_netzladeleistung` |
| max. battery power (W) | `number.symo_gen24_8_0_storage_batterie_ladeleistung_max` |
| battery SoC (%) | `sensor.sunspecfronius_storage_chastate` |
| grid import counter (Wh) | `sensor.sunspecfronius_sm_meter_three_phase_wye_total_watt_hours_imported` |
| battery **charge** power (W) | `sensor.sunspecfronius_mppt_module_2_dc_power` |
| battery **discharge** power (W) | `sensor.sunspecfronius_mppt_module_3_dc_power` |

⚠️ The two battery sensors are the DC power of two channels (MPPT "modules"), in W and positive. On the author's system module 2 is the battery charge and module 3 the discharge. **On your system it may be the other way round.** Check by watching which sensor shows a value while the battery charges or discharges.

The package integrates these powers to energy (`sensor.fronius_batterie_ladeenergie` / `..._entladeenergie`). The `lifetime_energy` counters of the same modules are deliberately **not** used: they update only every ca. 5 minutes and caused false demand spikes.

Note: the import counter appears in the file several times (utility_meter, Statistics sensor, automation).

## 4. Verify before switching on

1. Developer Tools → States: the grid import counter must be a number and rise when you import. After a restart the integral sensors `sensor.fronius_batterie_ladeenergie` and `sensor.fronius_batterie_entladeenergie` start counting: the first rises while charging, the second while discharging.
2. After a restart, wait 1–2 minutes. Then `sensor.fronius_bedarf_energie` must show the **house consumption minus PV** in watts. Compare with the real value in three situations:
   - battery idle
   - battery charging
   - battery discharging

   The value must be about the same in all three. If it jumps by twice the battery power when the battery changes direction, the charge and discharge counters are swapped.
3. If your grid import counter is in kWh instead of Wh, replace `3600` by `3600000` for the import term in the demand sensor. The battery power sensors must be in W (with kW the integral would be in kWh).
4. `sensor.fronius_bezug_viertelstunde` must reset at :00, :15, :30, :45 and count the import in Wh.

## 5. Start values

| Helper | Start value |
|---|---|
| Max. Bezug pro 15 min | 500 Wh |
| Sicherheitsreserve | 50 Wh |
| Mindest-SoC für Entladen | 15 % |
| Reserve-SoC für Spitzen | 25 % |
| Netzladen startet unter SoC | 20 % |
| Netzladen endet bei SoC | 25 % |
| Prognosegewicht am Anfang | 0.6 (1 = strict) |
| Leerlaufmodus | `auto_mit_reserve` |
| Netzladen im freien Budget erlaubt | off at first |

Choose the reserve SoC from your peaks: a short peak of a few hundred Wh needs only a few percent of the battery.

## 6. Switch on

1. Restart Home Assistant (or reload YAML configuration; the new `statistics` and `utility_meter` platforms need a restart).
2. Watch `input_select.fronius_zustand` and the inverter mode with `Fronius: Bezugsbegrenzung aktiv` on.
3. Test with a low limit (e.g. 100 Wh) and a known load, and confirm that the battery discharges.
4. Test the fallback: switch the main switch off and confirm that the mode returns to `auto`.
