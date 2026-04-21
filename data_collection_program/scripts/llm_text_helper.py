from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


DATA_COLLECTION_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
ALLOWED_MODES = {"auto", "api", "local"}


@dataclass(frozen=True)
class TextMode:
    requested: str
    effective: str
    model: str | None
    has_key: bool

    @property
    def is_api(self) -> bool:
        return self.effective == "api"


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv(DATA_COLLECTION_ROOT / ".env", override=False)


def resolve_text_mode(model_env_var: str | None = None) -> TextMode:
    _load_dotenv_if_available()

    requested = os.getenv("DATA_COLLECTION_TEXT_MODE", "auto").strip().lower()
    if requested not in ALLOWED_MODES:
        requested = "auto"

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    has_key = bool(api_key)

    if model_env_var:
        model = os.getenv(model_env_var, "").strip()
    else:
        model = ""
    if not model:
        model = os.getenv("OPENAI_TEXT_MODEL", "").strip()
    if not model:
        model = DEFAULT_OPENAI_MODEL

    if requested == "local":
        effective = "local"
    elif requested == "api":
        if not has_key:
            raise RuntimeError(
                "DATA_COLLECTION_TEXT_MODE=api requires OPENAI_API_KEY in the environment or .env file."
            )
        effective = "api"
    else:
        effective = "api" if has_key else "local"

    return TextMode(
        requested=requested,
        effective=effective,
        model=model if effective == "api" else None,
        has_key=has_key,
    )


def describe_text_mode(mode: TextMode) -> str:
    if mode.is_api and mode.model:
        return f"OpenAI API ({mode.model})"
    return "Local fallback"


def _extract_response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, "output", None)
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            content = getattr(item, "content", None)
            if not isinstance(content, list):
                continue
            for part in content:
                text = getattr(part, "text", None)
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        if chunks:
            return "\n".join(chunks).strip()

    return ""


def request_openai_text(
    *,
    system_prompt: str,
    user_prompt: str,
    model_env_var: str | None = None,
    temperature: float = 0.2,
    max_output_tokens: int = 300,
) -> tuple[str, TextMode]:
    mode = resolve_text_mode(model_env_var=model_env_var)
    if not mode.is_api or not mode.model:
        raise RuntimeError("OpenAI API mode is not enabled.")

    try:
        from openai import OpenAI
    except Exception as exc:
        raise RuntimeError(
            "openai package is not installed. Install requirements.txt to use API mode."
        ) from exc

    client_kwargs = {"api_key": os.getenv("OPENAI_API_KEY", "").strip()}
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)

    try:
        response = client.responses.create(
            model=mode.model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
        )
        text = _extract_response_text(response)
        if text:
            return text, mode
    except Exception:
        pass

    response = client.chat.completions.create(
        model=mode.model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_output_tokens,
    )
    content = response.choices[0].message.content
    if isinstance(content, str):
        text = content.strip()
    elif isinstance(content, list):
        text = "\n".join(
            part.get("text", "").strip()
            for part in content
            if isinstance(part, dict) and part.get("text")
        ).strip()
    else:
        text = ""
    if not text:
        raise RuntimeError("OpenAI returned an empty response.")
    return text, mode
