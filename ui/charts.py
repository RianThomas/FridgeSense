"""The nutrient ring: one SVG per nutrient, plus the words that carry the same
information (so it never depends on colour alone)."""
import math

from ui.common import esc

RADIUS = 52
CIRCUMFERENCE = 2 * math.pi * RADIUS


def ring(name, value, total, unit, kind="limit"):
    """kind: "goal" (more is better, e.g. protein) or "limit" (stay under)."""
    pct = (value / total) if total else 0.0
    shown = round(pct * 100)
    dash = min(pct, 1.0) * CIRCUMFERENCE
    classes, flag = "fs-ring", ""
    if kind == "goal" and pct >= 1.0:
        classes += " met"
        flag = "Goal met"
    elif kind == "limit" and pct > 1.0:
        classes += " over"
        flag = "Over limit"
    bar = ""
    if dash >= 0.5:
        bar = (f'<circle class="bar" cx="66" cy="66" r="{RADIUS}" fill="none" stroke-width="13" '
               f'stroke-linecap="round" stroke-dasharray="{dash:.1f} {CIRCUMFERENCE:.1f}" '
               f'transform="rotate(-90 66 66)"/>')
    label = f"{name}: {value:,.0f} of {total:,.0f} {unit}, {shown} percent"
    return (
        f'<div class="{classes}">'
        f'<svg viewBox="0 0 132 132" role="img" aria-label="{esc(label)}">'
        f'<circle class="track" cx="66" cy="66" r="{RADIUS}" fill="none" stroke-width="13"/>'
        f'{bar}<text class="pct" x="66" y="75" text-anchor="middle">{shown}%</text></svg>'
        f'<div class="fs-ring-name">{esc(name)}</div>'
        f'<div class="fs-ring-val">{value:,.0f} / {total:,.0f} {esc(unit)}</div>'
        f'<div class="fs-ring-flag">{flag}&nbsp;</div>'
        f'</div>'
    )


def ring_grid(rings):
    return '<div class="fs-rings">' + "".join(rings) + "</div>"
