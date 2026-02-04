# qtrace-pro/gemini_explainer.py — Gemini API Integration

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Optional dependency - best-effort import
try:
    import google.generativeai as genai  # type: ignore
    GENAI_INSTALLED = True
except Exception:
    genai = None
    GENAI_INSTALLED = False

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
_genai_configured = False


def _configure_genai_once():
    global _genai_configured
    if _genai_configured or not GENAI_INSTALLED or not GOOGLE_API_KEY:
        return
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        _genai_configured = True
        logger.debug("Configured Gemini client")
    except Exception as e:
        logger.debug("Failed to configure Gemini client: %s", e)


def _local_fallback_explanation(score: float, pattern: str, code_snippet: str) -> str:
    severity = "high" if score >= 0.7 else "medium" if score >= 0.4 else "low"
    return (
        f"Detected pattern: {pattern}. Risk score ~{score:.2f} ({severity}). "
        f"This pattern indicates a potential quantum-native construct (e.g., probabilistic triggers or chained logic). "
        f"Review the snippet for hidden triggers or chained checks; add instrumentation and tests. "
        f"Snippet preview:\n{code_snippet.strip()[:400]}"
    )


def explain_result(score: float, pattern: str, code_snippet: str) -> str:
    """
    Return a concise explanation. Uses Gemini when available/configured; otherwise fallback.
    """
    if GENAI_INSTALLED and GOOGLE_API_KEY:
        _configure_genai_once()
        try:
            model = genai.GenerativeModel("gemini-1.5-flash-latest")
            prompt = f"""
You are a cybersecurity expert analyzing 'Quantum-Native' threats in Python code.
Briefly (4-8 sentences) explain the risk of the following code snippet.
Focus on the probabilistic/quantum nature of the logic.

Pattern Detected: {pattern}
Calculated Risk Score: {score:.2f}

Code Snippet:
{code_snippet}
"""
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.debug("Gemini call failed: %s", e)
            return f"[Gemini error: {str(e)}] " + _local_fallback_explanation(score, pattern, code_snippet)

    if not GENAI_INSTALLED:
        logger.debug("Gemini client not installed; using local fallback explanation")
    elif not GOOGLE_API_KEY:
        logger.debug("GOOGLE_API_KEY not set; using local fallback explanation")

    return _local_fallback_explanation(score, pattern, code_snippet)


# Safe demo
if __name__ == "__main__":
    print(explain_result(0.93, "PROBABILISTIC_BOMB", 'if random.random() < 0.12: print("demo")'))
