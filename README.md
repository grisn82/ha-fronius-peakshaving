# ha-fronius-peakshaving

🇬🇧 English · [🇩🇪 Deutsch](README.de.md)

A Home Assistant package that limits the **grid import per quarter-hour** (e.g. to 500 Wh) with a **Fronius Gen24 inverter and battery**. When the house would import more than the budget allows, the battery discharges just enough. When there is room in the budget, it can optionally charge from the grid.

It controls the battery through the entities of the [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) integration (Modbus).

## Why energy-based?

Peak-based tariffs and import limits are defined in **energy per interval** (Wh per 15 min), not in power. This package therefore works with energy counters:

- Grid import so far in the current quarter-hour comes from a `utility_meter` on the import counter. Even a spike of a few seconds is counted exactly.
- The current demand is the mean over the last ~60 s, calculated from the integrated grid import and battery charge/discharge power (energy). No instantaneous power samples, so slow or jumpy power readings do not matter.
- Hysteresis in watts instead of dwell times: the battery reacts immediately, but does not flap between charging and discharging.
- Relaxed at the start, strict at the end of each quarter-hour, so the budget is actually used.

## Features

- Max. grid import per 15 min, configurable at runtime (helper `Max. Bezug pro 15 min`)
- Battery discharges only as much as needed (discharge limit in watts)
- Optional grid charging inside the free budget, with start/target SoC hysteresis
- Four idle modes: `sperren` (block discharge), `auto` (normal self-consumption), `auto_mit_reserve` (self-consumption, but keeps a reserve SoC for peaks), `auto_nach_budget` (like `auto_mit_reserve`, but the reserve zone only discharges once the 15-min budget is used up)
- Fail-safe: any missing sensor value switches the inverter back to `auto`
- Status helper `input_select.fronius_zustand` shows what the regulator is doing

> The helper names and the `name:` strings in the YAML are in German, because the package was written for a German-language installation. The entity IDs derive from the keys/names and are used throughout the documentation. Display names of the helpers can be changed freely; do **not** rename the Statistics and template sensors.

## Requirements

- Fronius Gen24 (tested: Symo GEN24 8.0) with battery and a smart meter at the grid connection
- [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) (not the read-only `ha-sunspec` by CJNE) with the battery control entities
- Modbus TCP enabled on the inverter, control allowed. The inverter accepts only **one** Modbus connection
- Home Assistant **2024.10 or newer** (uses the `triggers:` / `trigger:` syntax)

## Quick start

1. Enable packages in `configuration.yaml`:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. Copy [`packages/fronius_peakshaving.yaml`](packages/fronius_peakshaving.yaml) to `<config>/packages/`.
3. **Replace the 9 entity IDs** listed at the top of the file with the ones of your system (search & replace).
4. Verify the counters and the demand sensor (see [setup](docs/en/setup.md)), restart Home Assistant.
5. Set the helpers (start values in the setup guide), switch `Fronius: Bezugsbegrenzung aktiv` on.

## Documentation

| | English | Deutsch |
|---|---|---|
| How it works (formulas, states) | [how-it-works](docs/en/how-it-works.md) | [funktionsweise](docs/de/funktionsweise.md) |
| Setup and verification | [setup](docs/en/setup.md) | [einrichtung](docs/de/einrichtung.md) |
| Tuning and troubleshooting | [tuning-troubleshooting](docs/en/tuning-troubleshooting.md) | [feinabstimmung-fehlersuche](docs/de/feinabstimmung-fehlersuche.md) |

A dashboard for control and testing is in [`dashboard/`](dashboard/fronius_peakshaving_dashboard.yaml).

A small simulation of the quarter-hour logic is in [`simulation/sim_budget.py`](simulation/sim_budget.py).

## 🤖 Authorship

The code and the documentation in this repository were written by an AI assistant (Claude, by Anthropic). The maintainer did not write the code, but tested it on his own system and gave the feedback that shaped the design. Review the code before you use it.

## ⚠️ Disclaimer

This was developed and tested on **one system** (Symo GEN24 8.0 with ha-sunspec2). It writes to the battery control of your inverter. Test with care: first with the main switch off and the entities watched, then with a low limit. Check that the "Battery rate revert time" fallback works on your system. Use at your own risk, see the [MIT license](LICENSE). This is an independent project, not affiliated with Fronius.

## Credits

- [`ha-sunspec2`](https://github.com/hilman2/ha-sunspec2) by hilman2 for the Modbus/SunSpec integration
- Home Assistant `utility_meter` and `statistics` integrations

## License

[MIT](LICENSE)
