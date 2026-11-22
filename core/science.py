"""The interdisciplinary backbone: the strategy library and the disciplines
it draws on. Every strategy the agent can pick is tagged with the field it
comes from and a citation, and the UI shows that tag on every card.
Double-check citations before you pitch them."""

LEVERS = {
    "expectancy": {
        "label": "Can I even do this?",
        "short": "Confidence",
        "buddy_mood": "wobbly",
        "explain": "The task feels too big or too hard, so starting feels pointless.",
    },
    "value": {
        "label": "Why does this matter?",
        "short": "Meaning",
        "buddy_mood": "shrug",
        "explain": "The task feels boring or disconnected from what you care about.",
    },
    "impulsiveness": {
        "label": "Ooh, something shiny",
        "short": "Focus",
        "buddy_mood": "dizzy",
        "explain": "Distractions win the moment-to-moment tug of war.",
    },
    "delay": {
        "label": "It's due... later?",
        "short": "Urgency",
        "buddy_mood": "sleepy",
        "explain": "The deadline feels far away, so it doesn't feel real yet.",
    },
}

DISCIPLINES = {
    "Psychology": {
        "what": "Temporal Motivation Theory gives the agent its four-lever diagnosis; "
                "self-efficacy and if-then planning research give it fixes.",
        "where": "Diagnosis bars, tiny-first-step and if-then cards",
        "cite": "Steel (2007), Psychological Bulletin; Gollwitzer (1999), American Psychologist",
    },
    "Behavioral Economics": {
        "what": "Present bias explains why distant deadlines don't feel real. Commitment devices "
                "and temptation bundling counter it.",
        "where": "Mini-deadline and temptation-bundle cards, calendar blocks",
        "cite": "Ariely & Wertenbroch (2002), Psychological Science; Milkman et al. (2014), Management Science",
    },
    "Cognitive Science & ADHD research": {
        "what": "ADHD research on delay aversion and 'time blindness' explains why the "
                "Impulsiveness and Delay levers are often the loudest for ADHD brains.",
        "where": "ADHD notes on each strategy; visible countdowns; one-thing-at-a-time UI",
        "cite": "Barkley (1997), Psychological Bulletin; Sonuga-Barke et al. (1992), J. Child Psychology & Psychiatry",
    },
    "Education / Learning Sciences": {
        "what": "Utility-value interventions (linking coursework to personal goals) raise interest "
                "and grades; syllabi are the real-world data source.",
        "where": "'Why it matters' card, syllabus import",
        "cite": "Hulleman & Harackiewicz (2009), Science",
    },
    "HCI & Affective Design": {
        "what": "Cute imagery has been shown to improve careful, focused task performance; a "
                "shame-free buddy lowers the emotional cost of checking in.",
        "where": "Pip the buddy, moods, soft blue palette, big single buttons",
        "cite": "Nittono et al. (2012), PLoS ONE ('The Power of Kawaii')",
    },
    "Public Health": {
        "what": "Students in distress need people, not productivity tips. A safety model routes "
                "those check-ins to real support.",
        "where": "Safety check before every response",
        "cite": "988 Suicide & Crisis Lifeline; campus counseling services",
    },
    "Computer Science / AI": {
        "what": "Nemotron models parse syllabi, diagnose, pick and run tools, and learn from feedback.",
        "where": "Agent trace panel",
        "cite": "NVIDIA Nemotron",
    },
}

STRATEGIES = [
    {
        "id": "tiny_first_step",
        "lever": "expectancy",
        "name": "Tiny first step",
        "how": "Shrink the task to a 10-minute step you can't fail.",
        "discipline": "Psychology",
        "cite": "Bandura (1977), self-efficacy",
        "adhd": "Starting is the hardest part for ADHD brains; a tiny step lowers the activation energy.",
        "tool": "make_first_step",
    },
    {
        "id": "success_spiral",
        "lever": "expectancy",
        "name": "Success spiral",
        "how": "Do the easiest part first to build momentum before the hard part.",
        "discipline": "Psychology",
        "cite": "Steel (2007)",
        "adhd": "Quick wins give the dopamine hit that keeps you going.",
        "tool": "make_first_step",
    },
    {
        "id": "why_it_matters",
        "lever": "value",
        "name": "Why it matters to YOU",
        "how": "Connect this assignment to your own goal in one sentence.",
        "discipline": "Education / Learning Sciences",
        "cite": "Hulleman & Harackiewicz (2009)",
        "adhd": "Interest is fuel: if it's personally meaningful, it's easier to engage.",
        "tool": "link_to_goal",
    },
    {
        "id": "temptation_bundle",
        "lever": "value",
        "name": "Temptation bundle",
        "how": "Pair the boring task with something you enjoy (only allowed during it).",
        "discipline": "Behavioral Economics",
        "cite": "Milkman et al. (2014)",
        "adhd": "Borrows stimulation from something fun to get through something dull.",
        "tool": "create_calendar_block",
    },
    {
        "id": "if_then_plan",
        "lever": "impulsiveness",
        "name": "If-then plan",
        "how": "'If it's [time] at [place], then I open [thing].' Decided now, not later.",
        "discipline": "Psychology",
        "cite": "Gollwitzer (1999)",
        "adhd": "Moves the decision out of the distracted moment and into the plan.",
        "tool": "create_calendar_block",
    },
    {
        "id": "body_double",
        "lever": "impulsiveness",
        "name": "Body double",
        "how": "Work next to someone (in person or on call), with Pip checking in.",
        "discipline": "HCI & Affective Design",
        "cite": "Zajonc (1965), social facilitation. Note: ADHD-specific evidence is still limited",
        "adhd": "Many ADHD students report it helps a lot; the research is still catching up.",
        "tool": "schedule_checkin",
    },
    {
        "id": "mini_deadline",
        "lever": "delay",
        "name": "Mini-deadline",
        "how": "Set an earlier, personal deadline for a first draft, and put it on the calendar.",
        "discipline": "Behavioral Economics",
        "cite": "Ariely & Wertenbroch (2002)",
        "adhd": "Makes 'later' into 'now-ish' so the urgency kicks in earlier.",
        "tool": "create_calendar_block",
    },
    {
        "id": "visible_countdown",
        "lever": "delay",
        "name": "Make time visible",
        "how": "A check-in from Pip with a real countdown: hours left, not 'next week'.",
        "discipline": "Cognitive Science & ADHD research",
        "cite": "Barkley (1997), time blindness",
        "adhd": "Time blindness is real; making time concrete helps it register.",
        "tool": "schedule_checkin",
    },
]

STRATEGY_BY_ID = {s["id"]: s for s in STRATEGIES}
