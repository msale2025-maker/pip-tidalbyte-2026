"""Shared HTML/CSS helpers (palette locked to 4 blues + butter + white, light and dark).

Readability choices (British Dyslexia Association style guide + WCAG):
- Lexend body font (designed for reading fluency), Fredoka rounded headings
- 17px+ text, 1.6 line height, extra letter/word spacing, left-aligned
- no italics, no underlines, no ALL CAPS, tinted (not stark white) page
- soft slate-blue text with AAA contrast; motion is slow and can be turned off
"""
import base64
import json
import random
from urllib.parse import quote
from html import escape
from pathlib import Path

from .config import BLUE, BUTTER, DARK, LIGHT, PINK, SKY, WHITE

_WAVE = "M0 60 C150 100 350 20 600 60 C850 100 1050 20 1200 60 C1350 100 1550 20 1800 60 C2050 100 2250 20 2400 60 V140 H0Z"
_FX_JS = (Path(__file__).parent / "fx.js").read_text()


def waves_html(dark: bool = False, big: bool = False) -> str:
    """Gentle waves along the bottom: 5 layers that drift sideways AND swell up and down."""
    p = DARK if dark else LIGHT
    layer = lambda cls, color, op: (
        f'<div class="wl {cls}"><svg class="wave" viewBox="0 0 2400 140" preserveAspectRatio="none" aria-hidden="true">'
        f'<path d="{_WAVE}" fill="{color}" opacity="{op}"/></svg></div>')
    a, b = (0.22, 0.10) if dark else (0.35, 0.10)
    return (f'<div class="waves{" big" if big else ""}" aria-hidden="true">'
            + layer("w5", p["wave_b"], b * 0.6) + layer("w1", p["wave_a"], a) + layer("w4", p["wave_a"], a * 0.55)
            + layer("w2", p["wave_b"], b) + layer("w3", p["wave_a"], a * 0.7) + "</div>")


def fx_html(sound=True, volume=60, haptics=True, still=False, dark=False, ambient="Off", amb_volume=40) -> str:
    """Script for sounds, haptics, sparkles, Pip's interactions, focus sounds and Enter-to-send."""
    settings = dict(sound=bool(sound), volume=int(volume), haptics=bool(haptics), still=bool(still),
                    ambient=ambient or "Off", amb_volume=int(amb_volume),
                    colors=[BUTTER, SKY, WHITE] if not dark else [BUTTER, SKY, "#8DB2F2"])
    return "<script>" + _FX_JS.replace("__SETTINGS__", json.dumps(settings)) + "</script>"


_CLOUD = ('<svg viewBox="0 0 120 60" width="100%" height="100%"><path d="M28 52 C10 52 6 34 20 30 C18 14 40 8 50 20 '
          'C58 4 86 6 88 26 C104 24 114 38 104 48 C100 52 96 52 92 52 Z"/></svg>')
_STAR = ('<svg viewBox="0 0 20 20" width="100%" height="100%"><path d="M10 1.5 L12.3 7.7 L18.5 10 L12.3 12.3 '
         'L10 18.5 L7.7 12.3 L1.5 10 L7.7 7.7Z"/></svg>')
AMBIENT_SOUNDS = ["Off", "White noise", "Rain", "Birdsong", "Ocean", "Music box"]


def ambient_html(kind: str) -> str:
    """Background animation that goes with each focus sound (behind content).
    Positions are seeded so reruns produce identical markup (no flicker)."""
    rnd = random.Random(7)
    items = []
    if kind == "White noise":  # slow drifting clouds
        for i in range(6):
            w = rnd.randint(110, 230)
            items.append(f'<i class="cloud" style="top:{rnd.randint(2, 55)}%;width:{w}px;height:{w // 2}px;'
                         f'animation-duration:{rnd.randint(70, 140)}s;animation-delay:-{rnd.randint(0, 140)}s;'
                         f'opacity:{rnd.uniform(.45, .85):.2f}">{_CLOUD}</i>')
    elif kind == "Rain":
        for i in range(95):
            items.append(f'<i class="drop" style="left:{rnd.uniform(0, 104):.1f}%;height:{rnd.randint(14, 28)}px;'
                         f'animation-duration:{rnd.uniform(.7, 1.4):.2f}s;animation-delay:-{rnd.uniform(0, 2):.2f}s;'
                         f'opacity:{rnd.uniform(.25, .6):.2f}"></i>')
    elif kind in ("Birdsong",):  # music notes floating up softly
        for i in range(16):
            items.append(f'<i class="note{" alt" if i % 3 == 0 else ""}" style="left:{rnd.uniform(2, 96):.1f}%;'
                         f'font-size:{rnd.randint(18, 34)}px;animation-duration:{rnd.uniform(9, 16):.1f}s;'
                         f'animation-delay:-{rnd.uniform(0, 16):.1f}s">{rnd.choice("♪♫♩♬")}</i>')
    elif kind == "Ocean":  # rising bubbles (waves also get bigger)
        for i in range(26):
            sz = rnd.randint(6, 18)
            items.append(f'<i class="bubble-o" style="left:{rnd.uniform(0, 100):.1f}%;width:{sz}px;height:{sz}px;'
                         f'animation-duration:{rnd.uniform(7, 14):.1f}s;animation-delay:-{rnd.uniform(0, 14):.1f}s"></i>')
    elif kind == "Music box":  # twinkling stars
        for i in range(22):
            sz = rnd.randint(12, 26)
            items.append(f'<i class="twinkle{" alt" if i % 2 else ""}" style="left:{rnd.uniform(1, 98):.1f}%;'
                         f'top:{rnd.uniform(2, 85):.1f}%;width:{sz}px;height:{sz}px;'
                         f'animation-duration:{rnd.uniform(2.5, 5):.1f}s;animation-delay:-{rnd.uniform(0, 5):.1f}s">{_STAR}</i>')
    if not items:
        return ""
    return f'<div class="amb" aria-hidden="true">{"".join(items)}</div>'


def thinking_html(seconds: int) -> str:
    """Pip's speech bubble while Nemotron works, with a live stopwatch."""
    watch = ('<svg class="watch" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">'
             '<circle cx="12" cy="13.5" r="8.5" fill="none" stroke="currentColor" stroke-width="2"/>'
             '<path d="M9.5 2.5h5M12 2.5v2.5M18.5 6.5l1.5-1.5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>'
             '<path class="hand" d="M12 13.5V8.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>')
    return (f'<div class="bubble thinking"><span class="pipping">Pipping<span class="dots"><b>.</b><b>.</b><b>.</b></span></span> '
            f'<span class="muted">(thinking...)</span><span class="stopwatch">{watch}<span>{seconds}s</span></span></div>')


def title_html(name: str) -> str:
    word = "".join(f'<span class="wig" style="--i:{i}">{c}</span>' for i, c in enumerate("unstuck"))
    return f'<h1>Hey {escape(name)}, let\'s get <span class="hl">{word}</span></h1>'


def css(easy_read: bool = False, still: bool = False, dark: bool = False) -> str:
    p = DARK if dark else LIGHT
    T, A, L, BG, S, BTN, BT, BAR, BU, OBU, SH = (p[k] for k in (
        "text", "accent", "line", "bg", "surface", "btn", "btn_text", "bar", "butter", "on_butter", "shadow"))
    base = 19 if easy_read else 17
    letter = ".06em" if easy_read else ".02em"
    word = ".16em" if easy_read else ".06em"
    line = 1.85 if easy_read else 1.6
    motion_off = "*, .wave, .pip { animation: none !important; transition: none !important; }" if still else ""
    tail = quote(f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 34'>"
                 f"<path d='M40 2 C30 9 17 21 2 32 C19 32 32 29 40 25 Z' fill='{S}'/>"
                 f"<path d='M40 2 C30 9 17 21 2 32 C19 32 32 29 40 25' fill='none' stroke='{A}' stroke-width='2.2' "
                 f"stroke-linecap='round' stroke-linejoin='round'/></svg>")
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600&family=Lexend:wght@400;500;600&display=swap');
:root {{ color-scheme: {"dark" if dark else "light"}; }}
html, body, .stApp, .stMarkdown, p, li, label, input, textarea, button, td, th {{
  font-family: 'Lexend', 'Atkinson Hyperlegible', sans-serif !important; font-size: {base}px;
  letter-spacing: {letter}; word-spacing: {word}; line-height: {line}; text-align: left; font-style: normal !important; }}
