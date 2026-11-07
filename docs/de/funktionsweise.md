# Funktionsweise

[English](../en/how-it-works.md)

Die Automation `Fronius: Netzbezug pro 15 min begrenzen` läuft alle 10 Sekunden, solange `input_boolean.fronius_peakshaving` an ist. Jeder Durchlauf berechnet den Zustand neu und **schreibt Batteriemodus und Leistung erneut**. Das Neuschreiben in jedem Zyklus hält die „Battery rate revert time“ des Wechselrichters am Laufen.

## Eingangsgrößen

| Größe | Quelle |
|---|---|
| Bisheriger Bezug dieser Viertelstunde `used_wh` | `utility_meter` auf dem Bezugszähler (Reset bei :00/:15/:30/:45) |
| Bedarf `p_free` (W) | Template-Sensor `sensor.fronius_bedarf_energie` |
| SoC | Sensor für den Ladezustand der Batterie |
| `WChaMax` | Entität für die max. Batterieleistung |

### Bedarf aus Energiezählern

Drei Statistik-Sensoren berechnen `change_second` (Wh pro Sekunde) der Zähler für Netzbezug, Batterie entladen und Batterie geladen über ein 60-s-Fenster. Der Template-Sensor kombiniert sie:

```
p_free = (Δbezug + Δentladen − Δgeladen) / Δt · 3600     [W]
```

Das ist der Hausverbrauch minus PV-Erzeugung, also was das Netz **ohne** Batterie liefern müsste. Da der Wert aus Zählern stammt, ist alles enthalten, was zwischen zwei Abfragen passiert ist.

## Erlaubte Leistung

Mit `T_rem` als Restsekunden der Viertelstunde (für die Rechnung mindestens 60 s):

```
p_strict = max( (limit − reserve − used) · 3600 / T_rem , 0 )
```

`p_strict` ist die konstante Leistung, die das restliche Budget genau am Ende des Intervalls aufbraucht.

### Lockerer Start

Anzunehmen, dass der aktuelle Bedarf die ganze restliche Viertelstunde anhält, ist am Anfang pessimistisch. Ein Gewicht steigt linear von `w0` auf 1:

```
x       = vergangen / 900
w       = w0 + (1 − w0) · x
p_relax = p_strict / max(w, 0.2)
```

Mit `w0 = 0.6` ist die erlaubte Leistung am Anfang etwa das 1,67-fache von `p_strict`. Am Ende entspricht sie `p_strict`.

**Guard:** Wenn `p_free − p_strict ≥ guard_anteil · WChaMax` (Standard 0,6), könnte die Batterie nur knapp aufholen. Dann gilt sofort der strenge Wert:

```
p_allow = p_relax   wenn (p_free − p_strict) < guard_anteil · WChaMax
        = p_strict  sonst
p_dis   = p_free − p_allow         # nötige Entladeleistung
headroom = p_strict − p_free       # freies Budget (für Netzladen, immer streng)
```

## Entscheidungsreihenfolge

Die erste zutreffende Regel gewinnt:

| # | Bedingung | Zustand | Modus am Wechselrichter |
|---|---|---|---|
| 1 | ein benötigter Wert fehlt / ist nicht verfügbar | `fehler` | `auto` |
| 2 | SoC > Mindest-SoC und `p_dis` über der Schwelle | `entladen` | `discharge_limit` (Watt) |
| 3 | Netzladen erlaubt, Ladephase aktiv und genug Spielraum | `laden` | `charge_from_grid` (Watt) |
| 4 | Leerlauf, Modus `sperren` (oder Reserve erreicht) | `sperren` | `block_discharging` |
| 5 | sonst Leerlauf | `auto` | `auto` |

Ein Entladelimit unter 10 W wird als `block_discharging` gesendet (ein 0-W-Limit wird nie geschrieben).

### Hysterese (in Watt)

- **Entladen** startet bei `p_dis > 50 W` und endet bei `p_dis < −200 W` (`entlade_hyst_w`).
- **Netzladen** startet bei `headroom − 300 W > 300 W` (`laden_marge_w`, `laden_min_w`) und läuft weiter, solange der Wert über 100 W bleibt.
- **Ladephase** (`input_boolean.fronius_ladephase`, nur von der Automation gesetzt): startet unter `start_soc`, endet bei `ziel_soc`.
- **Reserve** (`auto_mit_reserve`): Bei `SoC ≤ reserve_soc` wird die Batterie gesperrt, bei `reserve_soc + 3` wieder freigegeben.

### Leerlaufmodi

| Modus | Verhalten ohne Spitze und ohne Netzladen |
|---|---|
| `sperren` | `block_discharging`. Die Batterie wird nur für Spitzen genutzt. Keine Eigenverbrauchsoptimierung |
| `auto` | normale Eigenverbrauchsoptimierung. Die Batterie kann bei einer Spitze leer sein |
| `auto_mit_reserve` | `auto`, solange der SoC über `reserve_soc` liegt; darunter wird gesperrt, um die Reserve für Spitzen zu halten |

`min_soc`, `start_soc` und `ziel_soc` gelten für das Entladen bei Spitzen und das Netzladen. Das Leerlaufverhalten in `auto_mit_reserve` ändern sie nicht, dort zählt nur `reserve_soc`.

## Statusanzeige

`input_select.fronius_zustand`: `auto`, `sperren`, `entladen`, `laden`, `fehler`, `aus`. Wird nur von der Automation geschrieben. `aus` heißt: Hauptschalter aus (die zweite Automation setzt den Wechselrichter dann zurück auf `auto`).

## Grenzen

- Die Zähler sind DC-seitige Modulzähler und nicht perfekt synchron mit dem Netzzähler. Kleine Abweichungen deckt die Sicherheitsreserve ab.
- Nach einem Neustart von Home Assistant brauchen die Statistik-Sensoren 1–2 Minuten, bis sie gefüllt sind. Bis dahin kann der Zustand `fehler` (= `auto`) sein.
- Ein lockerer Start kann das Limit überschreiten, wenn spät in der Viertelstunde eine sehr große Last auftritt. In der Simulation endet ein später 7-kW-Sprung bei etwa 510 Wh statt 462 Wh mit der strengen Regel. Wenn dir das wichtig ist, `fronius_anfang_gewicht` Richtung 1 erhöhen.
- Die Viertelstundengrenzen folgen der Home-Assistant-Uhr. Die Zeit synchron halten (NTP). Prüfen, ob dein Netzbetreiber auf denselben Grenzen misst.
- Das Package kann nicht mehr entladen, als Batterie und Wechselrichter erlauben. Bei sehr großer Last wird das Limit überschritten.
