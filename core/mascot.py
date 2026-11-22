"""Pip: a shima enaga (Hokkaido long-tailed tit) study buddy, drawn in SVG
with the 4-blue palette. Pip's mood mirrors the diagnosed lever so the
science is visible at a glance."""
import math

from .config import BLUE, BUTTER, DEEP, ICE, PINK, SKY, WHITE

MOODS = ["happy", "cheer", "wobbly", "shrug", "dizzy", "sleepy", "hug"]
L, R, Y = 80, 120, 104  # big eyes, set wide and low = cuter


def _spiral(cx, cy, turn=1, max_r=10.5, loops=2.6):
    """Archimedean spiral drawn from the centre out (r grows with the angle)."""
    pts, steps = [], 60
    for i in range(steps + 1):
        a = i / steps * loops * 2 * math.pi
        r = max_r * i / steps
        pts.append((cx + r * math.cos(turn * a), cy + r * math.sin(turn * a)))
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return f'<path d="{d}" stroke="{DEEP}" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'


def _eyes(mood):
    sw = 'stroke-width="5" fill="none" stroke-linecap="round"'
    if mood in ("cheer", "hug"):
        return "".join(f'<path d="M{x-9} {Y+3} q9 -13 18 0" stroke="{DEEP}" {sw}/>' for x in (L, R))
    if mood == "sleepy":
        return "".join(f'<path d="M{x-9} {Y} q9 9 18 0" stroke="{DEEP}" {sw}/>' for x in (L, R))
    if mood == "dizzy":  # proper spiral eyes, like ꩜ (spinning opposite ways)
        return _spiral(L, Y, 1) + _spiral(R, Y, -1)
    if mood == "shrug":  # small blank "meh" eyes
        return "".join(f'<circle cx="{x}" cy="{Y+1}" r="6" fill="{DEEP}"/><circle cx="{x+2}" cy="{Y-1}" r="2" fill="{WHITE}"/>'
                       for x in (L, R))
    big = 10.5 if mood == "wobbly" else 10
    eyes = "".join(
        f'<circle cx="{x}" cy="{Y}" r="{big}" fill="{DEEP}"/>'
        f'<circle cx="{x+3.5}" cy="{Y-3.5}" r="3.8" fill="{WHITE}"/>'
        f'<circle cx="{x-3.5}" cy="{Y+4}" r="1.8" fill="{WHITE}"/>' for x in (L, R))
    if mood == "wobbly":  # worried brows
        eyes += (f'<path d="M{L-9} {Y-20} l12 5" stroke="{DEEP}" stroke-width="3.5" stroke-linecap="round"/>'
                 f'<path d="M{R+9} {Y-20} l-12 5" stroke="{DEEP}" stroke-width="3.5" stroke-linecap="round"/>')
    return eyes


def _beak(mood):
    cx, y = (L + R) / 2, Y + 9
    if mood in ("cheer", "wobbly", "dizzy"):  # tiny open beak
        return (f'<path d="M{cx-5} {y} L{cx+5} {y} L{cx} {y+5}Z" fill="{DEEP}" stroke="{DEEP}" stroke-width="1.5" stroke-linejoin="round"/>'
                f'<path d="M{cx-3.5} {y+7.5} L{cx+3.5} {y+7.5} L{cx} {y+11}Z" fill="{DEEP}" stroke="{DEEP}" stroke-width="1.2" stroke-linejoin="round"/>')
    return f'<path d="M{cx-5} {y} L{cx+5} {y} L{cx} {y+6}Z" fill="{DEEP}" stroke="{DEEP}" stroke-width="2" stroke-linejoin="round"/>'


