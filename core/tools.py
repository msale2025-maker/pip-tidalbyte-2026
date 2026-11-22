"""Tools the agent can call. Each returns a JSON-able dict the UI can show."""
import json
import uuid
from datetime import datetime, timedelta

from . import config

CHECKINS = config.DATA_DIR / "checkins.json"


def _parse_time(s: str | None) -> datetime:
    if s:
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(s[:19], fmt)
            except ValueError:
                continue
    # default: next half hour
    now = datetime.now().replace(second=0, microsecond=0)
    return now + timedelta(minutes=30 - now.minute % 30)


def make_first_step(task: str, step: str, minutes: int = 10) -> dict:
    minutes = max(2, min(int(minutes or 10), 25))
    return {"type": "first_step", "task": task, "step": step, "minutes": minutes}


def create_calendar_block(title: str, start: str | None = None, minutes: int = 25, note: str = "") -> dict:
    dt = _parse_time(start)
    end = dt + timedelta(minutes=int(minutes or 25))
    fmt = "%Y%m%dT%H%M%S"
    ics = "\r\n".join([
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Pip//pip-tidalbyte-2026//EN",
        "BEGIN:VEVENT", f"UID:{uuid.uuid4()}@pip-tidalbyte-2026",
        f"DTSTAMP:{datetime.now().strftime(fmt)}",
        f"DTSTART:{dt.strftime(fmt)}", f"DTEND:{end.strftime(fmt)}",
        f"SUMMARY:{title}", f"DESCRIPTION:{note.replace(chr(10), ' ')}",
        "BEGIN:VALARM", "TRIGGER:-PT5M", "ACTION:DISPLAY", "DESCRIPTION:Pip says: it's time!", "END:VALARM",
        "END:VEVENT", "END:VCALENDAR", "",
    ])
    path = config.DATA_DIR / f"block_{dt.strftime('%Y%m%d_%H%M')}.ics"
    path.write_text(ics)
    return {"type": "calendar", "title": title, "start": dt.strftime("%a %b %d, %I:%M %p"),
            "start_iso": dt.isoformat(timespec="minutes"),
            "minutes": int(minutes or 25), "note": note, "ics_path": str(path)}


def schedule_checkin(task: str, when: str | None = None, message: str = "") -> dict:
    dt = _parse_time(when)
    try:
        items = json.loads(CHECKINS.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        items = []
    item = {"task": task, "when": dt.isoformat(timespec="minutes"), "message": message}
    items.append(item)
    CHECKINS.write_text(json.dumps(items, indent=2))
    return {"type": "checkin", **item, "pretty": dt.strftime("%a %I:%M %p")}


def link_to_goal(task: str, goal: str, connection: str) -> dict:
    return {"type": "goal_link", "task": task, "goal": goal, "connection": connection}


def list_checkins() -> list:
    try:
        return json.loads(CHECKINS.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return []


REGISTRY = {
    "make_first_step": make_first_step,
    "create_calendar_block": create_calendar_block,
    "schedule_checkin": schedule_checkin,
    "link_to_goal": link_to_goal,
}

SCHEMAS = [
    {"type": "function", "function": {
        "name": "make_first_step",
        "description": "Write ONE concrete, physical first step the student can finish in a few minutes.",
        "parameters": {"type": "object", "properties": {
            "task": {"type": "string"},
            "step": {"type": "string", "description": "Imperative, specific, e.g. 'Open the lab doc and write the title + 3 section headers'"},
            "minutes": {"type": "integer", "description": "2-25"}},
            "required": ["task", "step"]}}},
    {"type": "function", "function": {
        "name": "create_calendar_block",
        "description": "Put a focused work block (or a personal mini-deadline) on the student's calendar.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "start": {"type": "string", "description": "Local time, format YYYY-MM-DDTHH:MM"},
            "minutes": {"type": "integer"},
            "note": {"type": "string", "description": "The if-then plan / what to do in the block"}},
            "required": ["title", "start"]}}},
    {"type": "function", "function": {
        "name": "schedule_checkin",
        "description": "Schedule Pip to check in on the student later (body doubling / countdown).",
        "parameters": {"type": "object", "properties": {
            "task": {"type": "string"},
            "when": {"type": "string", "description": "Local time, format YYYY-MM-DDTHH:MM"},
            "message": {"type": "string", "description": "Pip's nudge, MAX 12 words, warm and direct. Don't restate times or deadlines (the app shows a countdown). Examples: 'Pip here! 10 minutes in. Still going?' / 'Quick check: did the first step happen?'"}},
            "required": ["task", "when", "message"]}}},
    {"type": "function", "function": {
        "name": "link_to_goal",
        "description": "Explain in 1-2 sentences how this task connects to the student's personal goal.",
        "parameters": {"type": "object", "properties": {
            "task": {"type": "string"}, "goal": {"type": "string"},
            "connection": {"type": "string"}},
            "required": ["task", "goal", "connection"]}}},
]
