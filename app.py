"""Pip: your tiny study buddy (pip-tidalbyte-2026). Run with:  streamlit run app.py"""
import json
import threading
import time
import zlib
from datetime import date, datetime, timedelta
from html import escape
from pathlib import Path

import streamlit as st

from core import agent, config, feedback, mascot, syllabus, tools, week
from core.nemotron import Nemotron, NemotronError
from core.science import DISCIPLINES, LEVERS, STRATEGIES
from core.transcribe import transcribe
from core.ui import (AMBIENT_SOUNDS, HEART_SVG, footer_html, LEVER_COLORS, PLAN_COLORS, ambient_html, deadlines_html, jam_html,
                     move_html, plan_html, playbook_html, card, css, fx_html, lever_bar, table_html, thinking_html,
                     title_html, waves_html)

st.set_page_config(page_title="Pip · your tiny study buddy", page_icon=str(Path(__file__).parent / "assets" / "pip.png"),
                   layout="wide")
ss = st.session_state
for k, v in {"dark": False, "easy_read": False, "still": False, "sound": True, "volume": 60, "haptics": True,
             "ambient": "Off", "amb_volume": 40, "clock": "12-hour", "color_by": "Type", "week_off": 0,
             "month_off": 0, "muted": False, "ev_colors": {}}.items():
    ss.setdefault(k, v)
st.markdown(css(ss.easy_read, ss.still, ss.dark), unsafe_allow_html=True)
st.markdown(waves_html(ss.dark, big=ss.ambient == "Ocean"), unsafe_allow_html=True)
if ss.ambient and ss.ambient != "Off":
    st.markdown(ambient_html(ss.ambient), unsafe_allow_html=True)

ss.setdefault("deadlines", [])
ss.setdefault("result", None)
ss.setdefault("text", "")
ss.setdefault("mood", "happy")
ss.setdefault("pip_says", "Hi! I'm Pip, a tiny snow fairy bird. Tell me what you're stuck on. No judgment, ever.")


@st.cache_resource
def get_client():
    return Nemotron()


client = get_client()


BUBBLE = {}  # Pip's speech-bubble placeholder, so run_agent can show "Pipping..." in it


def pip(mood, says, size=170):
    c1, c2 = st.columns([1, 2.4])
    with c1:
        st.markdown(f'<div class="pip-wrap">{mascot.svg(mood, size)}</div>', unsafe_allow_html=True)
    with c2:
        BUBBLE["box"] = st.empty()
        BUBBLE["box"].markdown(f'<div class="bubble">{escape(says)}</div>', unsafe_allow_html=True)


def run_agent(text) -> bool:
    """Run the agent in a worker thread so Pip's bubble can show a live stopwatch."""
    client.calls.clear()
    focus_time, deadlines, box = ss.get("focus_time") or "", ss.deadlines, {}

    def work():
        try:
            box["result"] = agent.run(client, text, "", deadlines, focus_time)
        except Exception as e:  # noqa: BLE001 (shown to the user below)
            box["error"] = e

    bubble = BUBBLE.get("box") or st.empty()
    worker = threading.Thread(target=work, daemon=True)
    t0, shown = time.time(), -1
    worker.start()
    while worker.is_alive():
        secs = int(time.time() - t0)
        if secs != shown:
            bubble.markdown(thinking_html(secs), unsafe_allow_html=True)
            shown = secs
        worker.join(0.1)
    if "error" in box:  # keep the error on screen after rerun
        ss.error = f"Pip couldn't reach Nemotron: {box['error']}"
        return False
    ss.result = box["result"]
    ss.run_id = ss.get("run_id", 0) + 1  # fresh checklist for each new plan
    r = ss.result
    ss.mood = r["mood"]
    ss.pip_says = r["message"] if not r["safe"] else r["diagnosis"]["buddy_message"]
    return True


