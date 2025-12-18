# Chatbot Configuration

The chatbot forwards every farmer question to Groq's Chat Completions API.

## Environment variables

Set the following variables (for example in a `.env` file) before starting Django:

```
CHATBOT_API_KEY="gsk_..."
CHATBOT_MODEL="llama-3.1-8b-instant"
# Optional: provide a Hugging Face token if the model requires authentication
HUGGINGFACE_API_TOKEN="hf_..."
```

`CHATBOT_API_URL` is optional; if you omit it, the backend will call Groq's standard chat-completions endpoint (`https://api.groq.com/openai/v1/chat/completions`).

If `CHATBOT_MODEL` is omitted, the backend will default to `llama-3.1-8b-instant`. Update this if Groq recommends a different model in the future.

`CHATBOT_EMBED_MODEL` controls the semantic filter (defaults to `all-MiniLM-L6-v2`). Adjust `ALLOWED_SIMILARITY` (default 0.65) to tighten or loosen the cattle-domain guard.

Responses are post-processed to add light structuring (bullet lists) for readability before returning to the UI. This happens server-side in `chatbot/views.py`.

> **Heads up:** Groq retired older names such as `llama3-70b-8192`, `llama-3.1-70b-versatile`, and `mixtral-8x7b-32768`. The backend now auto-upgrades those aliases to `llama-3.1-8b-instant`, but you should still update your environment variable to avoid warnings.

## Domain guard

All incoming messages are still validated to ensure they relate to cattle/dairy topics. Non-cattle queries receive a friendly reminder instead of being sent to Groq. You can tune this behaviour in `chatbot/views.py` (`CATTLE_KEYWORDS`).

## Error handling

If the Groq request fails (invalid credentials, unsupported model, network issue), the API responds with `{"ok": false, "error": "model_error"}` so the front end can display an appropriate message.
