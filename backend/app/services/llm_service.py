import asyncio
import logging
import re

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Task 7.3 — Fallback ad idea template
# ---------------------------------------------------------------------------

FALLBACK_AD_IDEA = (
    "Showcase {product_description} to your {niche} audience with authentic storytelling "
    "that highlights real-world benefits and drives genuine engagement."
)


def get_fallback_ad_idea(product_description: str, creator_niche: list[str]) -> str:
    """Return a formatted fallback ad idea string."""
    niche_str = ", ".join(creator_niche) if creator_niche else "general"
    return FALLBACK_AD_IDEA.format(
        product_description=product_description,
        niche=niche_str,
    )


# ---------------------------------------------------------------------------
# Task 7.4 — Input sanitization
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = re.compile(
    r"ignore previous instructions|system:|user:|assistant:",
    re.IGNORECASE,
)

_MAX_PROMPT_LEN = 500


def sanitize_for_prompt(text: str) -> str:
    """Sanitize user-provided text before LLM prompt interpolation.

    - Strips leading/trailing whitespace
    - Removes backticks, angle brackets, and curly braces
    - Removes common prompt-injection phrases
    - Truncates to 500 characters
    """
    text = text.strip()
    # Remove characters that could break prompt structure or enable injection
    for ch in ("`", "<", ">", "{", "}"):
        text = text.replace(ch, "")
    # Remove injection phrases
    text = _INJECTION_PATTERNS.sub("", text)
    return text[:_MAX_PROMPT_LEN]


# ---------------------------------------------------------------------------
# Task 7.1 — generate_ad_idea using LangChain + Groq
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE_STR = (
    "You are a creative advertising expert. "
    "Generate a compelling ad concept for a product described as: {product_description}. "
    "The creator specializes in: {niche}. "
    "Provide a concise, creative ad idea in 2-3 sentences."
)


def _get_langchain_deps():
    """Lazily import LangChain dependencies so the module loads without them installed."""
    from langchain_core.prompts import ChatPromptTemplate  # noqa: PLC0415
    from langchain_groq import ChatGroq  # noqa: PLC0415

    return ChatGroq, ChatPromptTemplate


async def generate_ad_idea(product_description: str, creator_niche: list[str]) -> str:
    """Generate an ad concept using Groq LLM via LangChain.

    - Sanitizes inputs before prompt interpolation (Task 7.4)
    - Wraps LLM call in a 30-second timeout (Task 7.2)
    - Retries up to 3 times with exponential backoff: 1s, 2s, 4s (Task 7.2)
    - Falls back to a template string if all attempts fail (Task 7.3)
    - Always returns a non-empty string
    """
    # Task 7.4 — sanitize inputs before prompt interpolation
    clean_product = sanitize_for_prompt(product_description)
    clean_niche_items = [sanitize_for_prompt(n) for n in creator_niche]
    niche_str = ", ".join(clean_niche_items) if clean_niche_items else "general"

    ChatGroq, ChatPromptTemplate = _get_langchain_deps()

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0.7,
    )
    prompt = ChatPromptTemplate.from_messages([
        ("human", _PROMPT_TEMPLATE_STR),
    ])
    chain = prompt | llm

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            # Task 7.2 — 30-second timeout per attempt
            response = await asyncio.wait_for(
                chain.ainvoke(
                    {"product_description": clean_product, "niche": niche_str}
                ),
                timeout=30.0,
            )
            return response.content
        except (asyncio.TimeoutError, Exception) as exc:
            delay = 2 ** attempt  # 1s, 2s, 4s
            logger.error(
                "generate_ad_idea attempt %d/%d failed: %s. Retrying in %ds.",
                attempt + 1,
                max_attempts,
                exc,
                delay,
            )
            if attempt < max_attempts - 1:
                await asyncio.sleep(delay)

    # Task 7.3 — fallback template after all attempts exhausted
    logger.warning("All LLM attempts exhausted; returning fallback ad idea.")
    return get_fallback_ad_idea(clean_product, clean_niche_items)
