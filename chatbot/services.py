"""Service helpers for GAAYATRI chatbot views."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

import requests
from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from ipware import get_client_ip

from .constants import (
    BOVINE_CORE_TERMS,
    CATTLE_KEYWORD_PATTERN,
    DEFAULT_GROQ_API_URL,
    DEFAULT_GROQ_MODEL,
    DEFAULT_LOCATION_LABEL,
    DECOMMISSIONED_MODEL_MAP,
    GREETING_PATTERN,
    HUMAN_HEALTH_CUES,
    HUMAN_HEALTH_TERMS,
    INDIA_KEYWORDS,
    IP_PATTERN,
    SELF_HARM_TERMS,
    VIOLENCE_TERMS,
)

logger = logging.getLogger(__name__)

_location_session_key = "chatbot_location_label"


def _clean_location_fragment(value: Any) -> str:
    if value in (None, "", "unknown"):
        return ""
    text = str(value)
    text = IP_PATTERN.sub("", text)
    text = re.sub(r"[^A-Za-z,\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.title()


def _parse_geo_payload(payload: Any) -> Dict[str, str]:
    def _first_match(data: Dict[str, Any], *keys: str) -> str:
        for key in keys:
            if key in data:
                cleaned = _clean_location_fragment(data.get(key))
                if cleaned:
                    return cleaned
        return ""

    if isinstance(payload, dict):
        country = _first_match(payload, "country", "country_name", "countryName", "country_code", "countryCode")
        state = _first_match(payload, "state", "state_name", "region", "region_name", "province")
        district = _first_match(payload, "district", "city", "city_name", "locality", "town")
        return {"country": country, "state": state, "district": district}
    if isinstance(payload, list):
        for item in payload:
            parsed = _parse_geo_payload(item)
            if parsed.get("country"):
                return parsed
        return {"country": "", "state": "", "district": ""}
    if isinstance(payload, str):
        cleaned = _clean_location_fragment(payload)
        if not cleaned:
            return {"country": "", "state": "", "district": ""}
        pieces = [p.strip() for p in cleaned.split(",") if p.strip()]
        if len(pieces) >= 3:
            district, state, country = pieces[-3], pieces[-2], pieces[-1]
        elif len(pieces) == 2:
            district, state, country = "", pieces[0], pieces[1]
        else:
            district, state, country = "", "", pieces[0]
        return {"country": country, "state": state, "district": district}
    return {"country": "", "state": "", "district": ""}


def _format_location_label(parsed: Dict[str, str]) -> str:
    country = (parsed.get("country") or "").strip()
    if country.lower() not in INDIA_KEYWORDS:
        return DEFAULT_LOCATION_LABEL
    parts: list[str] = []
    for key in ("district", "state"):
        value = (parsed.get(key) or "").strip()
        if value and value.lower() not in INDIA_KEYWORDS:
            parts.append(value)
    parts.append("India")
    ordered: Dict[str, None] = {}
    for part in parts:
        if part and part not in ordered:
            ordered[part] = None
    return ", ".join(ordered.keys()) if ordered else "India"


def get_location_label(request) -> str:
    """Return a cached location label for the request/session."""
    session: SessionBase = request.session  # type: ignore[assignment]
    cached = session.get(_location_session_key)
    if cached:
        return cached

    client_ip, _ = get_client_ip(request)
    ip = client_ip or request.META.get("HTTP_X_FORWARDED_FOR") or request.META.get("REMOTE_ADDR") or ""
    if "," in ip:
        ip = ip.split(",")[0].strip()

    geo_api = getattr(settings, "GEOIP_API_URL", None)
    if geo_api:
        try:
            resp = requests.get(f"{geo_api}?ip={ip}", timeout=5)
            if resp.ok:
                try:
                    payload = resp.json()
                except ValueError:
                    payload = resp.text
                parsed = _parse_geo_payload(payload)
                label = _format_location_label(parsed)
                if label:
                    session[_location_session_key] = label
                    session.modified = True
                    return label
        except Exception:  # pragma: no cover - defensive logging
            logger.debug("GeoIP lookup failed; falling back to default", exc_info=True)

    session[_location_session_key] = DEFAULT_LOCATION_LABEL
    session.modified = True
    return DEFAULT_LOCATION_LABEL


def _has_human_health_intent(lowered: str) -> bool:
    if any(f"my {term}" in lowered for term in BOVINE_CORE_TERMS):
        return False
    if any(term in lowered for term in ("cow", "buffalo", "cattle", "calf", "heifer", "bull", "livestock", "animal")):
        return False
    if not any(term in lowered for term in HUMAN_HEALTH_TERMS):
        return False
    return any(cue in lowered for cue in HUMAN_HEALTH_CUES)


def should_refuse(message: str, has_cattle_context: bool) -> Optional[str]:
    lowered = message.lower()
    for term in SELF_HARM_TERMS:
        if term in lowered:
            return "self_harm"
    if not has_cattle_context:
        if any(term in lowered for term in VIOLENCE_TERMS):
            return "violence"
        if _has_human_health_intent(lowered):
            return "human_health"
        if "medicine for me" in lowered or "treatment for me" in lowered or "i need medicine" in lowered:
            return "human_health"
    return None


def beautify_reply(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return text

    text = re.sub(r"[ \t]+", " ", text)
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    formatted_paragraphs = []

    for paragraph in paragraphs:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()]
        if len(sentences) <= 1:
            formatted_paragraphs.append(paragraph)
            continue

        lead = sentences[0]
        bullets = [f"- {sentence}" for sentence in sentences[1:] if sentence]
        if bullets:
            formatted_paragraphs.append("\n".join([lead] + bullets))
        else:
            formatted_paragraphs.append(paragraph)

    return "\n\n".join(formatted_paragraphs) if formatted_paragraphs else text


def build_refusal_reply(reason: str) -> str:
    base = "I'm here to support Indian dairy farmers with cattle care and management."
    if reason == "human_health":
        guidance = (
            " I can't provide advice on human medical concerns. Please speak with a qualified doctor or your local "
            "health helpline for assistance."
        )
    elif reason == "self_harm":
        guidance = (
            " It sounds like you may need urgent help. Contact local emergency services, a trusted person, or a "
            "mental health professional immediately."
        )
    elif reason == "violence":
        guidance = (
            " I can't assist with harmful or illegal actions. Please stay safe and reach out to the appropriate "
            "authorities if needed."
        )
    else:
        guidance = (
            " Let's focus on bovine health, nutrition, reproduction, housing, or dairy farm management queries."
        )
    return beautify_reply(base + guidance)


def normalise_context(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    cleaned: Dict[str, Any] = {}
    allowed_keys = {
        "source",
        "animal_id",
        "name",
        "tag_number",
        "breed",
        "age_years",
        "milk_yield",
        "issue",
        "notes",
        "lactation_stage",
        "last_vaccination_date",
        "is_sick",
    }
    numeric_keys = {"age_years", "milk_yield"}
    boolean_keys = {"is_sick"}
    for key, value in raw.items():
        if key not in allowed_keys or value in (None, ""):
            continue
        if key in numeric_keys:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number.is_integer():
                cleaned[key] = int(number)
            else:
                cleaned[key] = round(number, 2)
            continue
        if key in boolean_keys:
            if isinstance(value, bool):
                cleaned[key] = value
            else:
                cleaned[key] = str(value).strip().lower() in {"1", "true", "yes", "y"}
            continue
        if isinstance(value, (int, float)):
            cleaned[key] = value
            continue
        cleaned[key] = str(value).strip()
    if cleaned and "source" not in cleaned:
        cleaned["source"] = "manual"
    return cleaned


def augment_context_with_cattle(user, context: Dict[str, Any]) -> Dict[str, Any]:
    if not context:
        return {}
    from core.models import Cattle  # Local import to avoid circular dependency

    enriched = dict(context)
    animal_id = enriched.get("animal_id")
    cattle_obj = None
    if animal_id not in (None, ""):
        try:
            animal_pk = int(animal_id)
        except (TypeError, ValueError):
            animal_pk = None
        if animal_pk:
            try:
                cattle_obj = Cattle.objects.get(pk=animal_pk, owner=user)
            except Cattle.DoesNotExist:
                cattle_obj = None
    if cattle_obj:
        enriched["animal_id"] = cattle_obj.pk
        enriched["source"] = "saved"
        enriched.setdefault("name", cattle_obj.name)
        enriched.setdefault("tag_number", cattle_obj.tag_number)
        enriched.setdefault("breed", cattle_obj.breed)
        enriched.setdefault("age_years", cattle_obj.age_years)
        if getattr(cattle_obj, "daily_milk_yield", None) not in (None, ""):
            try:
                milk = float(cattle_obj.daily_milk_yield)
                enriched.setdefault("milk_yield", round(milk, 2) if not milk.is_integer() else int(milk))
            except (TypeError, ValueError):
                pass
        if cattle_obj.last_vaccination_date:
            enriched.setdefault("last_vaccination_date", cattle_obj.last_vaccination_date.isoformat())
    else:
        enriched.pop("animal_id", None)

    for key, value in list(enriched.items()):
        if value in (None, ""):
            enriched.pop(key, None)
    return enriched


def context_summary(ctx: Dict[str, Any]) -> str:
    if not ctx:
        return ""
    parts = []
    if ctx.get("name"):
        parts.append(ctx["name"])
    if ctx.get("breed"):
        parts.append(f"{ctx['breed']} breed")
    if ctx.get("age_years"):
        parts.append(f"{ctx['age_years']} years old")
    if ctx.get("milk_yield"):
        parts.append(f"{ctx['milk_yield']} L/day")
    if ctx.get("issue"):
        parts.append(f"Issue: {ctx['issue']}")
    if ctx.get("lactation_stage"):
        parts.append(f"Stage: {ctx['lactation_stage']}")
    return ", ".join(parts)


@dataclass(slots=True)
class GroqResponse:
    reply: Optional[str]
    error_code: Optional[str]


def call_groq_sync(message: str, session_id: Optional[int] = None, *, location: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None) -> GroqResponse:
    api_url = getattr(settings, "CHATBOT_API_URL", "") or DEFAULT_GROQ_API_URL
    api_key = getattr(settings, "CHATBOT_API_KEY", None)
    configured_model = (getattr(settings, "CHATBOT_MODEL", "") or "").strip()
    if configured_model:
        replacement = DECOMMISSIONED_MODEL_MAP.get(configured_model.lower())
        if replacement:
            logger.warning(
                "CHATBOT_MODEL '%s' is deprecated; substituting recommended model '%s'. Update your environment.",
                configured_model,
                replacement,
            )
            model = replacement
        else:
            model = configured_model
    else:
        model = DEFAULT_GROQ_MODEL
    context = context or {}
    if not api_key:
        logger.error("Groq API key missing (CHATBOT_API_KEY)")
        return GroqResponse(None, "config_missing")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    summary = context_summary(context)
    system_parts = [
        "You are GAAYATRI, a veterinary assistant for Indian dairy farmers.",
        "Follow this priority order: (1) base guidance on trusted Indian sources (ICAR, DAHD, NDDB, state veterinary universities);",
        "(2) reuse the farmer's provided context or GAAYATRI knowledge base details;",
        "(3) if a question is outside bovine care, clearly refuse, suggest speaking with the right professional, and never invent facts.",
        "Keep replies focused on actionable steps (max 5-6 sentences, bullets when helpful), include quick checks or follow-up questions when uncertain,",
        "and remind farmers to contact a local veterinarian immediately for emergencies (bleeding, fractures, prolapse, poisoning, high fever, labor distress).",
        "Assume the farmer is in India and tailor examples to Indian breeds, fodder, climate, and regulations. Never mention IP addresses or how location was inferred.",
    ]
    if summary:
        system_parts.append(f"Current animal context: {summary}.")
    if location and location not in ("", "unknown", DEFAULT_LOCATION_LABEL):
        system_parts.append(f"Farmer region hint: {location}. Apply relevant Indian state considerations.")
    else:
        system_parts.append("No specific region provided beyond India; pick advice suitable for Indian farming conditions.")
    system_prompt = " ".join(system_parts)

    history_messages = []
    if session_id:
        from .models import ChatMessage  # Local import to avoid circular dependency

        past_entries = list(ChatMessage.objects.filter(session_id=session_id).order_by("-created_at")[:8])
        if past_entries and past_entries[0].role == "user" and past_entries[0].text == message:
            past_entries = past_entries[1:]
        for entry in reversed(past_entries):
            history_messages.append(
                {
                    "role": "assistant" if entry.role == "bot" else "user",
                    "content": entry.text,
                }
            )

    user_prompt = message
    if context.get("issue") and context["issue"].lower() not in message.lower():
        user_prompt = f"Issue: {context['issue']}. Question: {message}"

    payload = {
        "model": model,
        "messages": (
            [{"role": "system", "content": system_prompt}]
            + history_messages
            + [{"role": "user", "content": user_prompt}]
        ),
        "temperature": 0.7,
        "max_tokens": 512,
    }
    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        body = exc.response.text if exc.response is not None else str(exc)
        logger.exception("Groq HTTP error (status %s): %s", status, body[:500])
        return GroqResponse(None, f"http_{status}")
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Groq request failed: %s", exc)
        return GroqResponse(None, "request_failed")

    reply_text = data.get("choices", [{}])[0].get("message", {}).get("content")
    if not reply_text:
        reply_text = data.get("reply") or data.get("text")
    if not reply_text:
        logger.warning("Groq response missing content: %s", data)
        return GroqResponse(None, "empty_response")
    return GroqResponse(reply_text, None)


def greeting_for_context(context: Dict[str, Any]) -> str:
    welcome = (
        "Namaste! I'm GAAYATRI's dairy assistant. Ask me about cow or buffalo health, milk yield, nutrition, "
        "breeding, or daily management."
    )
    summary = context_summary(context)
    if summary:
        welcome = f"Namaste! I see we're discussing {summary}. " + welcome
    return beautify_reply(welcome)


def matches_greeting(text: str) -> bool:
    return bool(GREETING_PATTERN.search(text.lower()))


def keyword_match(lowered: str) -> bool:
    return bool(CATTLE_KEYWORD_PATTERN.search(lowered))


def embedding_debug_log(score: Optional[float], passed: bool, user_id: Any) -> None:
    if score is None:
        return
    logger.debug(
        "Semantic filter score %.3f (pass=%s) for user %s",
        score,
        passed,
        user_id,
    )


__all__ = [
    "beautify_reply",
    "build_refusal_reply",
    "call_groq_sync",
    "context_summary",
    "get_location_label",
    "greeting_for_context",
    "keyword_match",
    "matches_greeting",
    "normalise_context",
    "augment_context_with_cattle",
    "should_refuse",
    "embedding_debug_log",
]
