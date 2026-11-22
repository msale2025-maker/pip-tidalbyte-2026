# CLAUDE.md: Lever / Pip (tidalBYTE '26 hackathon)

Handoff context from a planning chat. Read this before changing anything.

## The event
- tidalBYTE '26 at Texas A&M (MSC). Prompt: apply AI/ML to real-world problems with cross-disciplinary impact.
- **Deadlines (Sat Nov 21, 2026, Central):** preliminary Devpost due **6:00 PM**, hacking ends / final submission **7:30 PM**, judging 8:00–9:30 PM (in person).
- Main rubric: Technicality, Ingenuity, Diversity (interdisciplinary), Applicability (real impact), Looks (pitch).
- Also entering **Best Use of NVIDIA Nemotron**: the model must do real agent work (not a thin chatbot). Judged on core model usage, technical execution, quality of AI output (prompting, grounding, eval, feedback loops), impact, creativity. Devpost needs a short explanation of what Nemotron does, why it matters and how we maximize it (draft is in README.md).
- Team of 2. **Both of us have ADHD.** That's the mission and the opening of the pitch.

## The product
**Pip** is a cute study buddy (a **shima enaga** bird) that diagnoses *why* a college student is procrastinating and does something about it.
- Core idea: **Temporal Motivation Theory** (Steel, 2007): Motivation = (Expectancy × Value) ÷ (Impulsiveness × Delay). Nemotron scores the 4 "levers" from the student's own words, picks a research-backed fix for the weakest lever, then *acts* with tools.
- Lever → buddy mood: expectancy→wobbly, value→shrug, impulsiveness→dizzy, delay→sleepy. Also happy, cheer, hug (safety).
- Feedback loop: "Did you start?" → records success/failure per strategy → next time picks differently (shows "X worked 0/1 for you, switching to Y"). This is the key demo moment.
- Safety: every check-in is screened first; real distress → 988 / campus counseling message instead of coaching. A local regex filter always runs, even if the safety model is down.

## Interdisciplinary story (must stay visible in the UI)
Each strategy card shows a discipline badge. Seven fields: Psychology (TMT, self-efficacy, implementation intentions), Behavioral Economics (commitment devices, temptation bundling), Cognitive Science & ADHD research (delay aversion, time blindness), Education/Learning Sciences (utility-value interventions), HCI & Affective Design (the "kawaii" study: cuteness improves focused performance; shame-free UX), Public Health (safety routing), CS/AI. All of it lives in `core/science.py`. Citations are from memory: **verify before the pitch**.

