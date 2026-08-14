from __future__ import annotations

import re
from collections.abc import Sequence

from groq import RateLimitError

from core.config import GROQ_MODEL_CANDIDATES, client


class GroqQuotaExceeded(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: float | None = None,
        models_tried: tuple[str, ...] = (),
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.models_tried = models_tried


_RETRY_AFTER_PATTERN = re.compile(
    r"try again in (?:(?P<minutes>\d+)m)?(?P<seconds>\d+(?:\.\d+)?)s",
    re.IGNORECASE,
)


def _extract_response_message(response: object | None) -> str | None:
    if response is None:
        return None

    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    json_payload = None
    try:
        json_payload = response.json()  # type: ignore[call-arg]
    except Exception:
        json_payload = None

    if isinstance(json_payload, dict):
        error = json_payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message.strip()

    return None


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        pass

    match = _RETRY_AFTER_PATTERN.search(value)
    if not match:
        return None

    minutes = int(match.group("minutes") or 0)
    seconds = float(match.group("seconds"))
    return minutes * 60 + seconds


def _extract_retry_after_seconds(exc: RateLimitError) -> float | None:
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers is not None:
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        parsed = _parse_retry_after(retry_after)
        if parsed is not None:
            return parsed

    message = _extract_response_message(response)
    if message:
        parsed = _parse_retry_after(message)
        if parsed is not None:
            return parsed

    return None


def _build_rate_limit_message(exc: RateLimitError, model_name: str) -> str:
    response = getattr(exc, "response", None)
    message = _extract_response_message(response)
    if message:
        return f"Groq rate limit reached for model '{model_name}': {message}"
    return f"Groq rate limit reached for model '{model_name}'."


def complete_json(
    messages: Sequence[dict[str, str]],
    *,
    model_candidates: tuple[str, ...] | None = None,
) -> str:
    candidates = model_candidates or GROQ_MODEL_CANDIDATES
    last_rate_limit: RateLimitError | None = None
    retry_after_seconds: float | None = None

    for model_name in candidates:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=list(messages),
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError(f"Groq returned an empty response for model '{model_name}'.")
            return content
        except RateLimitError as exc:
            last_rate_limit = exc
            parsed_retry_after = _extract_retry_after_seconds(exc)
            if parsed_retry_after is not None:
                if retry_after_seconds is None:
                    retry_after_seconds = parsed_retry_after
                else:
                    retry_after_seconds = max(retry_after_seconds, parsed_retry_after)
            continue

    if last_rate_limit is not None:
        raise GroqQuotaExceeded(
            _build_rate_limit_message(last_rate_limit, candidates[-1]),
            retry_after_seconds=retry_after_seconds,
            models_tried=candidates,
        ) from last_rate_limit

    raise RuntimeError("No Groq model candidates were configured.")