h1, h2, h3, h4 {{ font-family: 'Fredoka', 'Lexend', sans-serif !important; color: {T} !important;
  font-weight: 600 !important; letter-spacing: .01em; line-height: 1.25; }}
.stApp {{ background: {BG}; color: {T}; transition: background .35s ease, color .35s ease; }}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp small, .stApp summary,
[data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] * {{ color: {T}; }}

/* chrome: no deploy button / toolbar / rainbow bar; header see-through so the title can sit high */
[data-testid="stAppDeployButton"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], #MainMenu {{ display: none !important; }}
[data-testid="stHeader"] {{ background: transparent !important; height: 2.75rem; pointer-events: none; }}
[data-testid="stHeader"] button, [data-testid="stToolbar"] {{ pointer-events: auto; }}
[data-testid="stToolbar"] {{ background: transparent !important; }}
[data-testid="stExpandSidebarButton"] {{ background: {BU} !important; border: 2px solid {A} !important; border-radius: 999px !important;
  box-shadow: 0 4px 12px {SH} !important; width: 2.4rem; height: 2.4rem; margin: .4rem 0 0 .2rem;
  animation: nudge 3.5s ease-in-out infinite; }}
[data-testid="stExpandSidebarButton"] * {{ color: {OBU} !important; }}
[data-testid="stExpandSidebarButton"]:hover {{ transform: scale(1.08); }}
@keyframes nudge {{ 0%, 80%, 100% {{ transform: translateX(0); }} 87% {{ transform: translateX(4px); }} 93% {{ transform: translateX(0); }} }}
[data-testid="stMainBlockContainer"], .block-container {{ position: relative; z-index: 0;
  padding-top: 1rem !important; padding-bottom: 4.5rem !important; }}
/* the invisible style / waves / script elements shouldn't take up layout space */
[data-testid="stElementContainer"]:has(style), [data-testid="stElementContainer"]:has(.waves),
[data-testid="stElementContainer"]:has(script), .stHtml:has(script) {{ position: absolute !important; height: 0 !important;
  margin: 0 !important; overflow: visible; }}
[data-testid="stSidebarHeader"] {{ position: absolute !important; top: 0; right: 0; height: auto !important;
  padding: .5rem .6rem 0 0 !important; z-index: 5; background: transparent !important; }}
.stApp h1 {{ padding-top: 0 !important; margin-top: 0 !important; font-size: 2.3rem; }}
.hl {{ background: linear-gradient(transparent 58%, {BU} 58%, {BU} 92%, transparent 92%);
  padding: 0 .12em; border-radius: 4px; color: inherit; -webkit-box-decoration-break: clone; }}
{".stApp .hl, .stApp .hl .wig { background: none; color: " + BU + " !important; padding: 0; }" if dark else ""}

[data-testid="stSidebar"] {{ background: {S}; border-right: 2px solid {L}; }}
[data-testid="stSidebar"] h3 {{ display: flex; align-items: center; gap: .45em; }}
[data-testid="stSidebar"] h3::before {{ content: ""; flex: none; width: .9em; height: .9em;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Cpath d='M10 1.5 L12.3 7.7 L18.5 10 L12.3 12.3 L10 18.5 L7.7 12.3 L1.5 10 L7.7 7.7Z' fill='{BU.replace("#", "%23")}' stroke='{A.replace("#", "%23")}' stroke-width='{"0" if dark else "1.3"}' stroke-linejoin='round'/%3E%3C/svg%3E") center / contain no-repeat; }}
.badge.nemo {{ background: {BU}; border-color: {A}; color: {OBU} !important; }}

/* gentle animated waves along the bottom */
.waves {{ position: fixed; left: 0; right: 0; bottom: 0; height: 160px; z-index: -1; pointer-events: none; overflow: hidden; }}
.wl {{ position: absolute; left: 0; right: 0; bottom: 0; height: 100%; transform-origin: bottom;
  animation: swell 9s ease-in-out infinite; }}
.wave {{ position: absolute; bottom: 0; left: 0; width: 200%; height: 100%; animation: drift 30s linear infinite; }}
.wl.w1 .wave {{ animation-duration: 30s; }}
.wl.w2 {{ height: 85%; animation-duration: 11s; animation-delay: -3s; }} .wl.w2 .wave {{ animation-duration: 42s; animation-direction: reverse; }}
.wl.w3 {{ height: 65%; animation-duration: 7s; animation-delay: -5s; }} .wl.w3 .wave {{ animation-duration: 22s; }}
.wl.w4 {{ height: 48%; animation-duration: 8.5s; animation-delay: -1.5s; }} .wl.w4 .wave {{ animation-duration: 34s; animation-direction: reverse; }}
.wl.w5 {{ height: 125%; animation-duration: 13s; animation-delay: -7s; }} .wl.w5 .wave {{ animation-duration: 55s; }}
@keyframes swell {{ 0%, 100% {{ transform: translateY(0) scaleY(1); }} 50% {{ transform: translateY(-6px) scaleY(1.12); }} }}
@keyframes drift {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-50%); }} }}

.card {{ background: {S}; border: 2px solid {L}; border-radius: 26px; padding: 20px 24px;
  margin: 0 0 18px 0; box-shadow: 0 8px 22px {SH}; color: {T}; }}
.card h4 {{ margin: 0 0 8px 0; font-size: 1.2rem; }}
.card.strong {{ border-color: {A}; }}
.card ul {{ padding-left: 1.2rem; }} .card li {{ margin-bottom: .5rem; }}
.bubble {{ background: {S}; border: 2px solid {A}; border-radius: 30px; padding: 16px 22px;
  font-weight: 500; font-size: 1.08em; color: {T}; position: relative; margin-top: 22px;
  box-shadow: 0 8px 22px {SH}; }}
.bubble::before {{ content: ""; position: absolute; left: -38px; top: 30px; width: 40px; height: 34px;
  background: url("data:image/svg+xml,{tail}") no-repeat center / contain; }}
.badge {{ display: inline-block; background: {BG}; color: {T}; border: 1.5px solid {L};
  border-radius: 999px; padding: 2px 12px; font-weight: 500; font-size: .82em; margin: 2px 6px 4px 0; }}
.badge.solid {{ background: {BTN}; border-color: {A}; color: {BT}; }}
.badge.butter, .stApp .badge.butter {{ background: {BU}; border-color: {BU}; color: {OBU} !important; }}
.muted {{ color: {T}; opacity: .9; font-size: .93em; }}
.lever-row {{ margin: 10px 0 14px 0; }}
.lever-top {{ display: flex; justify-content: space-between; font-weight: 500; gap: 8px; }}
.bar-wrap {{ background: {BG}; border-radius: 999px; height: 16px; overflow: hidden; }}
.bar {{ background: {BAR}; height: 100%; border-radius: 999px; }}
.bar.primary {{ background: {A}; }}
.formula {{ font-family: 'Fredoka', sans-serif; font-size: 1.45rem; text-align: center; color: {T}; padding: 10px; }}
.formula .up {{ color: {A}; }}
.pip-wrap {{ background: radial-gradient(circle at 50% 55%, {BU}{"40" if dark else "99"} 0%, transparent 62%);
  border-radius: 50%; }}
.pip {{ animation: bob 4s ease-in-out infinite; display: block; margin: 0 auto; }}
@keyframes bob {{ 50% {{ transform: translateY(-6px); }} }}

/* buttons: round, soft, with a little squish */
.stButton button, .stDownloadButton button, .stFormSubmitButton > button,
[data-testid="stPopover"] > div > button, .stPopover button {{
  border-radius: 999px !important; border: 2px solid {A} !important;
  background: {BTN} !important; color: {BT} !important; font-weight: 600 !important;
  box-shadow: 0 4px 12px {SH} !important; padding: .5rem 1.4rem !important;
  transition: transform .12s ease, background .2s ease, box-shadow .2s ease !important; }}
