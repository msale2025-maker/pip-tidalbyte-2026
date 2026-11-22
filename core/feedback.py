"""The learning loop: remembers which strategies actually got this student
to start, and picks accordingly (a tiny Bayesian-ish bandit)."""
import json

from . import config
from .science import STRATEGIES, STRATEGY_BY_ID

PATH = config.DATA_DIR / "feedback.json"


def _load():
    try:
        return json.loads(PATH.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(d):
    PATH.write_text(json.dumps(d, indent=2))


def score(stats):
    return (stats.get("worked", 0) + 1) / (stats.get("tried", 0) + 2)


def choose(lever: str):
    """Return (strategy, reason) for this lever, based on past results."""
    data = _load()
    options = [s for s in STRATEGIES if s["lever"] == lever]
    ranked = sorted(options, key=lambda s: score(data.get(s["id"], {})), reverse=True)
    best = ranked[0]
    # Plain words on purpose: students don't know (or need) the word "lever".
    reason = "It's your first time trying this, so Pip picked the trick that helps the most people."
    for s in options:
        st = data.get(s["id"], {})
        if s is not best and st.get("tried"):
            reason = (f"'{s['name']}' helped {st.get('worked', 0)} out of {st['tried']} times for you, "
                      f"so let's try '{best['name']}' instead.")
            break
    bst = data.get(best["id"], {})
    if bst.get("tried"):
        w = bst.get("worked", 0)
        reason = (f"'{best['name']}' has helped you {w} out of {bst['tried']} times, so let's do it again."
                  if w else f"Nothing has clicked yet, so let's give '{best['name']}' another go. That's okay!")
    return best, reason


def record(strategy_id: str, worked: bool):
    data = _load()
    st = data.setdefault(strategy_id, {"tried": 0, "worked": 0})
    st["tried"] += 1
    st["worked"] += int(worked)
    _save(data)


def summary():
    data = _load()
    return [
        {"strategy": STRATEGY_BY_ID[k]["name"], "tried": v["tried"], "worked": v["worked"]}
        for k, v in data.items() if k in STRATEGY_BY_ID
    ]


def stats():
    """Per-strategy results with the strategy's details (for the 'What helps you start' view)."""
    data = _load()
    return [{**STRATEGY_BY_ID[k], "tried": v["tried"], "worked": v["worked"]}
            for k, v in data.items() if k in STRATEGY_BY_ID and v.get("tried")]


def reset():
    _save({})