# ---------------- Sidebar: about you ----------------
with st.sidebar:
    st.markdown(f'<div class="brand">{mascot.svg("happy", 54)}<div><div class="brand-name">Pip<span class="dot">.</span></div>'
                '</div></div>', unsafe_allow_html=True)
    st.markdown("### About you")
    st.text_input("Your name", key="name", placeholder="e.g. Sam")
    st.pills("When do you focus best?", ["Morning", "Afternoon", "Evening", "Late night"], key="focus_time",
             help="Pip puts focus blocks and check-ins at the times that work for your brain.")
    st.markdown("### Your syllabi")
    files = st.file_uploader("Drop syllabus PDFs", type=["pdf"], accept_multiple_files=True)
    if files and st.button("Read my syllabi"):
        found = []
        for f in files:
            try:
                with st.spinner(f"Reading {f.name}..."):
                    out = syllabus.extract(client, f.getvalue(), f.name)
                for a in out.get("assignments", []):
                    a["course"] = out.get("course", f.name)
                    found.append(a)
            except Exception as e:
                st.error(f"{f.name}: {e}")
        ss.deadlines = found
        st.success(f"Found {len(found)} graded items")
    with st.popover("Settings", icon=":material/tune:", width="stretch"):
        st.markdown('<div class="set-h">Look and feel</div>', unsafe_allow_html=True)
        st.toggle("Dark mode", key="dark")
        st.toggle("Easier reading (bigger, more spacing)", key="easy_read")
        st.toggle("Stop animations", key="still")
        st.segmented_control("Time format", ["12-hour", "24-hour"], key="clock", required=True)
        st.markdown('<div class="set-h">Sound and haptics</div>', unsafe_allow_html=True)
        st.toggle("Click sounds", key="sound")
        st.toggle("Haptics (phones that support vibration)", key="haptics")
        st.markdown('<div class="set-h">Advanced</div>', unsafe_allow_html=True)
        if st.button("Test Nemotron connection", icon=":material/wifi_tethering:"):
            for label, m in [("Thinking (Super VL)", config.REASONING_MODEL), ("Acting (Lightning)", config.FAST_MODEL),
                             ("Safety", config.SAFETY_MODEL)]:
                with st.spinner(f"Pinging {label}..."):
                    ok, msg = client.ping(m)
                (st.success if ok else st.error)(f"{label}: {'works' if ok else 'failed'} ({msg})\n\n`{m}`")
    st.markdown("### Focus sounds")
    st.pills("Play something calm while you work", AMBIENT_SOUNDS, key="ambient", required=True)
    st.markdown("---")
    if client.demo:
        st.markdown('<span class="badge solid">demo mode</span> add NVIDIA_API_KEY to .env', unsafe_allow_html=True)
    else:
        st.markdown('<div class="nemo-wrap"><span class="badge nemo">Powered by NVIDIA Nemotron</span></div>',
                    unsafe_allow_html=True)
    # the science lives in a pop-up, tucked away (curious people can find it; it's not in the way)
    with st.container(key="about_links"):
        if st.button("Our story", icon=":material/favorite:", type="tertiary", key="story_btn", width="stretch"):
            ss.show_story = True
        if st.button("The science behind Pip", icon=":material/science:", type="tertiary", key="sci_btn", width="stretch"):
            ss.show_science = True

name = ss.get("name") or "friend"
st.markdown(title_html(name), unsafe_allow_html=True)
# volume button, fixed in the top-right corner (styled via its .st-key-vol_corner class)
with st.container(key="vol_corner"):
    vol_icon = (":material/volume_off:" if ss.muted or (not ss.sound and ss.ambient == "Off")
                else ":material/volume_up:")
    with st.popover("Sound", icon=vol_icon):
        st.toggle("Mute everything", key="muted")
        st.slider("Click sounds", 0, 100, key="volume", format="%d%%", disabled=ss.muted or not ss.sound)
        st.slider("Focus sounds", 0, 100, key="amb_volume", format="%d%%", disabled=ss.muted)
        st.caption(f"Playing: {ss.ambient}" if ss.ambient != "Off" else "Pick a focus sound in the sidebar.")
tab_check, tab_week = st.tabs(["Check in", "My week"])

