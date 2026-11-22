"""Syllabus PDF -> list of assignments with due dates and grade weights.

Stretch goal: swap `pdf_text` for Nemotron Parse to handle tables and
scanned syllabi better (and name it in the Devpost)."""
import io
from datetime import date

from pypdf import PdfReader

from . import config
from .nemotron import Nemotron

SYSTEM = """You extract graded work from course syllabi.
Return ONLY JSON: {"course": str, "assignments": [{"title": str, "due": "YYYY-MM-DD" or null,
"due_time": "HH:MM" (24-hour) or null, "weight_pct": number or null,
"type": "exam|project|homework|lab|quiz|paper|other"}]}
Rules: include only graded items. Use the syllabus's year; if no year is given assume %d.
Never invent dates or weights; use null if unknown."""


def pdf_text(data: bytes, max_chars=40000) -> str:
    reader = PdfReader(io.BytesIO(data))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    return text[:max_chars]


def extract(client: Nemotron, data: bytes, filename="syllabus.pdf") -> dict:
    if client.demo:
        return {"course": filename.rsplit(".", 1)[0], "assignments": [
            {"title": "Lab Report 3", "due": "2026-11-25", "weight_pct": 8, "type": "lab"},
            {"title": "Problem Set 9", "due": "2026-11-24", "weight_pct": 3, "type": "homework"},
            {"title": "Final Project", "due": "2026-12-08", "weight_pct": 25, "type": "project"},
        ]}
    text = pdf_text(data)
    # Thinking off: a long syllabus made the hidden reasoning eat the whole token budget,
    # leaving an empty answer ("model did not return valid JSON"). Off = ~2s instead of ~20s.
    out = client.chat_json(SYSTEM % date.today().year, text, config.REASONING_MODEL, max_tokens=6000, think=False)
    if not isinstance(out, dict):
        out = {"course": filename.rsplit(".", 1)[0], "assignments": out if isinstance(out, list) else []}
    out.setdefault("assignments", [])
    return out
