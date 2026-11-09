# Changelog

## 1.1.0 - 2026-11-08

- Fix: the battery energy is no longer taken from the inverter's `lifetime_energy` counters (they update only every ca. 5 minutes and caused false demand spikes and unnecessary discharging). Instead the DC power sensors of the battery channels are integrated to Wh (Integration sensors, `max_sub_interval` 10 s).
- Changed entity IDs to adjust: battery charge/discharge **power** (`..._dc_power`) instead of the energy counters. Existing installations must change these two IDs.
- New sensors: `sensor.fronius_batterie_ladeenergie`, `sensor.fronius_batterie_entladeenergie`.

## 1.0.0 - 2026-11-07

First public release.

- Energy-based regulation of the grid import per quarter-hour (utility_meter on the import counter).
- Demand estimate from energy counters (Statistics sensors with `change_second`, 60 s window).
- Battery control through the `ha-sunspec2` battery entities (mode, discharge limit, grid charge power).
- Hysteresis in watts instead of dwell times; grid charging with start/target SoC hysteresis and safety margin.
- Idle modes `sperren`, `auto`, `auto_mit_reserve`.
- Relaxed start of each quarter-hour (forecast weight `w0`) with a safeguard for large loads.
- Fail-safe to automatic mode when a value is missing; status helper `input_select.fronius_zustand`.
