"""Two-tier content guardrail for IdeaForge.

Tier 1 — Keyword filter   : instant, zero API cost, catches obvious violations.
Tier 2 — Groq LLM check   : semantic understanding for nuanced cases.

If the Groq call fails for any reason (network, quota, etc.) the guardrail
defaults to SAFE so a transient API issue never blocks the entire pipeline.
The failure is logged as a warning so it can be investigated.
"""

import re
import structlog

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from ideaforge.guardrails.schemas import GuardrailResult, ViolationCategory

logger = structlog.get_logger(__name__)

# ── Tier 1: keyword patterns ──────────────────────────────────────────────────
# Intentionally broad — the LLM handles edge cases.
# Each entry: (compiled_regex, ViolationCategory)
_KEYWORD_RULES: list[tuple[re.Pattern, ViolationCategory]] = [
    (
        re.compile(
            r"\b(n[i1]gg[ae]r|ch[i1]nk|sp[i1]c|k[i1]ke|f[a@]gg[o0]t|tr[a@]nny)\b",
            re.IGNORECASE,
        ),
        ViolationCategory.HATE_SPEECH,
    ),
    (
        re.compile(
            r"\b(sell\s+drugs?|drug\s+deal|meth\s+lab|dark\s+web\s+market|"
            r"illegal\s+weapons?|gun\s+running|human\s+trafficking|hire\s+hitman)\b",
            re.IGNORECASE,
        ),
        ViolationCategory.ILLEGAL_ACTIVITY,
    ),
    (
        re.compile(
            r"\b(pyramid\s+scheme|ponzi|mlm\s+recruit|multi.?level\s+marketing\s+downline)\b",
            re.IGNORECASE,
        ),
        ViolationCategory.SCAM,
    ),
    (
        re.compile(
            r"\b(porn|pornograph|onlyfans|adult\s+content\s+platform|"
            r"lingerie|boudoir|nude\s+photo|nudity|xxx|erotic\s+content|"
            r"strip\s+club|camgirl|cam\s+girl|sexting)\b",
            re.IGNORECASE,
        ),
        ViolationCategory.EXPLICIT,
    ),
    # Compound pattern: intimate clothing + fan monetization
    # Catches "night wear/bikini/costumes + fans + donations/tips/subscribe"
    (
        re.compile(
            r"\b(nightwear|night\s+wear|bikini|swimwear|underwear|intimate\s+wear|outfit|costume)\b"
            r".{0,150}"
            r"\b(fans?|subscribers?|followers?|audience)\b"
            r".{0,150}"
            r"\b(donat|tip|pay|subscri|appreciat|monetiz|earn|income)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        ViolationCategory.EXPLICIT,
    ),
]

# ── Tier 2: LLM prompt ────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are a content moderator for a professional startup idea platform used by students and founders.

Many users use vague, indirect, or innocent-sounding language to disguise inappropriate ideas. Your job is to detect not just explicit violations but also ideas that are ambiguous or could hide adult content, scams, or other harm — and explain clearly to the user what is wrong or what they need to clarify.

━━━ HOW TO REASON ━━━
Step 1: In one sentence, state what this business ACTUALLY does or sells (ignore the framing, look at the model).
Step 2: Classify using the rules below.
Step 3: Write a reason that will be shown directly to the user — be specific and actionable.

━━━ CLASSIFICATION RULES ━━━

── AMBIGUOUS (safe = false) ──
Use this when the idea involves a payment or donation relationship between an individual and their fans/followers/subscribers, but the specific content, service, or product being paid for is NOT clearly stated.
Trigger conditions (any one is enough):
• "creator / individual / person" + "fans / followers / subscribers" + "donate / tip / appreciate / support / pay" — but no clear statement of what fans receive
• "exclusive content" or "personal content" from one person to paying fans without specifying the content type
• Any vague "appreciation" or "support" model where the recipient is a specific person and the value exchange is unstated

The reason field MUST ask the user exactly what is missing. Template:
"Your idea mentions [fans/donors/subscribers] giving [money/donations/tips] to [creator/individual] but does not specify what they receive in return or what content/service is being offered. This pattern is associated with adult content platforms when the purpose is left unstated. Please clarify: (1) What exactly do [fans/subscribers] receive for their payment? (2) What specific content or service does the creator provide?"

── EXPLICIT (safe = false) ──
Use this when the business is clearly an adult content platform — even when disguised with indirect language.
Trigger conditions:
• Creator + fans + payment + any intimate element: outfits / nightwear / sleepwear / lingerie / bikini / swimwear / underwear / costumes / body / intimate / sensual / boudoir / try-on
• "Try-on hauls", "costume showcases", or "outfit reveals" that fans pay/donate/tip for
• Subscription or donation platform where an individual shares photos/videos of themselves in various clothing states
• Any model where people pay to watch another person in clothing, undressing, or intimate scenarios

The reason field MUST explain the specific element that triggered the block:
"Your idea describes [specific pattern found, e.g. 'an individual sharing costume and nightwear content with fans who donate']. This is the structure of an adult content platform regardless of the vocabulary used. If this is not your intent, please describe the specific non-intimate content being created and the clear business purpose."

── SCAM (safe = false) ──
Trigger conditions:
• Earning model that requires recruiting new paying participants (pyramid/MLM) regardless of product
• "Passive income" combined with "recruit / refer / build your network / downline / invite others"
• Returns promised without a real product or service backing them

The reason field MUST name the specific scam pattern:
"Your idea describes [specific pattern, e.g. 'a revenue model where participants earn by recruiting new paying members']. This is the structure of a pyramid scheme / MLM regardless of what product or service is mentioned."

── ILLEGAL_ACTIVITY (safe = false) ──
Trigger conditions:
• Drug markets using euphemisms: "herbal products", "recreational substances", "botanicals", "specialty goods", "420-friendly", "discreet delivery"
• Weapons without explicit legal compliance language
• Financial services designed to avoid reporting thresholds ("below the threshold", "no paperwork", "minimal documentation" for money transfers)
• Hacking tools even framed as security research: "phishing kit", "credential harvester", "exploit generator"

The reason field MUST name the specific illegal activity.

── HARMFUL (safe = false) ──
Trigger conditions: doxxing tools, stalking services, mass surveillance of individuals, targeted harassment enablement.

── HATE_SPEECH (safe = false) ──
Trigger conditions: slurs, discrimination, content targeting ethnic/gender/religious groups.

── SAFE (safe = true) ──
Mark safe when:
• Clear legitimate business with a specific, stated product or service
• Fan-support platform with clearly non-intimate content (music, writing, gaming, art, podcasts)
• Clothing/fashion e-commerce where the business sells garments — not the creator's body
• Fitness/wellness platforms where content is exercise instruction, not intimate display
• Regulated industries (cannabis, firearms) with explicit compliance emphasis
• Edgy, controversial, or disruptive ideas that are clearly legal and described

━━━ OUTPUT FORMAT ━━━
Respond ONLY with valid JSON:
{{
  "safe": true | false,
  "category": "SAFE" | "AMBIGUOUS" | "EXPLICIT" | "SCAM" | "ILLEGAL_ACTIVITY" | "HARMFUL" | "DEROGATORY" | "HATE_SPEECH",
  "reason": "Empty string if safe=true. If safe=false: a clear, user-facing message explaining exactly what is wrong and what (if anything) the user should clarify or change."
}}"""

_HUMAN_PROMPT = "Analyze this startup idea:\n\n{text}"

_PROMPT = ChatPromptTemplate.from_messages(
    [("system", _SYSTEM_PROMPT), ("human", _HUMAN_PROMPT)]
)


class ContentGuard:
    """Stateless content guardrail. Instantiate once per application startup."""

    def __init__(self, api_key: str, model: str) -> None:
        _llm = ChatGroq(api_key=api_key, model=model, temperature=0)
        self._chain = _PROMPT | _llm.with_structured_output(GuardrailResult)

    # ── Public API ────────────────────────────────────────────────────────────

    async def check(self, text: str) -> GuardrailResult:
        """Run both tiers and return the combined result.

        Args:
            text: Raw user-supplied text (problem statement or generated idea).

        Returns:
            GuardrailResult with safe=True if content passes, safe=False otherwise.
        """
        text = text.strip()
        if not text:
            return GuardrailResult(safe=False, category=ViolationCategory.HARMFUL, reason="Empty input")

        # Tier 1 — instant keyword check
        keyword_result = self._keyword_check(text)
        if keyword_result is not None:
            logger.warning("guardrail.keyword_block", category=keyword_result.category)
            return keyword_result

        # Tier 2 — LLM semantic check
        return await self._llm_check(text)

    def check_sync(self, text: str) -> GuardrailResult:
        """Synchronous keyword-only check (no LLM call).

        Use this only in contexts where async is not available.
        The LLM tier is skipped so nuanced violations may pass through.
        """
        text = text.strip()
        if not text:
            return GuardrailResult(safe=False, category=ViolationCategory.HARMFUL, reason="Empty input")
        result = self._keyword_check(text)
        return result or GuardrailResult(safe=True)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _keyword_check(self, text: str) -> GuardrailResult | None:
        """Return a violation result if a keyword pattern matches, else None."""
        for pattern, category in _KEYWORD_RULES:
            if pattern.search(text):
                return GuardrailResult(
                    safe=False,
                    category=category,
                    reason=f"Content matched a blocked pattern for category: {category.value}",
                )
        return None

    async def _llm_check(self, text: str) -> GuardrailResult:
        """Call Groq to perform semantic content moderation.

        On any failure (network, quota, parsing) returns SAFE with a warning
        so a transient Groq outage never blocks the user pipeline.
        """
        try:
            result: GuardrailResult = await self._chain.ainvoke({"text": text})
            if not result.safe:
                logger.warning(
                    "guardrail.llm_block",
                    category=result.category,
                    reason=result.reason,
                )
            return result
        except Exception as exc:
            logger.warning("guardrail.llm_error", error=str(exc))
            # Fail open: do not block users when Groq is unavailable
            return GuardrailResult(safe=True, reason="Guardrail LLM unavailable — passed through")