.stButton button p, .stDownloadButton button p, .stFormSubmitButton > button p,
.stPopover button p, .stPopover button span {{ color: inherit !important; }}
.stButton button:hover, .stDownloadButton button:hover, .stPopover button:hover {{ background: {S} !important; }}
.stButton button:active, .stDownloadButton button:active, .stFormSubmitButton > button:active,
.stPopover button:active {{ transform: scale(.95); }}
.stApp .stFormSubmitButton button {{ background: {BU} !important; border-color: {A} !important; color: {OBU} !important; }}
.stApp .stFormSubmitButton button *, .stApp .stButton button *, .stApp .stDownloadButton button *,
.stApp .stPopover button * {{ color: inherit !important; }}
[data-testid="stAudioInputWaveformTimeCode"], [data-testid="stAudioInput"] [data-testid="stElementToolbarButtonContainer"] {{
  background: transparent !important; color: {T} !important; }}
[data-testid="stSidebarUserContent"] {{ padding-top: .9rem !important; }}
[data-testid="stSidebarUserContent"] > div > div > div > [data-testid="stElementContainer"]:first-child h3,
[data-testid="stSidebar"] h3:first-of-type {{ padding-top: 0 !important; }}
.stFormSubmitButton > button:hover {{ filter: brightness(1.04); box-shadow: 0 6px 18px {BU}88 !important; }}
.stButton button:focus-visible, .stFormSubmitButton > button:focus-visible {{ outline: 3px solid {A} !important; outline-offset: 3px; }}

/* inputs */
.stTextArea textarea, .stTextInput input {{ border-radius: 18px !important; border: 2px solid {L} !important;
  background: {S} !important; color: {T} !important; caret-color: {A}; }}
.stTextArea textarea::placeholder, .stTextInput input::placeholder {{ color: {T}; opacity: .55; }}
.stTextArea textarea:focus, .stTextInput input:focus {{ border-color: {A} !important; }}
.stTextArea [data-baseweb="textarea"], .stTextInput [data-baseweb="input"], [data-baseweb="base-input"] {{
  background: transparent !important; border: none !important; }}
[data-testid="InputInstructions"] {{ display: none !important; }}
[data-testid="stForm"] {{ border: none !important; padding: 0 !important; background: transparent !important; }}
.hint {{ font-size: .85em; opacity: .8; margin: -6px 0 6px 4px; }}
kbd {{ font-family: 'Lexend', sans-serif; background: {S}; border: 1.5px solid {L}; border-bottom-width: 3px;
  border-radius: 8px; padding: 0 .45em; font-size: .9em; color: {T}; }}

/* tabs */
.stTabs [data-baseweb="tab"] {{ font-weight: 500; color: {T}; background: transparent; }}
.stTabs [data-baseweb="tab"] p {{ color: inherit; }}
.stTabs [aria-selected="true"] {{ color: {A} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {A} !important; height: 3px; border-radius: 3px; }}
.stTabs [data-baseweb="tab-border"] {{ background: {L} !important; }}

/* native widgets, themed for both modes */
[data-testid="stExpander"] details, [data-testid="stFileUploaderDropzone"], [data-testid="stAudioInput"] > div,
[data-testid="stPopoverBody"], [data-baseweb="popover"] > div {{
  background: {S} !important; border: 2px solid {L} !important; border-radius: 20px !important; color: {T}; }}
[data-testid="stFileUploaderDropzone"] * , [data-testid="stExpander"] summary * {{ color: {T} !important; }}
[data-testid="stFileChip"], .stFileChip {{ background: {BG} !important; border: 1.5px solid {L} !important; border-radius: 14px !important; }}
[data-testid="stFileChip"] *, .stFileChip * {{ color: {T} !important; }}
[data-testid="stFileUploaderDropzone"] button, [data-testid="stFileUploader"] button {{ background: {BTN} !important;
  border: 2px solid {L} !important; border-radius: 999px !important; color: {BT} !important; }}
[data-testid="stAlert"] > div {{ border-radius: 18px; }}
{f'[data-testid="stAlert"] > div {{ background: {S} !important; border: 2px solid {L}; }} [data-testid="stAlert"] * {{ color: {T} !important; }}' if dark else ""}
[data-testid="stJson"] {{ background: {S} !important; border-radius: 14px; }}
[data-testid="stSpinner"] * {{ color: {T} !important; }}
[data-testid="stSlider"] [data-testid="stSliderThumbValue"], [data-testid="stSlider"] [data-testid="stTickBar"] * {{ color: {T} !important; }}
hr {{ border-color: {L} !important; }}

/* simple tables (replace dataframes so both themes match) */
.tbl-wrap {{ overflow-x: auto; margin-bottom: 18px; border: 2px solid {L}; border-radius: 20px; background: {S};
  box-shadow: 0 8px 22px {SH}; }}
.tbl {{ border-collapse: collapse; width: 100%; color: {T}; }}
.tbl th, .tbl td {{ padding: 10px 16px; text-align: left; border-bottom: 1.5px solid {L}; }}
.tbl tr:last-child td {{ border-bottom: none; }}
.tbl th {{ font-weight: 600; background: {BG}; }}

/* settings popover */
.set-h {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.05em; margin: 4px 0 2px 0; }}

/* sparkles from fx.js */
.pip-sparkle {{ position: fixed; z-index: 99999; pointer-events: none; border-radius: 2px;
  clip-path: polygon(50% 0, 62% 38%, 100% 50%, 62% 62%, 50% 100%, 38% 62%, 0 50%, 38% 38%);
  filter: drop-shadow(0 0 2px {BU}); }}

/* ---------- Pip: flaps, blinks, follows, hops ---------- */
svg.pip {{ cursor: pointer; overflow: visible; }}
svg.pip .wing {{ transform-box: view-box; animation: flapL 6.5s ease-in-out infinite; }}
svg.pip .wing-r {{ animation-name: flapR; }}
@keyframes flapL {{ 0%, 82%, 100% {{ transform: rotate(0); }} 85% {{ transform: rotate(-24deg); }} 88% {{ transform: rotate(0); }}
  91% {{ transform: rotate(-20deg); }} 94% {{ transform: rotate(0); }} }}
@keyframes flapR {{ 0%, 82%, 100% {{ transform: rotate(0); }} 85% {{ transform: rotate(24deg); }} 88% {{ transform: rotate(0); }}
  91% {{ transform: rotate(20deg); }} 94% {{ transform: rotate(0); }} }}
svg.pip:hover .wing {{ animation-duration: 1.2s; }}
svg.pip .pip-eyes {{ transition: transform .18s ease-out; }}
svg.pip .blink {{ transform-box: view-box; transform-origin: 100px 104px; animation: blink 5.2s infinite; }}
@keyframes blink {{ 0%, 93%, 100% {{ transform: scaleY(1); }} 95% {{ transform: scaleY(.08); }} 97% {{ transform: scaleY(1); }} }}
svg.pip .pip-hop {{ transform-box: view-box; transform-origin: 100px 190px; }}
.pip-heart {{ position: fixed; z-index: 99999; pointer-events: none; fill: {PINK}; filter: drop-shadow(0 1px 1px rgba(0,0,0,.08)); }}
.pip-say {{ position: fixed; z-index: 99999; pointer-events: none; background: {S}; color: {T}; border: 2px solid {A};
  border-radius: 18px 18px 18px 4px; padding: 4px 14px; font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.05rem;
  white-space: nowrap; box-shadow: 0 6px 16px {SH}; }}
.pip-snow {{ position: fixed; z-index: 99999; pointer-events: none; border-radius: 50%; opacity: .9;
  box-shadow: 0 0 0 1px {L}; }}

/* ---------- Pip is thinking ---------- */
.bubble.thinking {{ display: flex; align-items: center; gap: .5em; flex-wrap: wrap; }}
.bubble.thinking .muted {{ font-size: .78em; opacity: .6; font-weight: 400; }}
.pipping {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.1em; }}
.dots b {{ display: inline-block; animation: dot 1.2s infinite; font-weight: 600; }}
.dots b:nth-child(2) {{ animation-delay: .15s; }} .dots b:nth-child(3) {{ animation-delay: .3s; }}
@keyframes dot {{ 0%, 60%, 100% {{ transform: translateY(0); }} 30% {{ transform: translateY(-5px); }} }}
.stopwatch {{ margin-left: auto; display: inline-flex; align-items: center; gap: .35em; background: {BU}; color: {OBU} !important;
  border: 2px solid {A}; border-radius: 999px; padding: 2px 12px 2px 8px; font-weight: 600; font-variant-numeric: tabular-nums; }}