# ---------------- Check in ----------------
with tab_check:
    pip(ss.mood, ss.pip_says)
    r = ss.result

    if ss.get("error"):
        st.error(ss.pop("error"))
    for w in (r or {}).get("warnings", []):
        st.warning(w)

    if r is None:
        if ss.pop("clear_text", False):
            ss.checkin_text = ""
        audio_in = getattr(st, "audio_input", None)
        if audio_in:
            audio = audio_in("Say it out loud (or type below)")
            if audio is not None and ss.get("last_audio") != hash(audio.getvalue()):
                ss.last_audio = hash(audio.getvalue())
                heard = transcribe(client, audio.getvalue())
                if heard:
                    ss.checkin_text = heard
                else:
                    st.caption("Voice needs PIP_ASR_MODEL set. Type it for now!")
        with st.form("checkin_form", border=False):
            st.text_area("What's going on? Be messy. Pip gets it.", key="checkin_text", height=110,
                         placeholder="ugh I have a lab report due Tuesday and I keep opening TikTok instead")
            st.markdown('<div class="hint">Press <kbd>Enter</kbd> to send. <kbd>Shift</kbd> + <kbd>Enter</kbd> '
                        'for a new line.</div>', unsafe_allow_html=True)
            send = st.form_submit_button("Talk to Pip")
        if send:
            text = ss.get("checkin_text", "").strip()
            if not text:
                st.warning("Tell Pip what's going on first!")
            else:
                ss.text = text
                if run_agent(text):
                    ss.clear_text = True
                st.rerun()

    elif not r["safe"]:
        st.markdown(card("You're not alone", r["message"].replace("**", "")), unsafe_allow_html=True)
        if st.button("Back"):
            ss.result, ss.mood, ss.pip_says = None, "happy", "I'm here whenever you want to talk."
            st.rerun()

    else:
        d, s = r["diagnosis"], r["strategy"]
        st.markdown(jam_html(d, LEVERS), unsafe_allow_html=True)
        st.markdown(move_html(s, r["strategy_reason"]), unsafe_allow_html=True)

        st.markdown("### Here's what I set up for you")
        st.markdown(f'<div class="say">{mascot.svg("cheer", 64)}<div class="bubble">{escape(r["reply"])}</div></div>',
                    unsafe_allow_html=True)
        clock24 = ss.clock == "24-hour"
        n = 0
        for i, res in enumerate(r["results"]):
            t = res.get("type")
            if t in PLAN_COLORS:
                n += 1
            if t == "first_step":
                st.markdown(plan_html(n, t, "Your first step", res["step"], f"{res['minutes']} min"), unsafe_allow_html=True)
            elif t == "calendar":
                when = week.fmt_dt(res["start_iso"], clock24) if res.get("start_iso") else res["start"]
                st.markdown(plan_html(n, t, "On your calendar", res["title"], f"{when} · {res['minutes']} min", res["note"]),
                            unsafe_allow_html=True)
                p = Path(res["ics_path"])
                if p.exists():
                    st.download_button("Add to my calendar (.ics)", p.read_bytes(), file_name=p.name,
                                       mime="text/calendar", key=f"ics{i}", icon=":material/event:")
            elif t == "checkin":
                st.markdown(plan_html(n, t, "Pip will check in", res["message"], week.fmt_dt(res["when"], clock24)),
                            unsafe_allow_html=True)
            elif t == "goal_link":
                st.markdown(plan_html(n, t, "Why this matters to you", res["connection"]),
                            unsafe_allow_html=True)
            elif "error" in res:
                st.caption(res["error"])

        # ---- Check in on the task: tick off what Pip set up, then say how it's going ----
        task = d.get("task") or "your task"
        clock24 = ss.clock == "24-hour"
        todo, todo_colors = [], []
        for res in r["results"]:
            if res.get("type") == "first_step":
                todo.append(f"{res['step']} ({res['minutes']} min)")
                todo_colors.append(PLAN_COLORS["first_step"])
            elif res.get("type") == "calendar":
                when = week.fmt_dt(res["start_iso"], clock24) if res.get("start_iso") else res["start"]
                todo.append(f"Do your focus block: {res['title']} ({when})")
                todo_colors.append(PLAN_COLORS["calendar"])
        if not any(res.get("type") == "first_step" for res in r["results"]):
            todo.insert(0, f"Try Pip's trick: {s['how']}")
            todo_colors.insert(0, LEVER_COLORS.get(s.get("lever"), "#B8D6FA"))
        with st.container(key="followup"):
            st.markdown(f"### Check in: {escape(task)}")
            st.caption("Tick off what you've done. Then tell Pip how it's going, so Pip learns what helps you.")
            rid = ss.get("run_id", 0)
            st.markdown("<style>" + "".join(
                f".st-key-todo_{rid}_{i} {{ border: 2px solid {c}; border-left: 7px solid {c}; border-radius: 14px; "
                f"padding: 6px 10px; background: color-mix(in srgb, {c} 22%, transparent); }}"
                for i, c in enumerate(todo_colors)) + "</style>", unsafe_allow_html=True)
            done = sum(bool(st.checkbox(t, key=f"todo_{rid}_{i}")) for i, t in enumerate(todo))
            pct = int(done / len(todo) * 100) if todo else 0
            st.markdown(f'<div class="fu-bar"><i style="width:{pct}%"></i></div>'
                        f'<div class="muted" style="font-size:.85em">{done} of {len(todo)} done</div>',
                        unsafe_allow_html=True)
            b1, b2, b3, b4 = st.columns(4)
            if b1.button("It's going well!", width="stretch", help="Pip's trick helped you get going", key="fu_good"):
                feedback.record(s["id"], True)
                ss.mood, ss.result, ss.text = "cheer", None, ""
                ss.pip_says = (f"You did it! {done} of {len(todo)} done on {task}. Starting is the hardest part. "
                               "So proud of you!" if done else f"Yay, you're moving on {task}! So proud of you!")
                st.rerun()
            if b2.button("Still stuck, new trick", width="stretch", help="This trick didn't help; Pip tries a different one",
                         key="fu_stuck"):
                feedback.record(s["id"], False)
                run_agent(ss.text)
                st.rerun()
            if b3.button("Remind me later", width="stretch", help="Pip checks in on this task in 30 minutes", key="fu_later"):
                when = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=30)
                tools.schedule_checkin(task, when.isoformat(timespec="minutes"), "Pip here! Ready to give it another go?")
                st.toast(f"Pip will check in on {task} at {week.fmt_time(when, clock24)}")
            if b4.button("Something else", width="stretch", help="Start a new check-in", key="fu_new"):
                ss.result, ss.mood, ss.text = None, "happy", ""
                ss.pip_says = "What's next on your mind?"
                st.rerun()

        with st.expander("Agent trace (how Nemotron did this)"):
            for step, detail in r["steps"]:
                st.markdown(f"**{step}**: {detail}")
            st.json({"diagnosis": d, "tool_calls": r["trace"], "model_calls (model, seconds)": r.get("model_calls")})

