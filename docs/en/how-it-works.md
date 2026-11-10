# How it works

[Deutsch](../de/funktionsweise.md)

The automation `Fronius: Netzbezug pro 15 min begrenzen` runs every 10 seconds while `input_boolean.fronius_peakshaving` is on. Each run recomputes the state and **rewrites the battery mode and power**. Rewriting every cycle keeps the inverter's "Battery rate revert time" from expiring.

## Inputs

| Quantity | Source |
|---|---|
| Imported so far in this quarter-hour `used_wh` | `utility_meter` on the grid import counter (resets at :00/:15/:30/:45) |
| Demand `p_free` (W) | template sensor `sensor.fronius_bedarf_energie` |
| SoC | battery state-of-charge sensor |
| `WChaMax` | max. battery power entity |

### Demand from energy counters

The battery power sensors are integrated to energy (Integration sensors, refreshed every 10 s). Three Statistics sensors then compute `change_second` (Wh per second) of the grid import counter and of the two integrated battery energies over a 60 s window. (The inverter's own `lifetime_energy` counters are not used: they update only every ca. 5 minutes.) The template sensor combines them:

```
p_free = (Δimport + Δdischarged − Δcharged) / Δt · 3600     [W]
```

This is the house consumption minus PV production, i.e. what the grid would have to supply **without** the battery. Because it comes from counters, everything that happened between two polls is included.

## Allowed power

With `T_rem` the remaining seconds of the quarter-hour (at least 60 s for the calculation):

```
p_strict = max( (limit − reserve − used) · 3600 / T_rem , 0 )
```

`p_strict` is the constant power that would use up the remaining budget exactly at the end of the interval.

### Relaxed start

Assuming the current demand lasts the whole rest of the interval is pessimistic at the start. A weight rises linearly from `w0` to 1:

```
x       = elapsed / 900
w       = w0 + (1 − w0) · x
p_relax = p_strict / max(w, 0.2)
```

With `w0 = 0.6`, the allowed power at the start is about 1.67 × `p_strict`. At the end it equals `p_strict`.

**Guard:** if `p_free − p_strict ≥ guard_anteil · WChaMax` (default 0.6), the battery would only barely be able to catch up, so the strict value is used immediately:

```
p_allow = p_relax   if (p_free − p_strict) < guard_anteil · WChaMax
        = p_strict  otherwise
p_dis   = p_free − p_allow         # required discharge power
headroom = p_strict − p_free       # free budget (used for grid charging, always strict)
```

## Decision order

The first matching rule wins:

| # | Condition | State | Inverter mode |
|---|---|---|---|
| 1 | a required value is missing/unavailable | `fehler` | `auto` |
| 2 | SoC > min SoC and `p_dis` above threshold | `entladen` | `discharge_limit` (watts) |
| 3 | grid charging allowed, charge phase active, and enough headroom | `laden` | `charge_from_grid` (watts) |
| 4 | idle, mode `sperren` (or reserve reached) | `sperren` | `block_discharging` |
| 5 | idle otherwise | `auto` | `auto` |

A discharge limit below 10 W is sent as `block_discharging` (a 0 W limit is never written).

### Hysteresis (in watts)

- **Discharging** starts when `p_dis > 50 W` and ends when `p_dis < −200 W` (`entlade_hyst_w`).
- **Grid charging** starts when `headroom − 300 W > 300 W` (`laden_marge_w`, `laden_min_w`) and continues while it stays above 100 W.
- **Charge phase** (`input_boolean.fronius_ladephase`, set by the automation only): starts below `start_soc`, ends at `ziel_soc`.
- **Reserve** (`auto_mit_reserve`): the battery is blocked at `SoC ≤ reserve_soc` and released again at `reserve_soc + 3`.

### Idle modes

| Mode | Behaviour when there is no peak and no grid charging |
|---|---|
| `sperren` | `block_discharging`. The battery is only used for peaks. No self-consumption optimisation |
| `auto` | normal self-consumption. The battery may be empty when a peak arrives |
| `auto_mit_reserve` | `auto` while SoC is above `reserve_soc`; below it the battery is blocked to keep the reserve for peaks |
| `auto_nach_budget` | `block_discharging` until the budget of the quarter-hour (`limit − reserve`) is used up, then `auto` until the next quarter-hour (see below) |

### Mode `auto_nach_budget`

The battery stays blocked while the grid import of the quarter-hour is still below the budget `limit − reserve`, so the house may use the free budget from the grid. Once the budget is used up, the regulation switches to `auto` and the inverter regulates the grid import to about 0 by itself. At the start of the next quarter-hour the budget is empty again and the battery is blocked again. The result: the battery only supplies the part of the consumption that exceeds the budget, and no energy is discharged unnecessarily early.

Details:
- The discharge limit in watts is **not** used in this mode (the discharge branch is skipped); `p_allow`/`w0` have no effect, except for grid charging.
- `auto` is only used while SoC > `min_soc`; otherwise the battery stays blocked. `reserve_soc` is not used.
- Grid charging (if allowed) works as usual inside the free budget and stops when the budget is used up.
- Trade-off: while the budget is not yet used up, the battery does not intervene. A large load can raise the import quickly, and after the switch to `auto` the inverter needs a few seconds to react (polling, the 10 s cycle and the inverter ramp together are ca. 15–30 s). At 6 kW that is 25–50 Wh above the budget. Use a larger safety reserve in this mode (e.g. 80–100 Wh) and test it.
- The inverter's own regulation to 0 is not as exact as the watt-based discharge limit; small residual imports are possible.

`min_soc`, `start_soc` and `ziel_soc` apply to peak discharging and grid charging. They do not change the idle behaviour in `auto_mit_reserve`, which only uses `reserve_soc`.

## Status helper

`input_select.fronius_zustand`: `auto`, `sperren`, `entladen`, `laden`, `fehler`, `aus`. Written by the automation only. `aus` means the main switch is off (the second automation sets the inverter back to `auto`).

## Limitations

- The battery energy is an integral of DC-side power values and the grid import comes from the meter counter; they are not perfectly in sync. Small errors are covered by the safety reserve.
- After a Home Assistant restart the Statistics sensors need 1–2 minutes to fill. Until then the state may be `fehler` (= `auto`).
- A relaxed start can exceed the limit if a very large load appears late in the interval. In the simulation, a late 7 kW step ends at about 510 Wh instead of 462 Wh with the strict rule. Raise `fronius_anfang_gewicht` toward 1 if that matters to you.
- Quarter-hour boundaries follow the Home Assistant clock. Keep the time synchronised (NTP). Check whether your utility measures on the same boundaries.
- The package cannot discharge more than the battery and inverter allow. With a very large load the limit will be exceeded.