.stApp .stopwatch span {{ color: {OBU} !important; }}
.stopwatch .hand {{ transform-origin: 12px 13.5px; animation: sweep 1s steps(8) infinite; }}
@keyframes sweep {{ to {{ transform: rotate(360deg); }} }}

/* ---------- little touches around the page ---------- */
.hl {{ white-space: nowrap; }}  /* keep "unstuck" whole when the title wraps */
.hl .wig {{ display: inline-block; transition: transform .2s; }}
.hl:hover .wig {{ animation: wig .55s ease calc(var(--i) * 45ms); }}
@keyframes wig {{ 30% {{ transform: translateY(-7px) rotate(-4deg); }} 60% {{ transform: translateY(1px); }} }}
.card {{ transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; }}
.card:hover {{ transform: translateY(-3px); box-shadow: 0 14px 30px {SH}; border-color: {A}; }}
.bar {{ transform-origin: left; animation: grow 1.1s cubic-bezier(.2,.8,.3,1) both; }}
@keyframes grow {{ from {{ transform: scaleX(0); }} }}
.bubble {{ animation: popin .35s ease-out both; }}
@keyframes popin {{ from {{ transform: scale(.94); opacity: 0; }} }}
.badge {{ transition: transform .2s; }} .badge:hover {{ transform: translateY(-2px) rotate(-2deg); }}
.waves.big {{ height: 240px; }} .waves.big .wave {{ animation-duration: 14s !important; }} .waves.big .wl {{ animation-duration: 5s; }}

/* ---------- Pip branding ---------- */
.brand {{ display: flex; align-items: center; gap: .55rem; margin: -.2rem 0 .3rem 0; }}
.brand svg.pip {{ animation-duration: 3s; flex: none; margin: 0 !important; }}
.brand-name {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 2rem; line-height: 1; color: {T}; }}
.brand-name .dot {{ color: {BU}; -webkit-text-stroke: 1.5px {A}; }}
/* narrow screens: push the title below the fixed corner buttons; Sound shrinks to just its icon */
@media (max-width: 900px) {{
  [data-testid="stMainBlockContainer"], .block-container {{ padding-top: 3.9rem !important; }}
}}
@media (min-width: 901px) {{ .stApp h1 {{ padding-right: 9.5rem !important; }} }}  /* room for the Sound button */
@media (max-width: 600px) {{
  .st-key-vol_corner button [data-testid="stMarkdownContainer"] {{ display: none !important; }}
  .st-key-vol_corner button {{ padding: .35rem .7rem !important; }}
  .stApp h1 {{ font-size: 1.85rem; }}
}}
/* volume button in the top-right corner */
.st-key-vol_corner {{ position: fixed !important; top: .55rem; right: 1rem; z-index: 999990; width: auto !important; }}
.st-key-vol_corner button {{ border-radius: 999px !important; border: 2px solid {A} !important; background: {S} !important;
  color: {T} !important; box-shadow: 0 4px 12px {SH} !important; padding: .3rem .9rem !important; min-height: 0 !important; }}
.st-key-vol_corner button:hover {{ background: {BU} !important; color: {OBU} !important; }}
.st-key-vol_corner button * {{ color: inherit !important; }}
.nemo-wrap {{ display: flex; justify-content: center; }}
.stApp .st-key-dl_past button, .stApp .st-key-dl_more button, .stApp .st-key-dl_less button {{
  background: transparent !important; border: 2px dashed {L} !important; box-shadow: none !important;
  padding: 3px 14px !important; min-height: 0 !important; font-size: .85em !important; margin: 2px 0 8px; }}
.stApp .st-key-dl_past button:hover, .stApp .st-key-dl_more button:hover, .stApp .st-key-dl_less button:hover {{
  border-color: {A} !important; background: {S} !important; }}
.stApp .st-key-sci_btn button {{ background: transparent !important; border: none !important; box-shadow: none !important;
  padding: 2px 6px !important; min-height: 0 !important; font-size: .82em !important; font-weight: 500 !important; opacity: .8; }}
.stApp .st-key-sci_btn button:hover {{ opacity: 1; background: transparent !important; }}
.stApp .st-key-sci_btn button p {{ font-size: 1em !important; }}
.badge.nemo {{ display: inline-flex; align-items: center; justify-content: center; text-align: center !important;
  padding: 5px 16px; line-height: 1.25; margin: 0; }}
/* footer: a little cloud fixed at the very bottom */
.pip-foot-wrap {{ position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); z-index: 60; }}
.pebble-peek {{ position: absolute; left: 50%; bottom: 62%; width: 118px; transform: translate(-50%, 46px) scale(.5);
  opacity: 0; transition: transform .45s cubic-bezier(.2,1.5,.4,1), opacity .25s; pointer-events: none; z-index: -1; }}
.pebble-peek img {{ width: 100%; display: block; filter: drop-shadow(0 4px 8px {SH}); }}
.pebble-say {{ position: absolute; left: 92%; top: -14px; white-space: nowrap; background: {S}; color: {T};
  border: 2px solid {A}; border-radius: 14px 14px 14px 4px; padding: 3px 10px; font-family: 'Fredoka', sans-serif;
  font-weight: 600; font-size: .78rem; box-shadow: 0 4px 10px {SH}; }}
.pip-foot-wrap:hover .pebble-peek {{ transform: translate(-50%, 0) scale(1); opacity: 1; }}
.pip-foot a {{ color: {A} !important; font-weight: 600; text-decoration: none; border-bottom: 1.5px dotted {A}; }}
.pip-foot a:hover {{ border-bottom-style: solid; }}
.pebble-walk {{ position: fixed; bottom: 34px; left: -140px; width: 120px; z-index: 99998; pointer-events: none;
  filter: drop-shadow(0 6px 10px {SH}); }}
.pebble-pop {{ position: fixed; width: 96px; z-index: 99998; pointer-events: none; filter: drop-shadow(0 6px 10px {SH}); }}
[data-testid="stDialog"] [role="dialog"] {{ background: {BG} !important; border-radius: 26px !important; border: 2px solid {L}; }}
[data-testid="stDialog"] [role="dialog"] * {{ color: {T}; }}
.stApp .pip-foot {{ position: relative; margin: 0;
  background: {S}; color: {T}; border-radius: 999px; padding: 8px 26px 7px; font-size: .7em; line-height: 1.3;
  white-space: nowrap; text-align: center !important;
  filter: drop-shadow(0 0 1.5px {A}88) drop-shadow(0 4px 10px {SH}); }}
.pip-foot-wrap {{ animation: float 6s ease-in-out infinite; }}
@keyframes float {{ 0%, 100% {{ transform: translate(-50%, 0); }} 50% {{ transform: translate(-50%, -3px); }} }}
.pip-foot b {{ font-family: 'Fredoka', sans-serif; }}

/* ---------- My week: calendars ---------- */
.mini-cal, .week-cal {{ background: {S}; border: 2px solid {L}; border-radius: 24px; padding: 14px 16px 16px;
  box-shadow: 0 8px 22px {SH}; margin-bottom: 10px; }}
.mc-title, .wk-title {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.15rem; margin-bottom: 8px; }}
.mc-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }}
.mh {{ text-align: center !important; font-size: .75em; font-weight: 600; opacity: .7; }}
.md {{ position: relative; aspect-ratio: 1; border-radius: 12px; display: flex; flex-direction: column; align-items: center;
  justify-content: center; font-size: .85em; cursor: default; transition: background .15s, transform .15s; outline: none; }}
.md:hover, .md:focus {{ background: {BG}; transform: scale(1.08); z-index: 3; }}
.md.out {{ opacity: .35; }}
.md.today span {{ background: {BU}; color: {OBU}; border: 2px solid {A}; border-radius: 50%; width: 1.9em; height: 1.9em;
  display: flex; align-items: center; justify-content: center; font-weight: 600; }}
.md .dots {{ display: flex; gap: 2px; height: 6px; margin-top: 1px; }}
.md .dots i {{ width: 6px; height: 6px; border-radius: 50%; box-shadow: 0 0 0 1px {A}55; }}
.mtip {{ display: none; position: absolute; top: 105%; left: 50%; transform: translateX(-50%); width: 230px; z-index: 50;
  background: {S}; border: 2px solid {A}; border-radius: 16px; padding: 8px 10px; box-shadow: 0 10px 24px {SH}; text-align: left; }}