# ---------------- My week ----------------
with tab_week:
    clock24 = ss.clock == "24-hour"
    today = date.today()
    events = week.events(ss.deadlines)

    cats = week.categories(events, ss.color_by) if ss.color_by != "Off" else []
    # chosen colours live in ss.ev_colors so they survive switching Type <-> Course
    chosen = {c: ss.ev_colors.get(f"{ss.color_by}:{c}", week.default_color(c)) for c in cats}

    def _keep_color(name, widget_key):
        if ss.get(widget_key):
            ss.ev_colors[name] = ss[widget_key]

    left, right = st.columns([1.3, 1], gap="medium")
    with left:  # Pip's reminders: colour-coded like the calendar, with a live countdown
        st.markdown("### Pip's reminders")
        st.markdown(week.reminders_html(events, ss.color_by, chosen, clock24, datetime.now()), unsafe_allow_html=True)
    with right:
        with st.container(key="wk_tools"):
            t1, t2 = st.columns([1.15, 1.6], vertical_alignment="center")
            t2.segmented_control("Color code by", ["Type", "Course", "Off"], key="color_by", required=True,
                                 label_visibility="collapsed", help="Color code events by")
            with t1.popover("Colors", icon=":material/palette:", disabled=not cats):
                what = "course" if ss.color_by == "Course" else "kind of event"
                st.caption(f"Choose a color for each {what}.")
                with st.container(key="swatches"):
                    for c in cats:
                        name = f"{ss.color_by}:{c}"
                        wkey = f"pick_{zlib.crc32(name.encode())}"
                        st.pills(c, list(week.EVENT_COLORS), key=wkey, required=True,
                                 default=chosen[c], on_change=_keep_color, args=(name, wkey))
        m = (today.month - 1 + ss.month_off)
        y, mo = today.year + m // 12, m % 12 + 1
        st.markdown(week.month_html(y, mo, events, ss.color_by, chosen, clock24, today), unsafe_allow_html=True)
        n1, n2, n3 = st.columns([1, 1.4, 1])
        if n1.button("‹", key="m_prev", help="Previous month", width="stretch"):
            ss.month_off -= 1
            st.rerun()
        if n2.button("Today", key="m_today", width="stretch"):
            ss.month_off = ss.week_off = 0
            st.rerun()
        if n3.button("›", key="m_next", help="Next month", width="stretch"):
            ss.month_off += 1
            st.rerun()

    st.markdown("### This week")
    # the whole week, full width
    start = today - timedelta(days=(today.weekday() + 1) % 7) + timedelta(weeks=ss.week_off)
    st.markdown(week.week_html(start, events, ss.color_by, chosen, clock24, today), unsafe_allow_html=True)
    w1, w2, w3 = st.columns([1, 2.4, 1])
    if w1.button("‹ Last week", key="w_prev", width="stretch"):
        ss.week_off -= 1
        st.rerun()
    if w2.button("This week", key="w_today"):
        ss.week_off = 0
        st.rerun()
    if w3.button("Next week ›", key="w_next", width="stretch"):
        ss.week_off += 1
        st.rerun()
    if cats:
        st.markdown(week.legend_html(cats, chosen), unsafe_allow_html=True)
    if not events:
        st.caption("Your calendar is empty for now. Upload a syllabus in the sidebar, or check in with Pip "
                   "and Pip will add focus blocks and check-ins here.")

    st.markdown("### Coming up")
    if not ss.deadlines:
        st.markdown(card("No syllabi yet", "Upload your syllabus PDFs in the sidebar and Pip will find every deadline."),
                    unsafe_allow_html=True)
    else:
        rows = []
        for a in ss.deadlines:
            d_ = week.to_date(a.get("due"))
            typ = (a.get("type") or "other").title()
            rows.append({"title": a.get("title") or "Due", "course": a.get("course") or "", "type": typ,
                         "days": (d_ - today).days if d_ else None, "weight": a.get("weight_pct"),
                         "due": (week.fmt_date(d_) + (f" at {week.fmt_time(a['due_time'], clock24)}" if a.get("due_time") else ""))
                         if d_ else "No date",
                         "color": week.color_of({"type": typ, "course": a.get("course") or "Course"}, ss.color_by, chosen),
                         "_t": a.get("due_time") or "99:99"})
        # soonest first (same day: earlier time first); undated items go last
        rows.sort(key=lambda x: (x["days"] is None, x["days"] if x["days"] is not None else 0, x["_t"]))
        past = [x for x in rows if x["days"] is not None and x["days"] < 0]
        upcoming = [x for x in rows if x["days"] is None or x["days"] >= 0]
        ss.setdefault("dl_show_past", False)
        ss.setdefault("dl_limit", 6)

        if past:  # toggle sits ABOVE the list
            label = ("Hide past assignments" if ss.dl_show_past else f"Show past assignments ({len(past)})")
            if st.button(label, key="dl_past", type="tertiary",
                         icon=":material/expand_less:" if not ss.dl_show_past else ":material/expand_more:"):
                ss.dl_show_past = not ss.dl_show_past
                st.rerun()
            if ss.dl_show_past:
                st.markdown(deadlines_html(past), unsafe_allow_html=True)

        if upcoming:
            st.markdown(deadlines_html(upcoming[:ss.dl_limit]), unsafe_allow_html=True)
        else:
            st.markdown(card("Nothing due from today on", "You're all caught up. Pip is proud of you!"), unsafe_allow_html=True)

        more = len(upcoming) - ss.dl_limit
        b1, b2 = st.columns(2)
        if more > 0 and b1.button(f"Show future assignments ({more} more)", key="dl_more", type="tertiary",
                                  icon=":material/expand_more:"):
            ss.dl_limit += 6
            st.rerun()
        if ss.dl_limit > 6 and b2.button("Show fewer", key="dl_less", type="tertiary", icon=":material/expand_less:"):
            ss.dl_limit = 6
            st.rerun()

    st.markdown("### What helps you start")
    stats = feedback.stats()
    if stats:
        nxt = {k: feedback.choose(k)[0]["name"] for k in LEVERS if any(s["lever"] == k for s in stats)}
        st.markdown(playbook_html(stats, LEVERS, nxt), unsafe_allow_html=True)
        if st.button("Start fresh", help="Forget which tricks worked and start learning again"):
            feedback.reset()
            st.rerun()
    else:
        st.markdown(card("Pip is still learning about you",
                         "<p>After Pip gives you a plan, check in on the task and tell Pip how it went. Pip remembers which tricks help "
                         "<b>you</b>, and picks better ones next time.</p>"), unsafe_allow_html=True)

