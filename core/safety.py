"""Runs before every response. If a check-in sounds like real distress,
Pip stops coaching and points to people who can help."""
import re

from . import config
from .nemotron import Nemotron, extract_json

# Fast local pre-filter so the safety net works even if the API is down.
_CRISIS = re.compile(
    r"\b(kill myself|suicid\w*|end it all|want to die|don'?t want to (be here|live)|"
    r"hurt myself|self[- ]harm|no reason to live|better off without me)\b", re.I)

SUPPORT_MESSAGE = (
    "Hey, I'm really glad you told me. This sounds bigger than homework, and you deserve "
    "a real person right now, not a study plan. You can call or text **988** (Suicide & "
    "Crisis Lifeline, 24/7), or reach your campus counseling center. If you're in "
    "danger right now, call **911**. Homework can wait. You matter more. 💙"
)


def check(client: Nemotron, text: str) -> dict:
    if _CRISIS.search(text or ""):
        return {"safe": False, "source": "local filter", "message": SUPPORT_MESSAGE}
    if client.demo:
        return {"safe": True, "source": "demo"}
    try:
        msg = client.chat(
            [{"role": "user", "content": text}], config.SAFETY_MODEL, temperature=0, max_tokens=120)
        raw = msg.content or ""
        try:
            verdict = str(extract_json(raw).get("User Safety", "safe")).lower()
        except Exception:
            verdict = "unsafe" if "unsafe" in raw.lower() else "safe"
        if verdict == "unsafe":
            return {"safe": False, "source": config.SAFETY_MODEL, "message": SUPPORT_MESSAGE}
        return {"safe": True, "source": config.SAFETY_MODEL}
    except Exception as e:
        # Fail open for ordinary text (local filter already ran), but log it.
        return {"safe": True, "source": f"safety model unavailable: {e}"}