.md:hover .mtip, .md:focus .mtip {{ display: block; animation: popin .2s ease-out; }}
.mtip-h {{ font-weight: 600; font-size: .85em; margin-bottom: 4px; }}
.wk-scroll {{ overflow-x: auto; }}
.wk-grid {{ display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }}
@media (max-width: 900px) {{ .wk-grid {{ grid-template-columns: repeat(7, minmax(92px, 1fr)); min-width: 660px; }} }}
.wd {{ background: {BG}; border-radius: 16px; padding: 8px 5px; min-height: 190px; min-width: 0; border: 2px solid transparent; }}
.wd.today {{ border-color: {A}; background: {S}; box-shadow: inset 0 4px 0 {BU}; }}
.wd-h {{ display: flex; align-items: baseline; justify-content: space-between; padding: 0 4px 6px; font-size: .8em; }}
.wd-h b {{ font-family: 'Fredoka', sans-serif; font-size: 1.35em; }}
.wd.today .wd-h b {{ color: {A}; }}
.ev {{ background: var(--ev); color: #34568B !important; border-radius: 10px; padding: 4px 7px; margin-bottom: 5px; font-size: .74em;
  line-height: 1.35; overflow-wrap: break-word; hyphens: auto; border-left: 4px solid rgba(52,86,139,.35); cursor: default;
  transition: transform .15s ease, box-shadow .15s ease; }}
.ev:hover {{ transform: translateY(-2px); box-shadow: 0 4px 10px {SH}; }}
.ev b {{ color: #34568B !important; }}
.stApp .ev, .stApp .ev * {{ color: #34568B !important; }}
.more {{ font-size: .72em; opacity: .75; text-align: center !important; cursor: default; }}
.free {{ font-size: .75em; opacity: .45; text-align: center !important; padding-top: 1.2rem; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 2px 0 8px; font-size: .85em; }}
.lg {{ display: inline-flex; align-items: center; gap: 6px; }}
.lg i {{ width: 14px; height: 14px; border-radius: 5px; box-shadow: 0 0 0 1.5px {A}55; }}
[data-testid="stButtonGroup"] {{ margin-bottom: .2rem; }}

/* ---------- Pip's reminders ---------- */
.rms {{ display: flex; flex-direction: column; gap: 10px; }}
.rm {{ position: relative; border-radius: 18px; padding: 10px 14px 10px 18px; border: 2px solid var(--ev);
  background: color-mix(in srgb, var(--ev) {16 if dark else 30}%, {S}); box-shadow: 0 6px 16px {SH}; overflow: hidden;
  transition: transform .2s ease, box-shadow .2s ease; }}
.rm::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 7px; background: var(--ev);
  filter: saturate(1.6) brightness(.92); }}
.rm:hover {{ transform: translateX(3px); box-shadow: 0 10px 22px {SH}; }}
.rm-top {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }}
.stApp .rm-rel {{ font-size: .74em; font-weight: 600; background: var(--ev); color: #34568B !important; border-radius: 999px;
  padding: 1px 10px; }}
.rm-task {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.12em; margin-top: 4px; line-height: 1.25; }}
.rm-msg {{ font-size: .88em; opacity: .9; margin-top: 2px; }}
.rm-when {{ display: inline-flex; align-items: center; gap: 6px; font-weight: 600; font-size: .82em; border-radius: 999px;
  padding: 2px 11px; background: {S}; border: 2px solid {L}; white-space: nowrap; }}
.rm-when.soon, .rm-when.now {{ background: {BU}; border-color: {A}; color: {OBU} !important; }}
.stApp .rm-when.soon *, .stApp .rm-when.now * {{ color: {OBU} !important; }}
.rm-when i {{ width: 8px; height: 8px; border-radius: 50%; background: {A}; animation: ping 1.4s ease-out infinite; }}
@keyframes ping {{ 0% {{ box-shadow: 0 0 0 0 {A}aa; }} 100% {{ box-shadow: 0 0 0 9px {A}00; }} }}
.rm.now, .rm.soon {{ border-color: {A}; }}
.rm.now {{ animation: nudge2 2.4s ease-in-out infinite; }}
@keyframes nudge2 {{ 0%, 85%, 100% {{ transform: none; }} 90% {{ transform: rotate(-.6deg); }} 95% {{ transform: rotate(.6deg); }} }}
.rm.faded {{ opacity: .6; box-shadow: none; }}
.rm-past summary {{ cursor: pointer; font-size: .85em; opacity: .8; margin: 2px 0 8px; }}
.rm-past .rm {{ margin-bottom: 8px; }}
.rm-empty {{ border: 2px dashed {L}; border-radius: 18px; padding: 14px; font-size: .9em; opacity: .85; }}