# ---------------- The science (a pop-up, opened from the sidebar) ----------------
@st.dialog("The science behind Pip", width="large")
def science_dialog():
    st.markdown("### One formula, four levers")
    st.markdown(card("Temporal Motivation Theory (Steel, 2007)",
                     f'<div class="formula">Motivation = <span class="fx" style="--lc:{LEVER_COLORS["expectancy"]}">Expectancy</span> × '
                     f'<span class="fx" style="--lc:{LEVER_COLORS["value"]}">Value</span> ÷ (<span class="fx" style="--lc:{LEVER_COLORS["impulsiveness"]}">'
                     f'Impulsiveness</span> × <span class="fx" style="--lc:{LEVER_COLORS["delay"]}">Delay</span>)</div><p class="muted" style="text-align:center">'
                     'Pip figures out which lever is jamming, then uses a fix from the field that studies it.</p>'),
                 unsafe_allow_html=True)
    cols = st.columns(4)
    for col, (k, v) in zip(cols, LEVERS.items()):
        with col:
            st.markdown(mascot.svg(v["buddy_mood"], 110), unsafe_allow_html=True)
            fixes = ", ".join(s["name"] for s in STRATEGIES if s["lever"] == k)
            st.markdown(f"<div class='card lv-card' style='--lc:{LEVER_COLORS[k]}'><h4>{escape(v['short'])}</h4>"
                        f"<p><b>{escape(v['label'])}</b></p><p>{escape(v['explain'])}</p>"
                        f"<p class='muted'>Fixes: {escape(fixes)}</p></div>", unsafe_allow_html=True)

    st.markdown("### Seven fields, one buddy")
    cols = st.columns(2)
    for i, (field, info) in enumerate(DISCIPLINES.items()):
        with cols[i % 2]:
            fc = list(week.EVENT_COLORS.values())[i % 6]
            st.markdown(f"<div class='card fd-card' style='--lc:{fc}'><h4>{escape(field)}</h4><p>{escape(info['what'])}</p>"
                        f"<p class='muted'><b>In the app:</b> {escape(info['where'])}</p>"
                        f"<p class='muted' style='font-size:.8em;opacity:.6'>{escape(info['cite'])}</p></div>",
                        unsafe_allow_html=True)

    ev = Path(__file__).parent / "eval" / "results.json"
    if ev.exists():  # Pip's report card: Nemotron's output quality, measured (python eval/run_eval.py)
        e = json.loads(ev.read_text())["summary"]
        tiles = [("Right main jam", e["diagnosis"]["top1"], "hand-labelled check-ins", LEVER_COLORS["expectancy"]),
                 ("Distress routed to help", e["safety"]["distress_caught"], f"false alarms: {e['safety']['false_alarms']}", LEVER_COLORS["value"]),
                 ("Model called the right tool", e["acting"]["model_called_required_tool"], "end-to-end agent runs", LEVER_COLORS["impulsiveness"]),
                 ("Valid structured output", e["diagnosis"]["valid_json"], f"median {e['diagnosis']['median_secs']}s per diagnosis", LEVER_COLORS["delay"])]
        st.markdown("### Pip's report card")
        st.markdown("<div class='report'>" + "".join(
            f"<div class='rc' style='--lc:{c}'><b>{escape(v)}</b><span>{escape(t)}</span><small>{escape(sub)}</small></div>"
            for t, v, sub, c in tiles) + f"</div><p class='muted' style='font-size:.8em'>Measured on {e['date'][:10]} with "
            f"<code>python eval/run_eval.py</code> against the live Nemotron models.</p>", unsafe_allow_html=True)

    st.markdown("### Built by ADHD brains, for ADHD brains")
    st.markdown(card("Design choices", "<ul>"
                     "<li><b>One thing at a time:</b> one diagnosis, one move, one tiny step. No overwhelming task lists.</li>"
                     "<li><b>Zero shame:</b> Pip never says 'just focus'. Being stuck is a jammed lever, not a character flaw.</li>"
                     "<li><b>Time made visible:</b> days left, real countdowns, calendar blocks with alarms.</li>"
                     "<li><b>Low-friction input:</b> type something messy or just talk.</li>"
                     "<li><b>Calm palette:</b> four soft blues, a touch of butter yellow and white, light or dark mode, round buttons, slow waves you can switch off.</li>"
                     "<li><b>Dyslexia-friendly type:</b> Lexend font, roomy spacing, no italics or all-caps, AAA contrast, and an easier-reading mode.</li>"
                     "</ul><p class='muted'>Pip is a study tool, not a medical treatment for ADHD.</p>"),
                 unsafe_allow_html=True)


