import json
import logging
from typing import Any, Dict, Optional

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from core.models import Cattle

from .constants import BOVINE_CORE_TERMS, DEFAULT_LOCATION_LABEL
from .models import ChatMessage, ChatSession
from .services import (
    augment_context_with_cattle,
    beautify_reply,
    build_refusal_reply,
    call_groq_sync,
    context_summary,
    embedding_debug_log,
    get_location_label,
    greeting_for_context,
    keyword_match,
    matches_greeting,
    normalise_context,
    should_refuse,
)


embedding_is_cattle_related: Optional[Any] = None
_embedding_import_error: Optional[Exception] = None
try:
    from .embedding_filter import is_cattle_related as embedding_is_cattle_related  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency or load failure
    _embedding_import_error = exc


logger = logging.getLogger(__name__)


if _embedding_import_error:
    logger.warning("Semantic embedding filter disabled: %s", _embedding_import_error)


@require_POST
@login_required
def chat_api(request):
    data = json.loads(request.body.decode("utf-8") or "{}")
    msg = (data.get("message") or "").strip()
    if not msg:
        return JsonResponse({"ok": False, "error": "empty_message"}, status=400)

    if not getattr(request.user, "is_farmer", False):
        return JsonResponse(
            {"ok": False, "error": "forbidden", "detail": "chatbot available to farmers only"},
            status=403,
        )

    active_session_id = request.session.get("chatbot_session_id")
    session = None
    if active_session_id:
        session = ChatSession.objects.filter(pk=active_session_id, user=request.user).first()
    if session is None:
        session = ChatSession.objects.create(user=request.user)
        request.session["chatbot_session_id"] = session.pk

    incoming_context = normalise_context(data.get("context"))
    incoming_context = augment_context_with_cattle(request.user, incoming_context)

    context = session.context or {}
    if incoming_context:
        if context != incoming_context:
            if ChatMessage.objects.filter(session=session).exists():
                session = ChatSession.objects.create(user=request.user, context=incoming_context)
                request.session["chatbot_session_id"] = session.pk
            else:
                session.context = incoming_context
                session.save(update_fields=["context"])
            context = incoming_context
        else:
            context = incoming_context

    has_context = bool(context)
    lowered = msg.lower()
    bovine_hint = any(term in lowered for term in BOVINE_CORE_TERMS)

    keyword_hit = keyword_match(lowered)
    embedding_pass = False
    embedding_score: Optional[float] = None
    if embedding_is_cattle_related:
        try:
            embedding_pass, embedding_score = embedding_is_cattle_related(msg)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Embedding similarity check failed: %s", exc)
            embedding_pass = False
    elif _embedding_import_error:
        logger.debug("Embedding filter unavailable: %s", _embedding_import_error)

    location_label = get_location_label(request)
    ChatMessage.objects.create(session=session, role="user", text=msg, location=location_label)

    if matches_greeting(lowered):
        welcome = greeting_for_context(context if has_context else {})
        bot_msg = ChatMessage.objects.create(session=session, role="bot", text=welcome, location=location_label)
        return JsonResponse({"ok": True, "reply": welcome, "bot_message_id": bot_msg.pk, "session_id": session.pk})

    refusal_reason = should_refuse(msg, has_context or bovine_hint)
    if refusal_reason:
        refusal_reply = build_refusal_reply(refusal_reason)
        bot_msg = ChatMessage.objects.create(session=session, role="bot", text=refusal_reply, location=location_label)
        return JsonResponse({"ok": True, "reply": refusal_reply, "bot_message_id": bot_msg.pk, "session_id": session.pk})

    if not (has_context or keyword_hit or embedding_pass):
        scope_msg = beautify_reply(
            "I'm focused on dairy cattle support. Choose one of your saved animals or share breed, age, milk yield, and "
            "current symptoms so I can guide you better."
        )
        bot_msg = ChatMessage.objects.create(session=session, role="bot", text=scope_msg, location=location_label)
        return JsonResponse({"ok": True, "reply": scope_msg, "bot_message_id": bot_msg.pk, "session_id": session.pk})

    embedding_debug_log(embedding_score, embedding_pass, getattr(request.user, "id", "anonymous"))

    groq_response = call_groq_sync(
        msg,
        session_id=session.pk,
        location=location_label,
        context=context,
    )
    if groq_response.reply is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "model_error",
                "detail": "Unable to contact the GAAYATRI model right now. Please try again shortly.",
                "code": groq_response.error_code,
                "session_id": session.pk,
            },
            status=502 if groq_response.error_code else 500,
        )

    beautified_reply = beautify_reply(groq_response.reply)
    bot_msg = ChatMessage.objects.create(session=session, role="bot", text=beautified_reply, location=location_label)
    return JsonResponse({"ok": True, "reply": beautified_reply, "bot_message_id": bot_msg.pk, "session_id": session.pk})


@login_required
def bot_ui(request):
    """Render the small bot UI (can be included on pages)."""
    if not getattr(request.user, 'is_farmer', False):
        return JsonResponse({'ok': False, 'error': 'forbidden', 'detail': 'chat UI available to farmers only'}, status=403)
    return render(request, 'chatbot/bot.html')


@require_POST
@login_required
def feedback(request):
    """Accept feedback for a bot message. POST JSON: {"message_id": <id>, "feedback": 1|-1} """
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
        mid = int(data.get('message_id'))
        fb = int(data.get('feedback'))
    except Exception:
        return JsonResponse({'ok': False, 'error': 'invalid_payload'}, status=400)

    try:
        m = ChatMessage.objects.get(pk=mid, role='bot')
    except ChatMessage.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'not_found'}, status=404)

    # only allow feedback from the same session user (simple check)
    if m.session.user != request.user:
        return JsonResponse({'ok': False, 'error': 'forbidden'}, status=403)

    if fb not in (-1, 0, 1):
        return JsonResponse({'ok': False, 'error': 'invalid_feedback'}, status=400)

    m.feedback = fb
    m.save()
    return JsonResponse({'ok': True})
