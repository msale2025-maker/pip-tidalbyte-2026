"""Step 1 of the agent: Nemotron scores the four Temporal Motivation Theory
levers for this check-in and says which one is the bottleneck."""
from datetime import date

from . import config
from .nemotron import Nemotron
from .science import LEVERS

SYSTEM = """You are the reasoning core of Lever, a kind study buddy for students,
many of whom have ADHD. You diagnose WHY a student is stuck using Temporal Motivation Theory
(Steel, 2007): Motivation = (Expectancy x Value) / (Impulsiveness x Delay).

Score how much each lever is CAUSING the stall, 1 (not a problem) to 5 (main problem):
- expectancy: they doubt they can do it / task feels huge or unclear
- value: task feels boring, pointless, disconnected from their goals
- impulsiveness: distraction, phone, can't stay on task once started
- delay: deadline feels far away / not real yet / time blindness

Ground every score in the student's actual words or the deadline data.
Do not diagnose medical conditions. Do not shame. Today is {today}.

"evidence" = Pip's INSIGHT for each lever, written TO the student ("you"), one sentence, max 28 words.
Don't just restate what they said or state the obvious ("you said stuck, so you're struggling" is useless).
Name the specific, non-obvious pattern behind their words and what it really means. Good examples:
- "Being 'stuck' halfway through usually means the next sentence isn't defined yet, not that you can't write it."
- "Your deadline is tomorrow, so urgency is already doing its job here; it's not what's slowing you."
- "The phone wins because it pays off in 2 seconds and the essay pays off in 2 weeks."
"tips" = one tiny, concrete thing to try for each lever (max 12 words, starts with a verb).

Return ONLY JSON:
{{"task": str, "scores": {{"expectancy": int, "value": int, "impulsiveness": int, "delay": int}},
 "evidence": {{"expectancy": str, "value": str, "impulsiveness": str, "delay": str}},
 "tips": {{"expectancy": str, "value": str, "impulsiveness": str, "delay": str}},
 "primary_lever": "expectancy|value|impulsiveness|delay",
 "confidence": float 0-1,
 "buddy_message": "1-2 warm, casual sentences from Pip validating the feeling (no advice yet)"}}"""


def _clean(d: dict, text: str) -> dict:
    scores = d.get("scores") or {}
    clean = {}
    for k in LEVERS:
        try:
            clean[k] = max(1, min(5, int(round(float(scores.get(k, 1))))))
        except (TypeError, ValueError):
            clean[k] = 1
    d["scores"] = clean
    if d.get("primary_lever") not in LEVERS:
        d["primary_lever"] = max(clean, key=clean.get)
    d.setdefault("evidence", {})
    if not isinstance(d.get("tips"), dict):
        d["tips"] = {}
    d.setdefault("task", text[:60])
    d.setdefault("buddy_message", "Oof, I hear you. Let's figure this out together.")
    try:
        d["confidence"] = float(d.get("confidence", 0.6))
    except (TypeError, ValueError):
        d["confidence"] = 0.6
    return d


def _demo(text: str) -> dict:
    t = text.lower()
    s = {"expectancy": 1, "value": 1, "impulsiveness": 1, "delay": 1}
    kw = {
        "expectancy": ["can't", "cant", "hard", "huge", "don't know how", "overwhelm", "stuck", "confus"],
        "value": ["boring", "pointless", "why", "don't care", "dont care", "useless", "hate"],
        "impulsiveness": ["phone", "tiktok", "youtube", "distract", "scroll", "game", "focus"],
        "delay": ["later", "next week", "plenty of time", "tomorrow", "far", "due in"],
    }
    for k, words in kw.items():
        s[k] += min(4, 2 * sum(w in t for w in words))
    lever = max(s, key=s.get)
    return {
        "task": text.split(".")[0][:60],
        "scores": s,
        "evidence": {k: ("keywords matched (demo mode)" if s[k] > 1 else "not mentioned") for k in s},
        "tips": {"expectancy": "Write just the first sentence, badly.", "value": "Name one way this helps future you.",
                 "impulsiveness": "Put your phone in another room for 10 minutes.",
                 "delay": "Set a mini-deadline for tonight."},
        "primary_lever": lever,
        "confidence": 0.5,
        "buddy_message": "Ugh, that's such a real feeling. You're not lazy. Something's just jamming the gears. Let's find it.",
    }


def diagnose(client: Nemotron, text: str, goal: str = "", deadlines: list | None = None) -> dict:
    if client.demo:
        return _clean(_demo(text), text)
    ctx = f"Student check-in: \"{text}\"\n" + (f"Student's personal goal: {goal}\n" if goal else "")
    if deadlines:
        ctx += "Upcoming graded work:\n" + "\n".join(
            f"- {a.get('title')} due {a.get('due')} ({a.get('weight_pct')}% of grade)" for a in deadlines[:15])
    d = client.chat_json(SYSTEM.format(today=date.today().isoformat()), ctx, config.REASONING_MODEL, max_tokens=4000)
    return _clean(d, text)
