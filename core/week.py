"""My Week: friendly dates, 12/24-hour times, and the month + week calendar widgets.

Events come from three places:
  - syllabus deadlines (st.session_state.deadlines)
  - Pip's scheduled check-ins (data/checkins.json)
  - focus blocks Pip put on the calendar (data/block_*.ics)
"""
import calendar
import zlib
from datetime import date, datetime, timedelta
from html import escape

from . import config, tools

# Soft pastels for colour-coding calendar chips ONLY (text on them is always DEEP).
EVENT_COLORS = {
    "Sky": "#B8D6FA", "Butter": "#FFE58A", "Pink": "#FFC4D4", "Lavender": "#D9CFFB",
    "Mint": "#C3EDDB", "Peach": "#FFD5B8", "Cloud": "#E6EDF7",
}
_ORDER = list(EVENT_COLORS)


# ---------------- formatting ----------------
def fmt_date(d: date | datetime | str | None, weekday=False) -> str:
    """2026-11-21 -> 'Nov 21, 2026' (or 'Sat, Nov 21, 2026')."""
    d = to_date(d)
    if not d:
        return "No date"
    s = f"{d:%b} {d.day}, {d.year}"
    return f"{d:%a}, {s}" if weekday else s


def fmt_time(t: datetime | str | None, clock24: bool) -> str:
    if isinstance(t, str):
        try:
            t = datetime.strptime(t[:5], "%H:%M")
        except ValueError:
            return t
    if not t:
        return ""
    return f"{t:%H:%M}" if clock24 else f"{t.hour % 12 or 12}:{t:%M} {'AM' if t.hour < 12 else 'PM'}"


def fmt_dt(dt: datetime | str | None, clock24: bool, weekday=True) -> str:
    dt = to_dt(dt)
    return f"{fmt_date(dt, weekday)} at {fmt_time(dt, clock24)}" if dt else "No date"


