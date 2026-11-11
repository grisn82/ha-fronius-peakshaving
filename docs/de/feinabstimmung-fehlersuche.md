# Feinabstimmung und Fehlersuche

[English](../en/tuning-troubleshooting.md)

## Feinabstimmung

| Einstellung | Wo | Wirkung |
|---|---|---|
| `fronius_bezug_reserve_wh` | Helfer | Sicherheitsabstand unter dem Limit (Standard 50 Wh). Deckt Zeitfehler zwischen Zähler und Wechselrichter ab |
| `fronius_anfang_gewicht` (`w0`) | Helfer | 1 = von Anfang an streng. 0,6 = locker am Anfang, nutzt mehr vom Budget. Niedriger = mehr Budget genutzt, höheres Risiko bei späten großen Lasten |
| `guard_anteil` | Variable in der Automation | Anteil der max. Batterieleistung, ab dem sofort die strenge Regel gilt (Standard 0,6) |
| `entlade_hyst_w` | Variable in der Automation | Größer = weniger Wechsel zwischen Entladen und Leerlauf, aber die Batterie entlädt länger weiter (Standard 200 W) |
| `laden_marge_w` | Variable in der Automation | Sicherheitsabstand zum Budget beim Netzladen (Standard 300 W) |
| `laden_min_w` | Variable in der Automation | Mindest-Ladeleistung, um das Netzladen zu starten (Standard 300 W) |
| `max_age` der Statistik-Sensoren | Statistik-Sensoren | 60 s = schnell. 90–120 s = ruhiger, aber träger |
| Abfrageintervall von ha-sunspec2 | Integration | Kürzeres Intervall = aktuellere Werte (der Autor nutzt 5 s) |

Wird das Budget oft nicht ausgenutzt? `w0` senken (z. B. 0,5). Überschreitet der Bezug am Ende von Intervallen das Limit? `w0` Richtung 1 erhöhen oder die Reserve vergrößern.

## Fehlersuche

**Zustand `fehler` / Wechselrichter bleibt auf `auto`**
Einer dieser Werte fehlt oder ist `unavailable`: die Zähler, `sensor.fronius_bedarf_energie`, der SoC oder `WChaMax`. In den Entwicklerwerkzeugen prüfen. Nach einem Neustart 1–2 Minuten auf die Statistik-Sensoren warten.

**`sensor.fronius_bedarf_energie` ist nicht verfügbar oder falsch**
- Batteriesensoren vertauscht (Laden ↔ Entladen): siehe [Einrichtung](einrichtung.md), Schritt 4.
- Bedarf ist meist 0 und zeigt alle paar Minuten kurz eine große Spitze: Es wurden die `lifetime_energy`-Zähler verwendet. Die integrierten Sensoren dieses Packages nutzen (Version 1.1.0 und neuer).
- Leistungssensoren in kW statt W: Der Bedarf ist 1000-mal zu klein. W-Sensoren verwenden.
- Statistik-Sensoren umbenannt: Ihre IDs müssen `sensor.fronius_stat_bezug`, `..._entladen`, `..._laden` lauten.

**Die Batterie wechselt ständig zwischen Entladen und Leerlauf**
`entlade_hyst_w` oder `max_age` erhöhen. Prüfen, dass die Leistung nicht wegen einer anderen Automation oder der Eigenregelung des Wechselrichters pendelt.

**Fehler bei `number.set_value` („value out of range“)**
Entladelimit oder Netzladeleistung liegt außerhalb des Bereichs der Entität. Die Automation begrenzt auf `WChaMax`; prüfen, ob die `WChaMax`-Entität stimmt.

**Netzladen startet nicht**
Ist `Netzladen im freien Budget erlaubt` an? Liegt der SoC unter `start_soc`? Ist der Spielraum groß genug (standardmäßig mindestens `laden_marge_w + laden_min_w` = 600 W freie Leistung)? Sind die Freigabe im Wechselrichter und der ha-sunspec2-Schalter an?

**„Battery rate revert time“ zeigt wieder 0**
Bei manchen Setups setzt sich die Entität selbst zurück. Den Rückfall testen: Home Assistant stoppen oder die Automation eine Minute deaktivieren, während `block_discharging` aktiv ist, und prüfen, ob der Wechselrichter in den Automatikmodus zurückkehrt.

**Das Limit wird trotzdem überschritten**
- Die Last ist größer als Hausbedarf minus das, was die Batterie liefern kann (`WChaMax`, SoC).
- Die Batterie war auf `min_soc` oder leer.
- Sehr große späte Last bei lockerem Start (siehe Grenzen in [Funktionsweise](funktionsweise.md)).
- Dein Netzbetreiber misst auf anderen Viertelstundengrenzen oder mit einer anderen Methode.

## Warum der Netzbezug aus der Leistung integriert wird

Der Bezugszähler des Smart Meters wächst in Stufen (mindestens 1 Wh) und wird alle 5–20 s gemeldet. Ein `change_second` über 60 s direkt auf diesem Zähler springt um etwa 60 W pro Wh-Stufe (bei kürzerem Fenster mehr), so dass `sensor.fronius_bedarf_energie` verrauscht wirkt. Das Package integriert deshalb die **Leistung** des Smart Meters (ganze Watt, keine Stufen) zu `sensor.fronius_netzbezug_energie`, wie die Batterieenergie. Das Integral folgt dem Leistungssensor, der dem Zähler etwas hinterherhinken kann. Das Viertelstundenbudget nutzt den exakten Zähler. Ist `sensor.fronius_bedarf_energie` trotzdem zu unruhig, bei den Statistik-Sensoren ein größeres `max_age` (90–120 s) verwenden.

## Simulation

`simulation/sim_budget.py` simuliert eine Viertelstunde in einem idealisierten Modell (keine Messverzögerung, sofort reagierende Batterie) und vergleicht `w0`-Werte:

```
python3 simulation/sim_budget.py
```

Sie hilft, die Wirkung von `w0` zu verstehen, nicht, deine Anlage vorherzusagen.
