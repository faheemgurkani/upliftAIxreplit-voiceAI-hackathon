"""Compatibility shim — engines import get_groq_service; implementation is OpenRouter-first."""

from app.services.llm_chat_service import (  # noqa: F401
    GroqService,
    LLMChatService,
    get_groq_service,
    get_llm_chat_service,
)
