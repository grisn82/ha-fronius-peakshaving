# Tuning and troubleshooting

[Deutsch](../de/feinabstimmung-fehlersuche.md)

## Tuning

| Setting | Where | Effect |
|---|---|---|
| `fronius_bezug_reserve_wh` | helper | Safety margin below the limit (default 50 Wh). Covers meter/inverter timing errors |
| `fronius_anfang_gewicht` (`w0`) | helper | 1 = strict from the start. 0.6 = relaxed at the start, uses more of the budget. Lower = more budget used, higher risk for late large loads |
| `guard_anteil` | automation variable | Share of the max. battery power at which the strict rule applies immediately (default 0.6) |
| `entlade_hyst_w` | automation variable | Larger = fewer switches between discharge and idle, but the battery keeps discharging longer (default 200 W) |
| `laden_marge_w` | automation variable | Safety margin to the budget while grid charging (default 300 W) |
| `laden_min_w` | automation variable | Minimum charge power to start grid charging (default 300 W) |
| `max_age` of the Statistics sensors | Statistics sensors | 60 s = quick. 90–120 s = calmer but slower to react |
| Poll interval of ha-sunspec2 | integration | A shorter interval gives fresher values (the author uses 5 s) |

Is the budget often unused? Lower `w0` (e.g. 0.5). Does the grid import exceed the limit at the end of intervals? Raise `w0` toward 1 or increase the reserve.

## Troubleshooting

**State `fehler` / the inverter stays in `auto`**
One of these is missing or `unavailable`: the counters, `sensor.fronius_bedarf_energie`, the SoC, or `WChaMax`. Check them in Developer Tools. After a restart, wait 1–2 minutes for the Statistics sensors.

**`sensor.fronius_bedarf_energie` is unavailable or wrong**
- Battery sensors swapped (charge ↔ discharge): see [setup](setup.md), step 4.
- Demand is 0 most of the time and shows a short, large spike every few minutes: the `lifetime_energy` counters were used. Use the integrated sensors of this package (version 1.1.0 and later).
- Counters in kWh: use `3600000` instead of `3600`.
- Statistics sensors renamed: their IDs must be `sensor.fronius_stat_bezug`, `..._entladen`, `..._laden`.

**The battery flaps between discharging and idle**
Increase `entlade_hyst_w` or `max_age`. Check that the power does not oscillate because of another automation or the inverter's own control.

**`number.set_value` error ("value out of range")**
The discharge limit or the grid charge power exceeds the range of the entity. The automation limits to `WChaMax`; check that the `WChaMax` entity is correct.

**Grid charging does not start**
Is `Netzladen im freien Budget erlaubt` on? Is the SoC below `start_soc`? Is the headroom big enough (at least `laden_marge_w + laden_min_w` = 600 W of free power by default)? Are the inverter permission and the ha-sunspec2 switch on?

**"Battery rate revert time" shows 0 again**
On some setups the entity resets itself. Test the fallback: stop Home Assistant or disable the automation for a minute while in `block_discharging`, and check that the inverter returns to automatic mode.

**The limit is still exceeded**
- The load is bigger than house demand minus what the battery can deliver (`WChaMax`, SoC).
- The battery was at `min_soc` or empty.
- A very large late load with a relaxed start (see limitations in [how-it-works](how-it-works.md)).
- Your utility measures on different quarter-hour boundaries or with another method.

## Simulation

`simulation/sim_budget.py` simulates one quarter-hour in an idealised model (no measurement lag, instant battery) and compares `w0` values:

```
python3 simulation/sim_budget.py
```

It helps to understand the effect of `w0`, not to predict your system.