def to_date(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str) and d:
        try:
            return datetime.strptime(d[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def to_dt(s):
    if isinstance(s, datetime):
        return s
    if isinstance(s, str) and s:
        for f in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y%m%dT%H%M%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(s[:19] if "-" in s else s[:15], f)
            except ValueError:
                continue
    return None


# ---------------- events ----------------
def _ics_blocks():
    out = []
    for p in sorted(config.DATA_DIR.glob("block_*.ics")):
        fields = {}
        for line in p.read_text().splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                fields.setdefault(k, v)
        start, end = to_dt(fields.get("DTSTART", "")), to_dt(fields.get("DTEND", ""))
        if start:
            out.append({"start": start, "end": end, "title": fields.get("SUMMARY", "Focus block"),
                        "note": fields.get("DESCRIPTION", "")})
    return out


def events(deadlines: list) -> list[dict]:
    """Every event as {day, time (datetime|None), title, kind, type, course, detail}."""
    ev = []
    for a in deadlines or []:
        d = to_date(a.get("due"))
        if not d:
            continue
        t = None
        if a.get("due_time"):
            try:
                t = datetime.combine(d, datetime.strptime(a["due_time"][:5], "%H:%M").time())
            except ValueError:
                t = None
        w = f" · {a['weight_pct']}% of grade" if a.get("weight_pct") not in (None, "") else ""
        ev.append({"day": d, "time": t, "title": a.get("title") or "Due", "kind": "Deadline",
                   "type": (a.get("type") or "other").title(), "course": a.get("course") or "Course",
                   "detail": f"{a.get('course', '')}{w}".strip(" ·")})
    for c in tools.list_checkins():
        dt = to_dt(c.get("when"))
        if dt:
            rel = match_deadline(c.get("task", ""), deadlines)  # colour it like the work it's about
            ev.append({"day": dt.date(), "time": dt, "title": f"Pip checks in: {c.get('task', '')}",
                       "kind": "Pip check-in", "task": c.get("task", ""), "msg": c.get("message", ""),
                       "type": (rel.get("type") or "other").title() if rel else "Pip check-in",
                       "course": (rel.get("course") or "Course") if rel else "Pip's plans",
                       "related": f"{_short_course(rel.get('course'))} · {rel.get('title')}" if rel else "",
                       "detail": c.get("message", "")})
    for b in _ics_blocks():
        mins = int((b["end"] - b["start"]).total_seconds() // 60) if b["end"] else 25
        ev.append({"day": b["start"].date(), "time": b["start"], "title": b["title"], "kind": "Focus block",
                   "type": "Focus block", "course": "Pip's plans", "detail": f"{mins} min. {b['note']}".strip()})
    ev.sort(key=lambda e: (e["day"], e["time"] or datetime.combine(e["day"], datetime.min.time())))
    return ev


_STOP = set("a an the to for of on in at my i im i'm and or with do get start study work working finish my your "
             "this that it is be due tonight tomorrow today week".split())
_GENERIC = {"homework", "exam", "quiz", "lab", "paper", "project", "report", "assignment", "other", "set"}
_ALIASES = {"chemistry": "chem", "stats": "stat", "statistics": "stat", "physics": "phys", "phy": "phys", "history": "hist", "english": "engl", "psychology": "psyc", "psych": "psyc", "biology": "biol", "bio": "biol", "economics": "econ", "mathematics": "math", "calc": "calculus", "hw": "homework",
            "pset": "homework", "problem": "homework", "midterm": "exam", "test": "exam", "essay": "paper"}


def _tokens(text: str) -> set:
    words = "".join(ch.lower() if ch.isalnum() else " " for ch in (text or "")).split()
    return {_ALIASES.get(w, w) for w in words if w not in _STOP and len(w) > 1}


def _short_course(course: str | None) -> str:
    return (course or "Course").split(" - ")[0].split(":")[0].strip()


def match_deadline(task: str, deadlines: list) -> dict | None:
    """Best syllabus item for a check-in's task (title words count double, course words once)."""
    t = _tokens(task)
    if not t or not deadlines:
        return None
    best, best_score = None, 0
    for a in deadlines:
        title_t = _tokens(a.get("title", "")) | ({_ALIASES.get((a.get("type") or "").lower(), (a.get("type") or "").lower())} - {""})
        title_hits, course_hits = t & title_t, t & _tokens(a.get("course", ""))
        if not (title_hits - _GENERIC) and not course_hits:
            continue  # "math homework" shouldn't match CHEM's "Homework 12" on the word "homework" alone
        score = 2 * len(title_hits) + len(course_hits)
        if score > best_score:
            best, best_score = a, score
    return best if best_score >= 2 else None


def _until(dt: datetime, now: datetime, clock24: bool) -> tuple[str, str]:
    """(label, urgency) e.g. ('in 25 min', 'soon')."""
    mins = int((dt - now).total_seconds() // 60)
    if mins < -1:
        ago = -mins
        return (f"{ago} min ago" if ago < 60 else (f"{ago // 60} h ago" if ago < 1440 else fmt_date(dt))), "past"
    if mins <= 1:
        return "now!", "now"
    if mins < 60:
        return f"in {mins} min", "soon"
    if dt.date() == now.date():
        return f"today {fmt_time(dt, clock24)}", "today"
    if dt.date() == now.date() + timedelta(days=1):
        return f"tomorrow {fmt_time(dt, clock24)}", "later"
    return f"{dt:%a} {fmt_time(dt, clock24)}", "later"


def reminders_html(ev: list, color_by: str, chosen: dict, clock24: bool, now: datetime, limit=5) -> str:
    """Pip's check-ins as colour-coded reminder cards with a live countdown."""
    items = [e for e in ev if e["kind"] == "Pip check-in"]
    upcoming = sorted([e for e in items if e["time"] >= now - timedelta(minutes=1)], key=lambda e: e["time"])
    past = sorted([e for e in items if e["time"] < now - timedelta(minutes=1)], key=lambda e: e["time"], reverse=True)

    def card(e, faded=False):
        label, urg = _until(e["time"], now, clock24)
        rel = f"<span class='rm-rel'>{escape(e['related'])}</span>" if e.get("related") else "<span class='rm-rel'>Pip's plan</span>"
        msg = f"<div class='rm-msg'>{escape(e['msg'])}</div>" if e.get("msg") else ""
        return (f"<div class='rm {urg}{' faded' if faded else ''}' style='--ev:{color_of(e, color_by, chosen)}'>"
                f"<div class='rm-top'>{rel}<span class='rm-when {urg}'>{'<i></i>' if urg in ('now', 'soon') else ''}"
                f"{escape(label)}</span></div><div class='rm-task'>{escape(e['task'] or 'Check-in')}</div>{msg}</div>")

    html = "".join(card(e) for e in upcoming[:limit])
    if not upcoming:
        html = "<div class='rm-empty'>Nothing coming up. Check in with Pip and Pip will nudge you here.</div>"
    if past:
        html += ("<details class='rm-past'><summary>Earlier (" + str(len(past)) + ")</summary>"
                 + "".join(card(e, True) for e in past[:6]) + "</details>")
    return f"<div class='rms'>{html}</div>"


def categories(ev: list, color_by: str) -> list[str]:
    key = "course" if color_by == "Course" else "type"
    seen = []
    for e in ev:
        if e[key] not in seen:
            seen.append(e[key])
    return seen


# Fixed defaults so a category keeps its colour when new events show up.
_TYPE_COLORS = {"Exam": "Pink", "Quiz": "Lavender", "Lab": "Mint", "Homework": "Peach", "Project": "Peach",
                "Paper": "Lavender", "Other": "Cloud", "Focus block": "Sky", "Pip check-in": "Butter",
                "Pip's plans": "Butter"}
_COURSE_CYCLE = ["Sky", "Pink", "Mint", "Lavender", "Peach", "Cloud"]


def default_color(cat: str) -> str:
    if cat in _TYPE_COLORS:
        return _TYPE_COLORS[cat]
    return _COURSE_CYCLE[zlib.crc32(cat.encode()) % len(_COURSE_CYCLE)]


def color_of(e: dict, color_by: str, chosen: dict) -> str:
    if color_by == "Off":
        return EVENT_COLORS["Sky"]
    key = e["course"] if color_by == "Course" else e["type"]
    return EVENT_COLORS.get(chosen.get(key, "Sky"), EVENT_COLORS["Sky"])


# ---------------- widgets ----------------
def _chip(e, color_by, chosen, clock24, show_time=True):
    when = fmt_time(e["time"], clock24) if (show_time and e["time"]) else ("Due" if e["kind"] == "Deadline" else "")
    tip = escape(f"{e['title']}\n{fmt_dt(e['time'], clock24) if e['time'] else fmt_date(e['day'], True)}\n{e['detail']}")
    return (f'<div class="ev" style="--ev:{color_of(e, color_by, chosen)}" title="{tip}">'
            f'{f"<b>{escape(when)}</b> " if when else ""}{escape(e["title"])}</div>')


def month_html(year: int, month: int, ev: list, color_by: str, chosen: dict, clock24: bool, today: date) -> str:
    by_day = {}
    for e in ev:
        by_day.setdefault(e["day"], []).append(e)
    cal = calendar.Calendar(firstweekday=6)  # Sunday first, like most US planners
    head = "".join(f"<div class='mh'>{d}</div>" for d in ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"])
    cells = []
    for d in cal.itermonthdates(year, month):
        items = by_day.get(d, [])
        cls = ["md"] + (["out"] if d.month != month else []) + (["today"] if d == today else []) + (["has"] if items else [])
        dots = "".join(f'<i style="background:{color_of(e, color_by, chosen)}"></i>' for e in items[:4])
        tip = ""
        if items:
            lines = "".join(f"<div>{_chip(e, color_by, chosen, clock24)}</div>" for e in items[:5])
            more = f"<div class='muted'>+{len(items) - 5} more</div>" if len(items) > 5 else ""
            tip = f"<div class='mtip'><div class='mtip-h'>{escape(fmt_date(d, True))}</div>{lines}{more}</div>"
        cells.append(f"<div class='{' '.join(cls)}' tabindex='0'><span>{d.day}</span><div class='dots'>{dots}</div>{tip}</div>")
    title = f"{calendar.month_name[month]} {year}"
    return f"<div class='mini-cal'><div class='mc-title'>{title}</div><div class='mc-grid'>{head}{''.join(cells)}</div></div>"


def week_html(start: date, ev: list, color_by: str, chosen: dict, clock24: bool, today: date) -> str:
    cols = []
    for i in range(7):
        d = start + timedelta(days=i)
        items = [e for e in ev if e["day"] == d]
        chips = "".join(_chip(e, color_by, chosen, clock24) for e in items[:6]) or "<div class='free'>free</div>"
        if len(items) > 6:
            rest = escape("\n".join(f"{fmt_time(e['time'], clock24)} {e['title']}".strip() for e in items[6:]))
            chips += f"<div class='more' title='{rest}'>+{len(items) - 6} more</div>"
        cls = "wd today" if d == today else "wd"
        cols.append(f"<div class='{cls}'><div class='wd-h'><span>{d:%a}</span><b>{d.day}</b></div>{chips}</div>")
    end = start + timedelta(days=6)
    rng = f"{start:%b} {start.day} to {end:%b} {end.day}, {end.year}"
    return f"<div class='week-cal'><div class='wk-title'>{rng}</div><div class='wk-scroll'><div class='wk-grid'>{''.join(cols)}</div></div></div>"


def legend_html(cats: list, chosen: dict) -> str:
    return "<div class='legend'>" + "".join(
        f"<span class='lg'><i style='background:{EVENT_COLORS.get(chosen.get(c, 'Sky'), EVENT_COLORS['Sky'])}'></i>{escape(c)}</span>"
        for c in cats) + "</div>"