/* ---------- colour picker swatches (pill order = EVENT_COLORS order) ---------- */
.st-key-swatches [data-testid="stWidgetLabel"] p {{ font-weight: 600; }}
.st-key-swatches .stButtonGroup button {{ padding: 2px 10px 2px 6px !important; gap: 6px; }}
.st-key-swatches .stButtonGroup button::before {{ content: ""; width: 14px; height: 14px; border-radius: 50%; flex: none;
  margin-right: 6px; box-shadow: 0 0 0 1.5px {A}88; background: var(--sw, #fff); }}
.st-key-swatches .stButtonGroup button:nth-of-type(1)::before {{ background: #B8D6FA; }}
.st-key-swatches .stButtonGroup button:nth-of-type(2)::before {{ background: #FFE58A; }}
.st-key-swatches .stButtonGroup button:nth-of-type(3)::before {{ background: #FFC4D4; }}
.st-key-swatches .stButtonGroup button:nth-of-type(4)::before {{ background: #D9CFFB; }}
.st-key-swatches .stButtonGroup button:nth-of-type(5)::before {{ background: #C3EDDB; }}
.st-key-swatches .stButtonGroup button:nth-of-type(6)::before {{ background: #FFD5B8; }}
.st-key-swatches .stButtonGroup button:nth-of-type(7)::before {{ background: #E6EDF7; }}

/* ---------- what's jamming the gears ---------- */
.jam {{ background: {S}; border: 2px solid {L}; border-radius: 26px; padding: 16px 20px 14px; box-shadow: 0 8px 22px {SH};
  margin-bottom: 14px; }}
.jam-kicker {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.05rem; }}
.jam-head {{ display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }}
.jam-sure {{ font-size: .78em; opacity: .75; }}
.jam-main {{ position: relative; display: flex; gap: 16px; align-items: center; background: {BU}; border: 2.5px solid {A};
  border-radius: 22px; padding: 14px 18px; animation: jamIn .6s cubic-bezier(.2,1.4,.4,1) both; }}
.stApp .jam-main, .stApp .jam-main * {{ color: {OBU} !important; }}
@keyframes jamIn {{ from {{ transform: scale(.92) rotate(-1deg); opacity: 0; }} }}
.jam-icon {{ flex: none; width: 64px; height: 64px; border-radius: 50%; background: var(--lc, #FFFFFF); border: 2.5px solid {A};
  display: flex; align-items: center; justify-content: center; font-family: 'Fredoka', sans-serif; font-weight: 600;
  font-size: 2rem; animation: ring 2.2s ease-out infinite; }}
@keyframes ring {{ 0% {{ box-shadow: 0 0 0 0 {A}88; }} 70%, 100% {{ box-shadow: 0 0 0 12px {A}00; }} }}
.jam-tag {{ display: inline-block; font-size: .72em; font-weight: 600; background: #FFFFFF; border: 1.5px solid {A};
  border-radius: 999px; padding: 1px 10px; margin-bottom: 4px; }}
.jam-title {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.6rem; line-height: 1.15; }}
.jam-sub {{ font-size: .95em; font-weight: 500; }}
.jam-quote {{ margin-top: 8px; font-size: .88em; border-left: 3px solid {A}; padding-left: 10px; }}
.jam-dots {{ display: inline-flex; gap: 3px; vertical-align: middle; }}
.jam-dots i {{ width: 9px; height: 9px; border-radius: 50%; border: 1.5px solid {A}; }}
.jam-dots i.on {{ background: {A}; }}
.jam-main .jam-dots i {{ width: 12px; height: 12px; border-color: #34568B; }}
.jam-main .jam-dots i.on {{ background: #34568B; }}
.jam-others {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin-top: 10px; }}
.jam-mini {{ position: relative; border: 2px solid var(--lc); border-radius: 16px; padding: 7px 10px; font-size: .82em;
  background: color-mix(in srgb, var(--lc) {18 if dark else 28}%, {S}); cursor: help; outline: none;
  transition: transform .2s, box-shadow .2s; }}
.jam-mini:hover, .jam-mini:focus {{ transform: translateY(-2px); box-shadow: 0 8px 18px {SH}; z-index: 20; }}
.tipbox {{ display: none; position: absolute; left: 50%; bottom: calc(100% + 10px); transform: translateX(-50%); width: 260px;
  z-index: 30; background: {S}; border: 2px solid {A}; border-radius: 16px; padding: 10px 12px; font-size: .95em;
  line-height: 1.45; box-shadow: 0 12px 26px {SH}; text-align: left; }}
.tipbox::after {{ content: ""; position: absolute; left: 50%; top: 100%; transform: translateX(-50%); border: 8px solid transparent;
  border-top-color: {A}; }}
.tipbox b {{ display: block; margin-bottom: 2px; }}
.stApp .tipbox em {{ display: block; font-style: normal !important; margin-top: 6px; padding: 4px 8px; border-radius: 10px;
  background: var(--lc); color: #34568B !important; font-weight: 500; }}
.jam-mini:hover .tipbox, .jam-mini:focus .tipbox {{ display: block; animation: popin .18s ease-out; }}
.jam-tip {{ margin-top: 8px; display: inline-block; background: #FFFFFF; border: 1.5px solid {A}; border-radius: 12px;
  padding: 4px 10px; font-size: .88em; }}
.jam-mini b {{ display: block; font-family: 'Fredoka', sans-serif; font-size: 1.05em; }}
.jam-foot {{ font-size: .7em; opacity: .55; margin-top: 8px; }}
@media (max-width: 700px) {{ .jam-others {{ grid-template-columns: 1fr; }} }}

/* ---------- "Here's what I set up for you": numbered colour tiles ---------- */
.plan {{ position: relative; display: flex; align-items: center; gap: 14px; border: 2px solid var(--pc); border-radius: 20px;
  background: color-mix(in srgb, var(--pc) {16 if dark else 30}%, {S}); padding: 12px 16px 12px 14px; margin-bottom: 12px;
  box-shadow: 0 6px 16px {SH}; animation: popin .35s ease-out both; transition: transform .2s; }}
.plan:hover {{ transform: translateX(3px); }}
.plan-num {{ position: absolute; top: -9px; left: -9px; width: 26px; height: 26px; border-radius: 50%; background: {A};
  color: #FFFFFF !important; font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: .85em; display: flex;
  align-items: center; justify-content: center; box-shadow: 0 2px 6px {SH}; }}
.plan-ic {{ flex: none; width: 46px; height: 46px; border-radius: 14px; background: var(--pc); color: #34568B;
  display: flex; align-items: center; justify-content: center; }}
.stApp .plan-ic svg {{ color: #34568B; }}
.plan-kick {{ font-size: .78em; font-weight: 600; opacity: .85; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
.stApp .plan-meta {{ background: var(--pc); color: #34568B !important; border-radius: 999px; padding: 0 9px; font-size: .95em; }}
.plan-main {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.15rem; line-height: 1.3; margin-top: 1px; }}
.plan-sub {{ font-size: .85em; opacity: .85; margin-top: 2px; }}

/* ---------- Coming up (deadlines) ---------- */
.dls {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }}
.dl {{ display: grid; grid-template-columns: auto 1fr auto auto; gap: 12px; align-items: center; background: {S};
  border: 2px solid {L}; border-left: 7px solid var(--ev); border-radius: 16px; padding: 8px 14px; box-shadow: 0 4px 12px {SH};
  transition: transform .2s; }}
.dl:hover {{ transform: translateX(3px); }}
.dl.past {{ opacity: .5; }}
.dl.hot {{ border-color: {A}; border-left-color: var(--ev); }}
.stApp .dl-chip {{ background: var(--ev); color: #34568B !important; border-radius: 999px; padding: 1px 10px; font-size: .75em; font-weight: 600; }}
.dl-main b {{ display: block; font-family: 'Fredoka', sans-serif; font-size: 1.05em; line-height: 1.2; }}
.dl-course {{ font-size: .78em; opacity: .75; }}
.dl-due {{ font-size: .85em; text-align: right !important; }}
.dl-w {{ display: block; font-size: .85em; opacity: .7; }}
.dl-pill {{ display: inline-flex; align-items: center; gap: 6px; font-size: .8em; font-weight: 600; border-radius: 999px;
  padding: 2px 11px; border: 2px solid {L}; white-space: nowrap; }}
.dl-pill.hot {{ background: {BU}; border-color: {A}; }} .stApp .dl-pill.hot {{ color: {OBU} !important; }}
.dl-pill.warm {{ background: {L}; }}
.dl-pill i {{ width: 8px; height: 8px; border-radius: 50%; background: {A}; animation: ping 1.4s ease-out infinite; }}
@media (max-width: 760px) {{ .dl {{ grid-template-columns: 1fr auto; }} .dl-chip, .dl-due {{ display: none; }} }}

/* ---------- science tab colours ---------- */
.lv-card {{ border-top: 8px solid var(--lc) !important; }}
.lv-card h4 {{ display: inline-block; background: var(--lc); color: #34568B !important; border-radius: 999px; padding: 1px 12px; }}
.fd-card {{ border-left: 8px solid var(--lc) !important; }}

/* reply bubble with a mini Pip so the tail points at someone */
.say {{ display: flex; align-items: center; gap: 30px; margin: 4px 0 22px; }}
.say svg.pip {{ flex: none; margin: 0 !important; }}
.say .bubble {{ margin-top: 0; flex: 1; }}
.say .bubble::before {{ top: 50%; margin-top: -17px; }}

/* check-in buttons: each option has its own colour */
.st-key-followup {{ border-top: 8px solid {BU} !important; }}
.stApp .st-key-fu_good button {{ background: {BU} !important; color: {OBU} !important; }}
.stApp .st-key-fu_stuck button {{ background: color-mix(in srgb, #FFC4D4 {35 if dark else 70}%, {S}) !important; border-color: #F49AB4 !important; }}
.stApp .st-key-fu_later button {{ background: color-mix(in srgb, #B8D6FA {35 if dark else 70}%, {S}) !important; }}
.stApp .st-key-fu_new button {{ background: color-mix(in srgb, #D9CFFB {35 if dark else 70}%, {S}) !important; border-color: #B6A6F2 !important; }}
.formula .fx {{ background: var(--lc); color: #34568B !important; border-radius: 12px; padding: 0 10px; }}

/* ---------- Pip's trick (compact) ---------- */
.move {{ display: flex; gap: 14px; align-items: flex-start; background: color-mix(in srgb, var(--lc, {L}) {14 if dark else 22}%, {S});
  border: 2px solid var(--lc, {L}); border-left: 6px solid {A};
  border-radius: 18px; padding: 10px 16px; margin-bottom: 14px; box-shadow: 0 6px 16px {SH}; }}
.move-kicker {{ font-size: .72em; font-weight: 600; opacity: .75; }}
.move-name {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 1.15rem; margin-right: 6px; }}
.move-how {{ font-size: .92em; margin-top: 2px; }}
.move-why {{ font-size: .8em; opacity: .85; margin-top: 4px; }}
.move-cite {{ font-size: .66em; opacity: .5; margin-top: 4px; }}
.move .plan-ic {{ background: var(--lc); width: 40px; height: 40px; margin-top: 4px; }}
.move .badge {{ font-size: .7em; padding: 0 9px; vertical-align: 2px; }}

/* ---------- My week tools (small, to the side) ---------- */
.st-key-wk_tools {{ margin-bottom: -.4rem; }}
.stApp .st-key-wk_tools button {{ min-height: 0 !important; padding: 3px 12px !important; font-size: .8em !important;
  white-space: nowrap; }}
.st-key-wk_tools button p {{ font-size: .95em !important; }}
.st-key-wk_tools [data-testid="stButtonGroup"] {{ margin: 0; }}

/* ---------- task check-in (follow-up) ---------- */
.st-key-followup {{ background: {S}; border: 2px solid {A}; border-radius: 26px; padding: 18px 22px 14px !important;
  box-shadow: 0 8px 22px {SH}; margin-top: .6rem; }}
.st-key-followup h3 {{ margin-top: 0 !important; padding-top: 0 !important; }}
.fu-bar {{ height: 10px; border-radius: 999px; background: {BG}; overflow: hidden; margin: 2px 0 4px; }}
.fu-bar i {{ display: block; height: 100%; background: {BU}; border-right: 2px solid {A}; border-radius: 999px;
  transition: width .4s ease; }}
.st-key-followup .stCheckbox label p {{ font-weight: 500; }}

/* ---------- "What helps you start" ---------- */
.pb-head {{ display: flex; gap: 16px; align-items: center; margin-bottom: 10px; }}
.pb-big {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 2.6rem; line-height: 1; background: {BU};
  color: {OBU} !important; border: 2px solid {A}; border-radius: 20px; padding: 6px 14px; }}
.stApp .pb-big span {{ font-size: .5em; color: {OBU} !important; }}
.pb-group {{ border-top: 2px solid {L}; padding-top: 10px; margin-top: 12px; }}
.pb-when {{ font-size: .9em; margin-bottom: 6px; }}
.pb-row {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 6px 0; }}
.pb-how {{ font-size: .85em; }}
.pb-score {{ text-align: right !important; font-size: .8em; white-space: nowrap; }}
.pb-dots {{ display: flex; gap: 4px; justify-content: flex-end; margin-bottom: 2px; }}
.pb-dots i {{ width: 12px; height: 12px; border-radius: 50%; border: 2px solid {A}; }}
.pb-dots i.y {{ background: {BU}; }}
.pb-tag {{ font-size: .72em; border: 1.5px solid {L}; border-radius: 999px; padding: 1px 9px; margin-left: 6px; white-space: nowrap; }}
.stApp .pb-tag.good {{ background: {BU}; border-color: {A}; color: {OBU} !important; }}
.pb-next {{ font-size: .85em; margin-top: 4px; }}
.pip-foot .heart {{ vertical-align: -1px; margin: 0 1px; }}

/* ---------- focus-sound scenery (behind content) ---------- */
.amb {{ position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden; }}
.amb i {{ position: absolute; display: block; font-style: normal !important; }}
.amb .cloud {{ left: 0; fill: {"#34548A" if dark else WHITE}; filter: drop-shadow(0 6px 10px {SH}); animation: cloud linear infinite; }}
@keyframes cloud {{ from {{ transform: translateX(-260px); }} to {{ transform: translateX(110vw); }} }}
.amb .drop {{ top: -30px; width: 2.5px; border-radius: 2px; background: linear-gradient(transparent, {A}); animation: rain linear infinite; }}
@keyframes rain {{ to {{ transform: translate(-30px, 112vh); }} }}
.amb .note {{ bottom: -40px; color: {A}; font-family: 'Fredoka', sans-serif; animation: note ease-in-out infinite; }}
.amb .note.alt {{ color: {BU}; -webkit-text-stroke: 1px {A}; }}
@keyframes note {{ 0% {{ transform: translate(0, 0) rotate(-8deg); opacity: 0; }} 15% {{ opacity: .5; }}
  50% {{ transform: translate(22px, -45vh) rotate(8deg); }} 85% {{ opacity: .4; }}
  100% {{ transform: translate(-10px, -90vh) rotate(-6deg); opacity: 0; }} }}
.amb .bubble-o {{ bottom: -20px; border-radius: 50%; border: 1.5px solid {A}; background: {L}55; animation: rise ease-in infinite; }}
@keyframes rise {{ 0% {{ transform: translate(0, 0); opacity: 0; }} 10% {{ opacity: .7; }}
  50% {{ transform: translate(12px, -35vh); }} 100% {{ transform: translate(-8px, -75vh); opacity: 0; }} }}
.amb .twinkle {{ fill: {BU}; animation: twinkle ease-in-out infinite; }}
.amb .twinkle.alt {{ fill: {L}; }}
@keyframes twinkle {{ 0%, 100% {{ transform: scale(.3) rotate(0deg); opacity: .15; }} 50% {{ transform: scale(1) rotate(45deg); opacity: .9; }} }}
[data-testid="stElementContainer"]:has(.amb) {{ position: absolute !important; height: 0 !important; margin: 0 !important; }}
.stButtonGroup button, [data-testid="stButtonGroup"] button {{ border-radius: 999px !important; border: 2px solid {L} !important;
  background: {S} !important; color: {T} !important; transition: transform .15s ease !important; }}
.stButtonGroup button:hover {{ transform: translateY(-1px); border-color: {A} !important; }}
.stButtonGroup button[kind*="Active"], .stButtonGroup button[data-testid*="Active"], .stButtonGroup button[aria-checked="true"],
.stButtonGroup button[aria-pressed="true"] {{ background: {BU} !important; border-color: {A} !important; color: {OBU} !important; }}
.stButtonGroup button * {{ color: inherit !important; }}

@media (prefers-reduced-motion: reduce) {{ .wave, .pip, .amb, svg.pip * {{ animation: none !important; }} }}
{".amb { display: none; }" if still else ""}
{motion_off}
</style>
"""


TIDALBYTE_URL = "https://f26.tidaltamu.com/"
_PEBBLE = base64.b64encode((Path(__file__).resolve().parent.parent / "assets" / "pebble.png").read_bytes()).decode()


def footer_html() -> str:
    """Fixed footer pill. Easter egg: hover it and Pebble (tidalBYTE's penguin) peeks out;
    'tidalBYTE' links to the hackathon site. fx.js reuses this <img> for more Pebble cameos."""
    return (f'<div class="pip-foot-wrap"><div class="pebble-peek" aria-hidden="true">'
            f'<img src="data:image/png;base64,{_PEBBLE}" alt="Pebble the penguin">'
            f'<span class="pebble-say">Hi! I\'m Pebble from tidalBYTE!</span></div>'
            f'<p class="pip-foot"><b>Pip</b> · made with {HEART_SVG} by two ADHD brains at '
            f'<a href="{TIDALBYTE_URL}" target="_blank" rel="noopener">tidalBYTE \'26</a></p></div>')


HEART_SVG = (f'<svg class="heart" viewBox="0 0 24 22" width="13" height="12" aria-label="love">'
             f'<path fill="{PINK}" d="M12 21s-8.5-5.3-10.6-10.1C-.3 6.9 2.3 2 6.6 2 9 2 10.7 3.4 12 5.2 '
             f'13.3 3.4 15 2 17.4 2c4.3 0 6.9 4.9 5.2 8.9C20.5 15.7 12 21 12 21z"/></svg>')


def playbook_html(stats: list, levers: dict, next_pick: dict) -> str:
    """'What helps you start': Pip's memory of which tricks got you going, in plain words."""
    tried = sum(s["tried"] for s in stats)
    worked = sum(s["worked"] for s in stats)
    head = (f'<div class="pb-head"><div class="pb-big">{worked}<span>/{tried}</span></div><div>'
            f'<b>check-ins where Pip\'s trick helped.</b><br><span class="muted">Every time you check in on a task, '
            f'Pip remembers which trick helped, and picks better ones next time.</span></div></div>')
    groups = []
    for key, lv in levers.items():
        rows = [s for s in stats if s["lever"] == key]
        if not rows:
            continue
        items = []
        for s in sorted(rows, key=lambda r: (r["worked"] / r["tried"], r["tried"]), reverse=True):
            rate = s["worked"] / s["tried"]
            tag = ("<span class='pb-tag good'>works for you</span>" if s["worked"] and rate >= .5
                   else "<span class='pb-tag'>didn't click yet</span>" if not s["worked"]
                   else "<span class='pb-tag'>sometimes</span>")
            dots = "".join("<i class='y'></i>" for _ in range(s["worked"])) + \
                   "".join("<i></i>" for _ in range(s["tried"] - s["worked"]))
            items.append(f"<div class='pb-row'><div><b>{escape(s['name'])}</b> {tag}<div class='muted pb-how'>"
                         f"{escape(s['how'])}</div></div><div class='pb-score'><div class='pb-dots'>{dots}</div>"
                         f"<span>helped {s['worked']} of {s['tried']}</span></div></div>")
        nxt = next_pick.get(key)
        nxt_html = f"<div class='pb-next'>Next time: Pip will try <b>{escape(nxt)}</b></div>" if nxt else ""
        groups.append(f"<div class='pb-group'><div class='pb-when'>When you feel: <b>{escape(lv['label'])}</b></div>"
                      f"{''.join(items)}{nxt_html}</div>")
    return f"<div class='card pb'>{head}{''.join(groups)}</div>"


def table_html(rows: list[dict]) -> str:
    if not rows:
        return ""
    cols = list(rows[0])
    head = "".join(f"<th>{escape(str(c))}</th>" for c in cols)
    body = "".join("<tr>" + "".join(f"<td>{escape('' if r.get(c) is None else str(r.get(c)))}</td>" for c in cols)
                   + "</tr>" for r in rows)
    return f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


CSS = css()  # default, for quick previews


def card(title: str, body_html: str, strong=False, badges=()) -> str:
    b = "".join(f'<span class="badge">{escape(x)}</span>' for x in badges)
    return f'<div class="card{" strong" if strong else ""}"><h4>{escape(title)}</h4>{b}<div>{body_html}</div></div>'


# One colour per lever / plan item, used everywhere (same pastels as the calendar).
LEVER_COLORS = {"expectancy": "#FFC4D4", "value": "#D9CFFB", "impulsiveness": "#C3EDDB", "delay": "#B8D6FA"}
PLAN_COLORS = {"first_step": "#C3EDDB", "calendar": "#B8D6FA", "checkin": "#FFE58A", "goal_link": "#D9CFFB"}
_ICONS = {
    "first_step": '<path d="M6 21V4M6 4h11l-2.5 4L17 12H6"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8.5 3v4M15.5 3v4"/>',
    "checkin": '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20.5a2 2 0 0 0 4 0"/>',
    "goal_link": '<path d="M12 3.5l2.5 5.3 5.8.7-4.3 4 1.1 5.7L12 16.4l-5.1 2.8 1.1-5.7-4.3-4 5.8-.7z"/>',
    "move": '<path d="M12 3a6 6 0 0 0-3.5 10.9V17h7v-3.1A6 6 0 0 0 12 3zM9.5 20.5h5"/>',
}


def icon(name: str, size=22) -> str:
    return (f'<svg viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_ICONS[name]}</svg>')


def jam_html(diag: dict, levers: dict) -> str:
    """What's jamming the gears: the main jam big and bright (Pip's insight + a quick idea),
    the other three small and colour-coded; hover/tap one to see Pip's take."""
    key = diag["primary_lever"]
    lv, sc, tips = levers[key], diag["scores"], diag.get("tips") or {}
    dots = lambda n: "<span class='jam-dots'>" + "".join(f"<i class='{'on' if i < n else ''}'></i>" for i in range(5)) + "</span>"
    useful = lambda t: t and "not mentioned" not in t.lower() and "demo mode" not in t.lower()
    ev = diag["evidence"].get(key, "")
    insight = f"<div class='jam-quote'>{escape(ev)}</div>" if useful(ev) else ""
    tip = f"<div class='jam-tip'><b>Try this:</b> {escape(tips[key])}</div>" if tips.get(key) else ""
    minis = []
    for k, v in levers.items():
        if k == key:
            continue
        why = diag["evidence"].get(k, "")
        box = (f"<span class='tipbox'><b>{escape(v['short'])}</b>{escape(why) if useful(why) else 'Not a big factor right now.'}"
               f"{f'<em>Try: {escape(tips[k])}</em>' if tips.get(k) else ''}</span>")
        minis.append(f"<div class='jam-mini' tabindex='0' style='--lc:{LEVER_COLORS[k]}'><b>{escape(v['short'])}</b>"
                     f"{dots(sc[k])} <span>{escape(v['label'])}</span>{box}</div>")
    sure = int(round(float(diag.get("confidence", 0) or 0) * 100))
    return (f"<div class='jam'><div class='jam-head'><span class='jam-kicker'>What's jamming the gears</span>"
            f"{f'<span class=jam-sure>Pip is {sure}% sure</span>' if sure else ''}</div>"
            f"<div class='jam-main' style='--lc:{LEVER_COLORS[key]}'><div class='jam-icon'>!</div><div>"
            f"<span class='jam-tag'>Your main jam</span>"
            f"<div class='jam-title'>{escape(lv['short'])} {dots(sc[key])}</div>"
            f"<div class='jam-sub'>{escape(lv['label'])}</div>{insight}{tip}</div></div>"
            f"<div class='jam-others'>{''.join(minis)}</div>"
            f"<div class='jam-foot'>Based on Temporal Motivation Theory (Steel, 2007). Hover or tap a box to see Pip's take.</div></div>")


def plan_html(n: int, kind: str, kicker: str, main: str, meta: str = "", sub: str = "") -> str:
    """One colour-coded, numbered tile in "Here's what I set up for you"."""
    return (f"<div class='plan' style='--pc:{PLAN_COLORS.get(kind, '#B8D6FA')}'><div class='plan-num'>{n}</div>"
            f"<div class='plan-ic'>{icon(kind)}</div><div class='plan-body'><div class='plan-kick'>{escape(kicker)}"
            f"{f'<span class=plan-meta>{escape(meta)}</span>' if meta else ''}</div>"
            f"<div class='plan-main'>{escape(main)}</div>{f'<div class=plan-sub>{escape(sub)}</div>' if sub else ''}</div></div>")


def deadlines_html(rows: list) -> str:
    """'Coming up' as colourful rows: type chip, title, due date, days-left pill (urgent = butter + pulse)."""
    out = []
    for r in rows:
        days = r["days"]
        if days is None:
            pill, cls = "no date", ""
        elif days < 0:
            pill, cls = "past", "past"
        elif days == 0:
            pill, cls = "today!", "hot"
        elif days <= 3:
            pill, cls = f"{days} day{'s' if days > 1 else ''} left", "hot"
        elif days <= 7:
            pill, cls = f"{days} days left", "warm"
        else:
            pill, cls = f"{days} days left", ""
        w = f"<span class='dl-w'>{r['weight']}% of grade</span>" if r.get("weight") not in (None, "") else ""
        out.append(f"<div class='dl {cls}' style='--ev:{r['color']}'><span class='dl-chip'>{escape(r['type'])}</span>"
                   f"<div class='dl-main'><b>{escape(r['title'])}</b><span class='dl-course'>{escape(r['course'])}</span></div>"
                   f"<div class='dl-due'>{escape(r['due'])}{w}</div><span class='dl-pill {cls}'>"
                   f"{'<i></i>' if cls == 'hot' else ''}{pill}</span></div>")
    return f"<div class='dls'>{''.join(out)}</div>"


def move_html(s: dict, reason: str) -> str:
    """Pip's trick, as a small strip: what to do, why this one, tiny citation."""
    return (f"<div class='move' style='--lc:{LEVER_COLORS.get(s.get('lever'), '#B8D6FA')}'>"
            f"<div class='plan-ic'>{icon('move')}</div><div><div class='move-kicker'>Pip's trick for this</div>"
            f"<span class='move-name'>{escape(s['name'])}</span><span class='badge'>{escape(s['discipline'])}</span>"
            f"<div class='move-how'>{escape(s['how'])}</div>"
            f"<div class='move-why'>{escape(reason)} {escape(s['adhd'])}</div>"
            f"<div class='move-cite'>Research: {escape(s['cite'])}</div></div></div>")


def lever_bar(label: str, short: str, score: int, primary: bool, evidence: str = "") -> str:
    pct = int(score / 5 * 100)
    tag = ' <span class="badge butter">main jam</span>' if primary else ""
    ev = f'<div class="muted">{escape(evidence)}</div>' if evidence else ""
    return (f'<div class="lever-row"><div class="lever-top"><span>{escape(short)} · {escape(label)}{tag}</span>'
            f'<span>{score}/5</span></div><div class="bar-wrap"><div class="bar{" primary" if primary else ""}" '
            f'style="width:{pct}%"></div></div>{ev}</div>')
