# Pip, the study buddy that knows *why* you're stuck

Built at tidalBYTE '26 by two students with ADHD, for every student who's ever stared at an assignment for three hours without starting it.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env # paste your build.nvidia.com key + exact model IDs
streamlit run app.py
```
No key? It runs in **demo mode** (keyword diagnosis, canned syllabus) so you can build the UI in parallel.

## How it works (the agent)

```
check-in (text / voice)
   │
   ├─ 1. Safety ......... Nemotron content-safety model + local filter → distress? route to 988 / counseling
   ├─ 2. Diagnose ....... Nemotron reasoning model scores 4 TMT levers, quoting the student's own words
   ├─ 3. Pick strategy .. feedback loop: which fixes have actually worked for THIS student?
   ├─ 4. Act ............ Nemotron (fast model) calls tools: first step, calendar block (.ics), check-in, goal link
   └─ 5. Learn .......... "Did you start?" → updates strategy scores → next time Pip adapts
syllabus PDFs → Nemotron extracts every graded item, due date, and weight → feeds steps 2 and 4
```

| File | What |
|---|---|
| `core/diagnose.py` | TMT diagnosis prompt + output validation |
| `core/agent.py` | tool-calling loop, with a guaranteed fallback if the model skips the tool |
| `core/science.py` | strategy library: every fix tagged with its discipline + citation |
| `core/feedback.py` | the learning loop |
| `core/safety.py` | safety routing |
| `core/syllabus.py` | syllabus → deadlines |
| `core/mascot.py` | Pip the shima enaga (SVG, 7 moods) |
| `core/ui.py` | palette, dyslexia-friendly type, animated waves |

## Why it's interdisciplinary

Motivation isn't a computer science problem. It's a human one. Each part of Pip comes from a different field, and the app labels each strategy card with the field it comes from:

| Field | What it gives Pip |
|---|---|
| **Psychology** | Temporal Motivation Theory: Motivation = (Expectancy × Value) ÷ (Impulsiveness × Delay). Plus self-efficacy and if-then plans. |
| **Behavioral Economics** | Present bias, commitment devices (mini-deadlines), temptation bundling |
| **Cognitive Science / ADHD research** | Delay aversion and time blindness: why Impulsiveness and Delay are the loudest levers for ADHD brains |
| **Education / Learning Sciences** | Utility-value interventions ("why this matters to *you*"); syllabi as real data |
| **HCI & Affective Design** | "Kawaii" research: cute imagery can improve focused performance. Shame-free buddy, calm palette |
| **Public Health** | Safety-first routing for students in real distress |
| **CS / AI** | Nemotron does the reasoning, tool use, and adaptation |

**One-line pitch:** *"Most productivity apps treat every stall the same. Psychology says there are four different reasons you're stuck. Pip uses Nemotron to figure out which one, then picks a fix from the field that studies it."*

## Devpost: "What Nemotron does" (draft)

> Nemotron is the agent's brain at every step, not a chat layer. (1) It reads messy syllabus PDFs into structured deadlines and grade weights. (2) A Nemotron reasoning model diagnoses *why* a student is procrastinating using Temporal Motivation Theory, scoring four levers and quoting the student's own words so the diagnosis is grounded and explainable. (3) A fast Nemotron model then calls tools that do real work: writing a 10-minute first step, creating calendar blocks, scheduling check-ins, linking the task to what the student cares about. (4) A Nemotron safety model screens every check-in and routes distress to human support. A feedback loop records whether each intervention got the student started, so strategy selection adapts per student. We split the work across models: deep reasoning where accuracy matters, the fast model for high-volume tool calls. We kept output quality up with strict JSON outputs, validation and retry, evidence quotes, and a guaranteed-action fallback.

## Who builds what (2 people)

- **Person A: agent brain.** Get the API key and model IDs working, tune `diagnose.py` on 10 real check-ins, verify tool calling in `agent.py`, try a real syllabus.
- **Person B: Pip & the product.** UI polish in `app.py`/`ui.py`, the science tab, Devpost, pitch, demo video.
- **Together at 5:00 PM:** run the demo script 3 times end to end.

## 3-minute demo script

1. *"We both have ADHD. 'Just focus' has never worked for us."* (10s)
2. Upload a real TAMU syllabus → deadlines appear in **My week**.
3. Check in: *"lab report due Tuesday, I keep opening TikTok."* Pip goes dizzy, and **Focus** is the main jam, with the quote highlighted.
4. Pip's move: if-then plan + calendar block → download the .ics.
5. Click **"Not yet"** → Pip says *"If-then worked 0/1 for you, switching to Body double."* ← the learning loop.
6. Click **The science behind Pip** (small link at the bottom of the sidebar) → seven fields, one buddy.
7. Easter eggs for the judges: hover the footer (Pebble peeks out, tidalBYTE link), type "pebble" in the check-in box, or tap Pip 5 times fast.
7. Open the agent trace → show the Nemotron calls and tool calls.

## Stretch goals (if time)
- Nemotron Parse for scanned/table-heavy syllabi
- Voice check-ins via the Transcribe model (`core/transcribe.py`)
- Embed + Rerank over a bigger strategy library

*Pip is a study tool, not a treatment for ADHD.*
