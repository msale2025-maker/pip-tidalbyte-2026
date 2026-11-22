"""Voice check-ins (stretch goal). Tries an OpenAI-style transcription
endpoint for the ASR model in PIP_ASR_MODEL. Check the model page on
build.nvidia.com for the exact API; some speech models use NVIDIA's Riva
gRPC client instead, so adapt this function if needed."""
import io

from . import config
from .nemotron import Nemotron


def transcribe(client: Nemotron, audio_bytes: bytes) -> str | None:
    if client.demo or not config.ASR_MODEL:
        return None
    try:
        f = io.BytesIO(audio_bytes)
        f.name = "checkin.wav"
        r = client._client.audio.transcriptions.create(model=config.ASR_MODEL, file=f)
        return getattr(r, "text", None)
    except Exception:
        return None
