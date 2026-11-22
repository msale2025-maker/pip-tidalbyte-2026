"""Settings. Copy .env.example to .env and fill in your key.

Model IDs: copy the exact IDs from build.nvidia.com (open a model page ->
"View Code"). The defaults below are placeholders and may not match the
current catalogue.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# Reasoning model: diagnosis + syllabus extraction (Super VL or Ultra)
def _env(name: str, default: str = "") -> str:
    """PIP_<name>, falling back to the old LEVER_<name> so older .env files keep working."""
    return os.getenv(f"PIP_{name}") or os.getenv(f"LEVER_{name}") or default


REASONING_MODEL = _env("REASONING_MODEL", "nvidia/nemotron-3.5-super-vl-120b-a12b")
# Fast model: tool calls / actions (Lightning)
FAST_MODEL = _env("FAST_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
# Content-safety model
SAFETY_MODEL = _env("SAFETY_MODEL", "nvidia/llama-3.1-nemotron-safety-guard-8b-v3")
# Speech-to-text model (optional; voice check-ins)
ASR_MODEL = _env("ASR_MODEL", "")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# The palette: 4 blues + butter yellow + white. Use ONLY these.
# Contrast (WCAG): DEEP on white 7.4:1 (AAA), DEEP on SKY 4.9:1 (AA), DEEP on BUTTER 6.1:1 (AA).
DEEP = "#34568B"   # all text, eyes/beak. Soft slate-blue, not harsh navy
BLUE = "#4A7BD6"   # accents: borders, main-jam bar, wing/tail (never body text)
SKY = "#B8D6FA"    # buttons (with DEEP text), bars, cheeks, waves
ICE = "#EEF5FF"    # page background, belly
WHITE = "#FFFFFF"  # cards, Pip's fluffy body
BUTTER = "#FFE58A" # clean butter highlight, used sparingly: main jam, send button, sparkles, glow behind Pip
PINK = "#FFB3C9"   # hearts (tap Pip, footer) and Pip's blush only
NAVY = DEEP        # backwards-compat alias

# Light and dark themes are the same palette, re-mapped. Dark keeps the blues
# (lifted for contrast on navy) and the same butter, slightly softened.
LIGHT = dict(text=DEEP, accent=BLUE, line=SKY, bg=ICE, surface=WHITE, btn=SKY, btn_text=DEEP,
             bar=SKY, butter=BUTTER, on_butter=DEEP, wave_a=SKY, wave_b=BLUE, shadow="rgba(74,123,214,.13)")
DARK = dict(text="#E3ECFA", accent="#8DB2F2", line="#2F4C7C", bg="#131E35", surface="#1B2A47",
            btn="#2A4472", btn_text="#EEF5FF", bar="#4A7BD6", butter="#FFE58A", on_butter=DEEP,
            wave_a="#4A7BD6", wave_b=SKY, shadow="rgba(0,0,0,.35)")
