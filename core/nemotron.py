"""Thin wrapper around NVIDIA's OpenAI-compatible endpoint, with retries
and JSON repair. When no API key is set, `demo` is True and callers fall
back to canned behaviour so the UI still works."""
import json
import re
import time

from . import config


class NemotronError(Exception):
    pass


_THINK = re.compile(r"<think>.*?</think>", re.S)


def extract_json(text: str):
    """Pull a JSON object/array out of a model reply (strips <think> and fences)."""
    text = _THINK.sub("", text or "").strip()
    fence = re.search(r"```(?:json)?\s*([\[{].*?[\]}])\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
        if not starts:
            raise ValueError("no JSON found")
        end = max(text.rfind("}"), text.rfind("]"))
        text = text[min(starts):end + 1]
    return json.loads(text)


class Nemotron:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key if api_key is not None else config.API_KEY
        self.demo = not self.api_key
        self.calls = []  # (model, seconds) — shown in the UI trace
        self._client = None
        if not self.demo:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key, base_url=config.BASE_URL, timeout=90)

    def chat(self, messages, model, tools=None, temperature=0.3, max_tokens=1500, think=True):
        kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
        if not think:  # Nemotron reasoning models: skip the hidden <think> pass (much faster, no truncation)
            kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        err = None
        for attempt in range(3):
            try:
                t0 = time.time()
                resp = self._client.chat.completions.create(**kwargs)
                self.calls.append((model, round(time.time() - t0, 2)))
                return resp.choices[0].message
            except Exception as e:
                err = e
                code = getattr(e, "status_code", None)
                if code in (400, 422) and "extra_body" in kwargs:  # endpoint doesn't know the flag: drop it
                    kwargs.pop("extra_body")
                    continue
                if code in (400, 401, 403, 404, 422):  # won't fix itself: fail fast
                    raise NemotronError(f"{model} -> HTTP {code}: {str(e)[:300]}") from e
                time.sleep(1.5 * (attempt + 1))  # network / rate limit / 5xx: retry
        raise NemotronError(f"{model}: {str(err)[:300]}")

    def ping(self, model: str):
        """Tiny test call. Returns (ok, message)."""
        if self.demo:
            return False, "no NVIDIA_API_KEY found in .env"
        if not model:
            return False, "no model ID set in .env"
        try:
            t0 = time.time()
            self._client.chat.completions.create(
                model=model, messages=[{"role": "user", "content": "Reply with: ok"}], max_tokens=20)
            return True, f"{time.time() - t0:.1f}s"
        except Exception as e:
            code = getattr(e, "status_code", "")
            hint = {401: "bad API key", 403: "key not allowed for this model",
                    404: "model ID not found; copy it from 'View Code' on build.nvidia.com",
                    429: "rate limited; wait a minute"}.get(code, "")
            return False, f"HTTP {code} {hint}: {str(e)[:160]}"

    def chat_json(self, system: str, user: str, model: str, temperature=0.2, max_tokens=1500, think=True):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        for _ in range(2):
            msg = self.chat(messages, model, temperature=temperature, max_tokens=max_tokens, think=think)
            content = msg.content or ""
            if not content.strip():  # the reasoning used the whole budget; the answer may be in the reasoning
                content = getattr(msg, "reasoning_content", None) or ""
            try:
                return extract_json(content)
            except (ValueError, json.JSONDecodeError):
                messages += [
                    {"role": "assistant", "content": msg.content or ""},
                    {"role": "user", "content": "That was not valid JSON. Reply with ONLY the JSON."},
                ]
        raise NemotronError("model did not return valid JSON")