def _wings(mood):
    # one little wing on each side; raised when cheering
    a = 55 if mood == "cheer" else 18
    yy = 112 if mood == "cheer" else 128
    wing = lambda cx, rot: (
        f'<g transform="rotate({rot} {cx} {yy})">'
        f'<ellipse cx="{cx}" cy="{yy}" rx="13" ry="23" fill="{SKY}" stroke="{BLUE}" stroke-width="2.5"/>'
        f'<path d="M{cx} {yy-10} q-1 12 0 22" stroke="{BLUE}" stroke-width="2" fill="none" stroke-linecap="round" opacity=".7"/></g>')
    return (f'<g class="wing wing-l" style="transform-origin:46px {yy-16}px">{wing(37, a)}</g>'
            f'<g class="wing wing-r" style="transform-origin:154px {yy-16}px">{wing(163, -a)}</g>')


def _extra(mood):
    f = 'font-family="Fredoka,Lexend,sans-serif" font-weight="600"'
    if mood == "sleepy":
        return (f'<text x="150" y="46" font-size="20" fill="{BLUE}" {f}>z</text>'
                f'<text x="166" y="30" font-size="15" fill="{BLUE}" {f}>z</text>')
    if mood == "wobbly":
        return f'<path d="M160 50 q-7 12 0 16 q7 -4 0 -16z" fill="{SKY}" stroke="{BLUE}" stroke-width="2"/>'
    if mood == "shrug":
        return f'<text x="154" y="52" font-size="28" fill="{BLUE}" {f}>?</text>'
    if mood == "dizzy":  # a little swirl, no floating dots
        return (f'<path d="M150 46 q8 -10 16 0 q8 10 16 0" stroke="{BLUE}" stroke-width="3" fill="none" stroke-linecap="round"/>'
                f'<path d="M18 46 q8 -10 16 0 q8 10 16 0" stroke="{BLUE}" stroke-width="3" fill="none" stroke-linecap="round"/>')
    if mood == "cheer":
        star = lambda x, y: (f'<path d="M{x} {y-8} L{x+2.5} {y-2.5} L{x+8} {y} L{x+2.5} {y+2.5} L{x} {y+8} '
                             f'L{x-2.5} {y+2.5} L{x-8} {y} L{x-2.5} {y-2.5}Z" fill="{BUTTER}" stroke="{BLUE}" stroke-width="1.5" stroke-linejoin="round"/>')
        return star(28, 50) + star(172, 46) + star(100, 26)
    if mood == "hug":
        return (f'<path d="M100 160 c-12 -10 -19 -17 -10 -23 c5 -3 10 0 10 4 c0 -4 5 -7 10 -4 '
                f'c9 6 2 13 -10 23z" fill="{SKY}" stroke="{BLUE}" stroke-width="2"/>')
    return ""


def svg(mood: str = "happy", size: int = 180) -> str:
    mood = mood if mood in MOODS else "happy"
    return f'''<svg class="pip" width="{size}" height="{size}" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pip the shima enaga, feeling {mood}">
  <ellipse cx="100" cy="190" rx="54" ry="6" fill="{SKY}" opacity="0.5"/>
  <g class="pip-hop">
  <path d="M136 156 Q166 158 186 180 Q178 190 166 186 Q150 178 132 170Z" fill="{SKY}" stroke="{BLUE}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M146 166 Q164 172 178 184" stroke="{BLUE}" stroke-width="2" fill="none" stroke-linecap="round" opacity=".7"/>
  <path d="M88 176 l-4 8 M88 176 l4 8 M112 176 l-4 8 M112 176 l4 8" stroke="{DEEP}" stroke-width="3" stroke-linecap="round"/>
  <ellipse cx="100" cy="114" rx="70" ry="64" fill="{WHITE}" stroke="{SKY}" stroke-width="4"/>
  <ellipse cx="100" cy="148" rx="40" ry="22" fill="{ICE}"/>
  {_wings(mood)}
  <ellipse cx="62" cy="122" rx="10" ry="6" fill="{PINK}" opacity=".9"/>
  <ellipse cx="138" cy="122" rx="10" ry="6" fill="{PINK}" opacity=".9"/>
  <g class="pip-eyes"><g class="{"blink" if mood in ("happy", "wobbly", "shrug") else ""}">{_eyes(mood)}</g></g>
  {_beak(mood)}
  {_extra(mood)}
  </g>
</svg>'''