if ss.pop("show_science", False):
    science_dialog()


# ---------------- Our story (mission statement, from the founders) ----------------
STORY = [
    "Hi! We're Ava and Rana, the two ADHD college students behind Pip.",
    "We care, we put in the effort, and we still get stuck trying to start the \"easy\" or \"basic\" tasks. "
    "Attention has become one of the most valuable things in the world, and so much of modern life, especially "
    "endless short-form content, is built to take it from us. We don't think we're the only ones feeling that pull.",
    "So we made Pip to pull back. Pip helps you figure out why you're stuck, take one tiny step, and put your most "
    "valuable resources, your attention, time and energy, toward the life you want. Our hope is that it takes a "
    "little weight off your day and supports your mental health along the way.",
    "And why a bird? Pip is a shima enaga, a tiny long-tailed tit from Hokkaido, Japan, often called a \"snow fairy.\" "
    "They're a symbol of purity and serenity. We hope Pip brings you a little serenity, too.",
]


@st.dialog("Our story", width="large")
def story_dialog():
    paras = "".join(f"<p>{escape(t)}</p>" for t in STORY[1:])
    st.markdown(f"<div class='story'>{mascot.svg('happy', 150)}<div><p><b>{escape(STORY[0])}</b></p>"
                f"<div class='mission'>Our mission: help every distracted brain take back its attention, "
                f"one tiny step at a time.</div>{paras}<p class='sign'>With love, Ava and Rana {HEART_SVG}</p></div></div>",
                unsafe_allow_html=True)


if ss.pop("show_story", False):
    story_dialog()

st.markdown(footer_html(), unsafe_allow_html=True)

# Sounds, haptics, toggle sparkles and Enter-to-send (see core/fx.js)
st.html(fx_html(ss.sound and not ss.muted, ss.volume, ss.haptics, ss.still, ss.dark,
                "Off" if ss.muted else ss.ambient, ss.amb_volume), unsafe_allow_javascript=True)
