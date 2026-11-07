#!/usr/bin/env python3
"""Idealised simulation of the quarter-hour budget regulation.

Purpose: show how the forecast weight w0 (helper `fronius_anfang_gewicht`) changes the
grid import and the battery usage over one 15-minute interval, and where the
relaxed start can hurt (late, very large loads).

Simplifications (this is a design aid, NOT a model of your system):
  - the demand is known exactly, no measurement lag
  - the battery follows the limit instantly and has unlimited energy
  - idle mode is "sperren" (battery blocked unless the limit requires discharging)
  - no hysteresis, no SoC logic, no grid charging

The formulas are the same as in packages/fronius_peakshaving.yaml.

Usage:  python3 sim_budget.py
"""

LIMIT, RESERVE = 500.0, 50.0   # Wh per quarter-hour, safety reserve in Wh
PMAX = 5000.0                  # max battery power in W (stand-in for WChaMax)
GUARD = 0.6                    # guard_anteil


def run(demand, w0, dt=10):
    """Return (grid import in Wh, battery energy in Wh) for one quarter-hour."""
    used = bat = 0.0
    for k in range(900 // dt):
        t = k * dt
        t_rem = 900 - t
        t_calc = max(t_rem, 60)
        remaining = LIMIT - RESERVE - used
        p_strict = max(remaining * 3600 / t_calc, 0)
        w = w0 + (1 - w0) * (t / 900)
        p_relax = p_strict / max(w, 0.2)
        d = demand(t)
        # strict rule applies as soon as the battery would only barely catch up
        p_allow = p_relax if (d - p_strict) < GUARD * PMAX else p_strict
        p_dis = d - p_allow
        limit_w = min(max(p_dis + 50, 0), PMAX) if p_dis > 50 else 0
        battery = min(limit_w, d, PMAX)
        used += (d - battery) * dt / 3600
        bat += battery * dt / 3600
    return used, bat


SCENARIOS = {
    "A  4 kW constant":                   lambda t: 4000,
    "B  4 kW for 3 min, then 0.5 kW":     lambda t: 4000 if t < 180 else 500,
    "C  4 kW for 5 min, then 1.5 kW":     lambda t: 4000 if t < 300 else 1500,
    "D  1.5 kW constant (below limit)":   lambda t: 1500,
    "E  0.5 kW, from minute 10 5 kW":     lambda t: 500 if t < 600 else 5000,
    "F  8 kW constant (battery too small)": lambda t: 8000,
}
RISK = {
    "G  4 kW until minute 10, then 7 kW": lambda t: 4000 if t < 600 else 7000,
    "H  3 kW until minute 12, then 6 kW": lambda t: 3000 if t < 720 else 6000,
    "I  2 kW until minute 13, then 5 kW": lambda t: 2000 if t < 780 else 5000,
}


def table(title, scenarios, weights):
    print(title)
    print(f"{'scenario':38s}" + "".join(f"  w0={w:<4}  import/battery Wh" for w in weights))
    for name, f in scenarios.items():
        row = f"{name:38s}"
        for w in weights:
            used, bat = run(f, w)
            flag = "!" if used > LIMIT else " "
            row += f"  {used:7.0f}{flag}/{bat:5.0f}          "
        print(row)
    print()


if __name__ == "__main__":
    table("Normal cases:", SCENARIOS, [1.0, 0.7, 0.6, 0.4])
    table("Risk cases (late, large load):", RISK, [1.0, 0.6, 0.4])
    print(f"(! = import above the limit of {LIMIT:.0f} Wh)")