## Design rules (user was specific; don't drift)
- **Palette: 4 blues + butter yellow + white** (butter added at user's request, Nov 21), defined in `core/config.py`: DEEP `#34568B` (all text, soft not harsh; 7.4:1 contrast on white), BLUE `#4A7BD6` (accents/borders only, never body text), SKY `#B8D6FA` (buttons with DEEP text, bars, cheeks, waves), ICE `#EEF5FF` (page bg), WHITE, BUTTER `#FFE58A` (clean butter; user found the earlier beige `#F8E3A3` muddy next to the blues. Used sparingly: "unstuck" highlighter in light mode / butter-coloured word in dark mode (user dislikes the underline in dark), "main jam" badge, Talk to Pip button with a BLUE outline, toggle sparkles, glow behind Pip, cheer stars, sidebar heading stars, "powered by Nemotron" badge). No other colors, including emoji-heavy UI.
- **Light/dark mode**: `config.LIGHT` / `config.DARK` map the same palette to roles; `ui.css(..., dark)` is fully token-driven. Dataframes were replaced by `ui.table_html` so both themes match.
- **Settings menu** (popover button in the sidebar under Connection; replaced the old "Comfort" section). Sidebar has no empty header band: the collapse arrow floats top-right: Dark mode, Easier reading, Stop animations, Click sounds + Volume, Haptics. Deploy button/dev menu hidden via `.streamlit/config.toml` `toolbarMode = "minimal"`.
- **Effects (`core/fx.js`, injected with `st.html(..., unsafe_allow_javascript=True)`)**: WebAudio-synthesised click sounds (no audio files), `navigator.vibrate` haptics (Android only; iOS ignores it), butter/sky sparkles when a toggle turns on (off with "Stop animations" or reduced motion), and **Enter sends the check-in** (Shift+Enter = new line; the text area is in an `st.form` and fx.js turns Enter into Streamlit's Ctrl/Cmd+Enter submit). Streamlit toggles swallow native `change` events, so fx.js listens for clicks. Restart Streamlit after editing `core/*.py` or `fx.js` (modules are cached). **Never put literal `<svg`/`<path` tags inside fx.js strings**: st.html silently drops the whole script (build them with `String.fromCharCode(60)`).
- **Pip interactions**: wings flap every ~6.5s (CSS on `.wing-l/.wing-r` groups in `mascot.svg`), open eyes blink, eyes follow the cursor (`.pip-eyes`), tapping Pip = hop + pink hearts (PINK `#FFB3C9`, hearts only) + a speech pop ("Pip!", "Hey!"...). Tapping empty page space makes a small snow puff; cards lift on hover, lever bars grow in, "unstuck" letters wiggle on hover.
- **Focus sounds** (sidebar pills, own volume slider): White noise (drifting clouds), Rain (falling drops), Birdsong (floating music notes), Ocean (bigger waves + bubbles), Music box (twinkling stars). Audio is synthesised in fx.js (WebAudio, no files); scenery is `ui.ambient_html` (seeded, behind content, hidden by "Stop animations").
- **Pip branding**: sidebar logo (mini Pip + "Pip." wordmark, no tagline), tab icon `assets/pip.png`, tabs "Check in" / "My week" / "The science behind Pip" (user wants these exact names), tiny footer "Pip · made with [pink heart] by two ADHD brains at tidalBYTE '26". Pip's cheeks are PINK (same as the tap hearts), centered "Powered by NVIDIA Nemotron" butter badge.
- **Simplified for ADHD users**: tabs are only "Check in" and "My week". The science is a pop-up (`science_dialog`, `@st.dialog`) opened from a small "The science behind Pip" link at the bottom of the sidebar. "Test Nemotron connection" lives in Settings → Advanced. The "big goal / why are you in college" field is gone (we don't assume college; it didn't help anyone get unstuck); replaced by "When do you focus best?" pills (Morning/Afternoon/Evening/Late night) → `agent.run(..., focus_time=)` so focus blocks/check-ins land at good times. Prompts say "student", not "college student".
- **tidalBYTE easter eggs** (Pebble the penguin, tidalBYTE's mascot; icon from f26.tidaltamu.com saved as `assets/pebble.png`): footer "tidalBYTE '26" links to https://f26.tidaltamu.com/ (new tab); hovering the footer pill makes Pebble peek out ("Hi! I'm Pebble from tidalBYTE!"); typing "pebble" in the check-in box makes Pebble waddle across the waves; tapping Pip 5 times fast makes Pebble pop up ("Pip's my best friend!"). fx.js clones the footer's Pebble image. Reminder: NO tag-like text anywhere in fx.js, even in comments (a comment containing an img tag silently killed the whole script).
- **Narrow screens**: under 900px the page gets extra top padding so the fixed Sound / expand-sidebar buttons never cover the title; under 600px Sound shows only its icon; above 900px the h1 keeps 9.5rem free on the right for the Sound button. "unstuck" is `white-space: nowrap` (its per-letter wiggle spans otherwise let the browser break mid-word). Dizzy Pip has real Archimedean spiral eyes (`mascot._spiral`).
- **Top-right corner = volume button** (`st.container(key="vol_corner")` → `.st-key-vol_corner` is fixed via CSS): popover with Mute everything, Click sounds volume, Focus sounds volume. No "Pip" pill there (user removed it).
- **Waves**: back along the bottom only (user disliked full-page waves): 5 layers that drift sideways at different speeds AND swell up/down (`.wl` wrapper = swell, `.wave` svg = drift).
- **Footer** is a plain rounded pill (user removed the cloud bumps) **fixed** at the bottom centre of the screen, gently floating: "Pip · made with [pink heart] by two ADHD brains at tidalBYTE '26".
- **My week controls**: Time format (12/24-hour) lives in Settings. Small "Colors" popover (material palette icon, NOT an emoji) + compact "Color code by" pills sit to the side, above the month calendar (`st.container(key="wk_tools")`) (pills with colour-circle swatches, one row per type or per course) + "Color code by". Chosen colours are stored in `ss.ev_colors["Type:Exam"]` etc. so they survive switching modes (widget keys are crc32 of that name).
- **Result layout**: Pip's speech bubbles have a real curved, outlined tail (SVG data-URI in `.bubble::before`). "What's jamming the gears" = `ui.jam_html`: the main jam is a big butter box with a pulsing "!" and the student's own words, other three are small hoverable boxes. "Pip's trick for this" = compact strip `ui.move_html` with a tiny, faint citation.
- **One colour system everywhere** (user loves the My week look and wants visual interest + simplicity throughout): `ui.LEVER_COLORS` (Confidence pink, Meaning lavender, Focus mint, Urgency sky) and `ui.PLAN_COLORS` (first step mint, focus block sky, check-in butter, why-it-matters lavender), same pastels as the calendar. Used in the jam boxes, Pip's trick strip, numbered plan tiles (`ui.plan_html` with line icons), check-in checklist rows, colour-coded check-in buttons (fu_good butter / fu_stuck pink / fu_later sky / fu_new lavender), "Coming up" rows (`ui.deadlines_html`, urgency pills), science-tab cards and formula terms.
- **Diagnosis insight**: `evidence` must be a non-obvious insight written to the student (not "you said stuck so you're struggling"), plus `tips` (one tiny action per lever). Diagnosis max_tokens 4000. Hover/tap on the small jam boxes shows an instant CSS `.tipbox` (native `title` tooltips were too slow/invisible).
- Reminder→deadline matching ignores generic words alone ("homework", "exam"...) unless the course matches; course abbreviations (stats→STAT, bio→BIOL...) live in `week._ALIASES`.
- **No more "Did you start?"** (users asked "start what?"). After Pip's plan, a "Check in: <task>" card lists what Pip set up as a checklist (first step, focus block, or "Try Pip's move"), with a progress bar and 4 buttons: "It's going well!" (records success), "Still stuck, new trick" (records failure + reruns agent), "Remind me later" (schedules a check-in in 30 min), "Something else" (new check-in). Checkboxes sparkle like toggles.
- **"What helps you start"** (bottom of My week, replaced the confusing "What works for you" table): big "1/2 times you got started after Pip helped", grouped by feeling ("When you feel: Ooh, something shiny"), each trick with a "works for you / didn't click yet" tag, dot score and "Next time: Pip will try X". Data: `feedback.stats()`. Reset button = "Start fresh".
- **Coming up** (My week): only today-and-later items, soonest first (same day: earlier time first, undated last), 6 at a time with "Show future assignments (N more)" / "Show fewer" underneath; "Show past assignments (N)" toggle sits ABOVE the list (`ss.dl_show_past`, `ss.dl_limit`).
- **Pip's reminders** (top of My week): check-ins are matched to the syllabus item they're about (`week.match_deadline`, keyword overlap) and coloured like that item in the calendar (Google-Calendar style), with a countdown pill ("in 10 min" pulses, "today 6:18 PM", "tomorrow..."); past ones fold into "Earlier". Check-in messages are capped at ~12 words by the tool schema + ACT_SYSTEM.
- **Plain language**: never say "lever" to students outside the science tab (e.g. `feedback.choose` reasons: "It's your first time trying this, so Pip picked the trick that helps the most people.").
- **Thinking state**: `run_agent` runs the agent in a thread and swaps Pip's bubble for "Pipping... (thinking...)" with a live butter stopwatch (1s, 2s...); "(thinking...)" is small and light. Dark mode: "unstuck" is butter text (no line); light mode keeps the highlighter line.
- Sidebar expand button lives inside `stToolbar`: don't hide the toolbar (it's styled as a butter pill when the sidebar is collapsed).
- **Cute but dyslexia-friendly:** Lexend body font, Fredoka rounded headings, ≥17px text, 1.6 line height, extra letter/word spacing, left-aligned, no italics, no ALL CAPS, no harsh borders (soft blurred shadows, 2px borders).
- Gentle animated **waves** along the bottom (slow, see-through, behind content, z-index -1). Settings toggles: "Easier reading" and "Stop animations"; `prefers-reduced-motion` is respected.
- **Pip (`core/mascot.py`)**: round white snowball body, big dark eyes with two white sparkles, tiny beak, sky cheeks, **one small wing on each side**, a small feather tail poking out lower-right, no dots/tuft on the head. User rejected: a seal, small eyes, head dots, a wing/tail that looked like sticks.
- Tone: zero shame, short sentences, one thing at a time.

## Code map (Python + Streamlit)
- `app.py`: UI. Tabs: Check in / My week / The science behind Pip. Sidebar: name, goal, syllabus upload, connection test, comfort toggles.
- `core/nemotron.py`: OpenAI-compatible client, retries on 5xx/network, fails fast on 4xx, `chat_json` with JSON repair, `ping()`.
- `core/agent.py`: safety → diagnose → `feedback.choose` → tool-calling loop (fast model) → guaranteed fallback action if the model skips the tool or errors. Returns `warnings` shown in the UI.
- `core/diagnose.py`: TMT prompt + validation; `_demo()` keyword backup.
- `core/tools.py`: `make_first_step`, `create_calendar_block` (.ics), `schedule_checkin`, `link_to_goal` + JSON schemas.
- `core/feedback.py`: per-strategy tried/worked in `data/feedback.json`.
- `core/syllabus.py`: pypdf text → reasoning model **with thinking off** (`think=False` → `chat_template_kwargs.enable_thinking=False`) → assignments JSON incl. `due_time`. With thinking on, the hidden reasoning ate the whole token budget and returned empty content ("model did not return valid JSON"). `chat_json` also falls back to `reasoning_content`. Demo PDF: `samples/sample_syllabus.pdf`.
- `core/week.py`: My Week. Text dates ("Nov 21, 2026"), 12/24-hour times (`ss.clock`, applies app-wide), events from syllabus + check-ins + `data/block_*.ics`, full-width week view, mini month with hover tooltips, colour-coding by Type/Course with fixed default colours (`_TYPE_COLORS`) and a "Pick your colors" expander. Event-chip pastels (`EVENT_COLORS`) are the only extra colours allowed.
- `core/safety.py`, `core/transcribe.py` (voice, stretch), `core/ui.py` (CSS, waves, cards), `core/science.py`.
- No API key → **demo mode** (canned behaviour), which is useful for UI work.

## Nemotron setup (status as of ~1:40 PM)
- Using the free hosted API: `NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1`, key in `.env` (never commit it; `.env` is gitignored).
- Model IDs, confirmed from the account's `/v1/models` list:
  - `LEVER_REASONING_MODEL=nvidia/nemotron-3.5-super-vl-120b-a12b` (diagnosis + syllabus)
  - `LEVER_FAST_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b` (tool calls)
  - `LEVER_SAFETY_MODEL=nvidia/llama-3.1-nemotron-safety-guard-8b-v3` (`nvidia/nemotron-3.5-content-safety` is listed but returns 404; the old nemoguard content-safety ID returns 410)
  - Ultra (`nvidia/nemotron-3-ultra-550b-a55b`) is available but skipped for latency.
- **Known issue:** chat calls returned **HTTP 403** on Super VL and Lightning. It's a widespread NVIDIA account problem ("Public API Endpoints" permission). Fixes tried/suggested: new key generated from a model page's "Get API Key", teammate's key, ask NVIDIA at the event / #nemotron-models Discord. Fallback: OpenRouter (set `NVIDIA_BASE_URL=https://openrouter.ai/api/v1`, OpenRouter key, OpenRouter model IDs). Check the sidebar's "Test Nemotron connection" for current status.
- Budget: the $50 is **Brev** credit (cloud machines), not API. We run locally; no Brev needed. Avoid GPU instances.

## Run
```bash
source .venv/bin/activate   # mac
streamlit run app.py        # or F5 → "Run Pip (Streamlit)"
```

## Not yet verified
- Real Nemotron tool calling end to end (only demo mode + a failing-client test were run).
- The Streamlit UI was never run in the original sandbox (only static HTML previews), so watch for layout quirks.
- Voice check-ins (`transcribe.py`) are a guess at the API shape.

## Next steps
1. Get Super VL + Lightning returning "works" in the connection test (or switch to OpenRouter).
2. Run 10 real check-ins and tune the diagnosis prompt; make sure the tool calls produce sensible times/steps.
3. Try a real TAMU syllabus PDF.
4. UI polish within the design rules; test with "Easier reading" on.
5. By ~5 PM: Devpost draft (README has the Nemotron blurb, demo script, interdisciplinary table). Record a backup demo video around 6 PM.
6. Stretch: Nemotron Parse for syllabi, voice via Transcribe, Embed+Rerank over a bigger strategy library.
