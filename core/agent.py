"""The agent loop: safety -> diagnose -> pick strategy (from feedback) ->
Nemotron calls tools to actually do the work -> return a trace for the UI."""
import json
from datetime import datetime, timedelta

from . import config, feedback, safety, tools
from .diagnose import diagnose
from .nemotron import _THINK, Nemotron, NemotronError
from .science import LEVERS

ACT_SYSTEM = """You are Pip, a cute, warm study buddy for a student (often ADHD).
You've already diagnosed the problem. Now DO the work using tools; don't just give advice.
Strategy to apply: {name}: {how}
You MUST call `{tool}`. You may call one more tool if it clearly helps.
Keep every text short, concrete, and kind. Current local time: {now}.
Check-in messages are tiny nudges: max 12 words, warm, direct, no time math (the app shows the countdown).
Times must be in the future, format YYYY-MM-DDTHH:MM.
If best_focus_time is given, put focus blocks / check-ins in that part of the day when it's still ahead
(Morning 8-12, Afternoon 12-17, Evening 17-21, Late night 21-24); otherwise pick something soon.
If there is no personal goal, link_to_goal should use something the student clearly cares about from their words.
After tools run, reply with ONE short sentence (max 25 words) telling the student what you set up."""


def _fallback_args(tool, task, goal, strategy):
    soon = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M")
    return {
        "make_first_step": {"task": task, "step": f"Open {task} and write just the title and 3 bullet points of what it needs.", "minutes": 10},
        "create_calendar_block": {"title": f"{strategy['name']}: {task}", "start": soon, "minutes": 25,
                                  "note": strategy["how"]},
        "schedule_checkin": {"task": task, "when": soon, "message": "Pip here! Just 10 minutes. You've got this."},
        "link_to_goal": {"task": task, "goal": goal or "what you care about",
                         "connection": f"Every piece of {task} is practice for {goal or 'where you want to go'}."},
    }[tool]


def _run_tool(name, args):
    fn = tools.REGISTRY.get(name)
    if not fn:
        return {"error": f"unknown tool {name}"}
    try:
        return fn(**args)
    except TypeError as e:  # model sent bad args
        return {"error": f"bad args for {name}: {e}"}


def act(client: Nemotron, diag, strategy, goal, deadlines, focus_time=""):
    task = diag.get("task", "your task")
    trace, results = [], []
    if client.demo:
        r = _run_tool(strategy["tool"], _fallback_args(strategy["tool"], task, goal, strategy))
        return [r], [{"tool": strategy["tool"], "args": "demo defaults", "result": r}], \
            "Okay! I set something small up for you. Let's go together."

    messages = [
        {"role": "system", "content": ACT_SYSTEM.format(
            now=datetime.now().strftime("%Y-%m-%dT%H:%M (%A)"), **strategy)},
        {"role": "user", "content": json.dumps({
            "task": task, "goal": goal or None, "best_focus_time": focus_time or None, "diagnosis": diag["scores"], "evidence": diag.get("evidence"),
            "deadlines": (deadlines or [])[:10]})},
    ]
    final_text = ""
    for _ in range(3):
        try:
            msg = client.chat(messages, config.FAST_MODEL, tools=tools.SCHEMAS, temperature=0.4)
        except NemotronError as e:
            trace.append({"tool": "(fast model error)", "args": "", "result": {"error": str(e)}})
            break
        calls = getattr(msg, "tool_calls", None) or []
        if not calls:
            final_text = msg.content or ""
            break
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
            {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
            for c in calls]})
        for c in calls:
            try:
                args = json.loads(c.function.arguments or "{}")
            except json.JSONDecodeError:
                args = _fallback_args(c.function.name, task, goal, strategy) if c.function.name in tools.REGISTRY else {}
            r = _run_tool(c.function.name, args)
            results.append(r)
            trace.append({"tool": c.function.name, "args": args, "result": r})
            messages.append({"role": "tool", "tool_call_id": c.id, "content": json.dumps(r)})

    # Guarantee the required action happened, even if the model skipped it.
    if not any(t["tool"] == strategy["tool"] and "error" not in t["result"] for t in trace):
        r = _run_tool(strategy["tool"], _fallback_args(strategy["tool"], task, goal, strategy))
        results.append(r)
        trace.append({"tool": strategy["tool"], "args": "fallback (model skipped tool)", "result": r})
    return results, trace, _THINK.sub("", final_text).strip() or "All set. One tiny step at a time!"


def run(client: Nemotron, text: str, goal: str = "", deadlines: list | None = None, focus_time: str = "") -> dict:
    out = {"input": text, "steps": []}
    s = safety.check(client, text)
    out["steps"].append(("Safety check", s.get("source")))
    if not s["safe"]:
        out.update(safe=False, message=s["message"], mood="hug")
        return out

    out["warnings"] = []
    try:
        diag = diagnose(client, text, goal, deadlines)
    except NemotronError as e:
        from .diagnose import _clean, _demo
        diag = _clean(_demo(text), text)
        out["warnings"].append(f"Diagnosis model failed, used keyword backup instead. {e}")
    out["steps"].append(("Diagnosis", f"primary lever = {diag['primary_lever']}"))
    strategy, why = feedback.choose(diag["primary_lever"])
    out["steps"].append(("Strategy pick", why))
    results, trace, reply = act(client, diag, strategy, goal, deadlines, focus_time)
    out["warnings"] += [t["result"]["error"] for t in trace if t["tool"] == "(fast model error)"]
    out["steps"].append(("Actions", f"{len(trace)} tool call(s)"))
    out.update(safe=True, diagnosis=diag, strategy=strategy, strategy_reason=why,
               results=results, trace=trace, reply=reply,
               mood=LEVERS[diag["primary_lever"]]["buddy_mood"],
               model_calls=list(client.calls))
    return out
