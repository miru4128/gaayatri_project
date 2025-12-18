"""Semantic filter to ensure queries relate to dairy and cattle topics."""
from __future__ import annotations

import logging
import threading
from typing import Any, Sequence, Tuple

import numpy as np
from django.conf import settings

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError as exc:  # pragma: no cover - import guarded for environments without dependency
    raise RuntimeError("sentence-transformers must be installed to use the embedding filter") from exc

logger = logging.getLogger(__name__)


DEFAULT_MODEL_NAME = getattr(settings, "CHATBOT_EMBED_MODEL", "all-MiniLM-L6-v2")
HF_TOKEN = getattr(settings, "HUGGINGFACE_API_TOKEN", None) or getattr(settings, "SENTENCE_TRANSFORMERS_API_KEY", None)

# Prompts that represent our allowed topic cluster
CATTLE_TOPIC_PROMPTS: Sequence[str] = (
    "cattle health and disease",
    "cow nutrition and feed",
    "buffalo milk production",
    "livestock housing and infrastructure",
    "veterinary support for cattle",
    "breeding and artificial insemination for cows",
    "mastitis in dairy cows",
    "calf care and management",
    "fodder and silage for cattle",
    "weather effects on dairy cattle",
    "dairy farm management",
)

_model = None
_topic_embeddings = None
_model_lock = threading.Lock()


def _load_model() -> Tuple[SentenceTransformer, Any]:
    """Lazy-load the sentence transformer and topic embeddings."""
    global _model, _topic_embeddings
    if _model is None:
        with _model_lock:
            if _model is None:
                kwargs = {}
                if HF_TOKEN:
                    kwargs["use_auth_token"] = HF_TOKEN
                logger.info("Loading sentence-transformer model '%s'", DEFAULT_MODEL_NAME)
                _model = SentenceTransformer(DEFAULT_MODEL_NAME, **kwargs)
    if _topic_embeddings is None:
        with _model_lock:
            if _topic_embeddings is None:
                _topic_embeddings = _model.encode(list(CATTLE_TOPIC_PROMPTS), convert_to_tensor=True)
    return _model, _topic_embeddings


def is_cattle_related(query: str, threshold: float | None = None) -> Tuple[bool, float]:
    """Return (is_related, cosine_score) based on semantic similarity to cattle prompts."""
    if not query:
        return False, 0.0
    model, topic_emb = _load_model()
    q_emb = model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(q_emb, topic_emb)[0].cpu().numpy()
    best = float(np.max(scores)) if scores.size else 0.0
    if threshold is None:
        threshold = float(getattr(settings, "ALLOWED_SIMILARITY", 0.65))
    is_related = best >= threshold
    logger.debug("Embedding filter score %.3f (threshold %.3f) for query: %s", best, threshold, query)
    return is_related, best


__all__ = ["is_cattle_related"]
