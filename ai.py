"""
All the AI-related code lives here: choosing a provider, building the
prompt, calling the API, and turning the raw response into a Python
dictionary the rest of the app can trust.

Keeping this separate from app.py means the Streamlit UI doesn't need to
know anything about prompts, providers, or JSON parsing - it just calls
analyze_inquiry() and gets back a clean, validated result.

WHY THERE ARE TWO PROVIDERS
---------------------------
Google's Gemini API is "OpenAI-compatible", meaning it accepts requests
in the same shape the OpenAI library sends. So the same `openai` Python
package can talk to either service - you only change the API key, the
base URL, and the model name.

That's genuinely useful beyond just saving money: being able to swap the
model behind a feature without rewriting the feature is a normal thing to
want in real software. Gemini is the default here because its free tier
doesn't require a credit card.
"""

import json
import os
import re

from openai import OpenAI

from constants import CATEGORIES, PRIORITIES, SENTIMENTS, DEPARTMENTS

# Each provider needs three things: where to send the request, which
# environment variable holds the key, and which model to ask for.
PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        # Fast, cheap, and included in the free tier. Google retires older
        # model names over time - if you get a 404 saying the model is no
        # longer available, the error message names the replacement, and
        # this line is the only place you need to change it.
        "model": "gemini-3.6-flash",
        "signup_url": "https://aistudio.google.com/apikey",
    },
    "openai": {
        "label": "OpenAI",
        "key_env": "OPENAI_API_KEY",
        # None means "use the library's normal OpenAI address".
        "base_url": None,
        "model": "gpt-5-nano",
        "signup_url": "https://platform.openai.com/api-keys",
    },
}

# Set AI_PROVIDER=openai in your environment to switch. Defaults to Gemini.
DEFAULT_PROVIDER = "gemini"

# The exact fields we expect back from the AI every time. Keeping this as
# one list means the prompt and the validation step can't drift apart.
RESULT_FIELDS = [
    "category",
    "priority",
    "customer_name",
    "order_number",
    "sentiment",
    "customer_request",
    "recommended_next_step",
    "suggested_department",
    "suggested_response",
]


class InquiryAnalysisError(Exception):
    """Raised when the AI's response can't be turned into a usable result."""


def get_provider() -> dict:
    """Return the settings for whichever provider is currently selected."""
    name = os.getenv("AI_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    if name not in PROVIDERS:
        valid = ", ".join(PROVIDERS)
        raise InquiryAnalysisError(
            f'AI_PROVIDER is set to "{name}", which isn\'t one of: {valid}'
        )
    return PROVIDERS[name]


def get_api_key(key_env: str):
    """Read the key from Streamlit secrets first, then the environment.

    Streamlit is imported here (not at the top of the file) so this
    module can still be imported and tested without Streamlit installed.
    """
    try:
        import streamlit as st
        return st.secrets[key_env]
    except Exception:
        return os.getenv(key_env)


def build_prompt(message: str) -> str:
    return f"""
You are an operations assistant for a small business.

Analyze the customer inquiry below and return ONLY valid JSON.
Do not include markdown, commentary, or code fences.

Use exactly these keys:
{{
  "category": "",
  "priority": "",
  "customer_name": "",
  "order_number": "",
  "sentiment": "",
  "customer_request": "",
  "recommended_next_step": "",
  "suggested_department": "",
  "suggested_response": ""
}}

Rules:
- category must be one of: {", ".join(CATEGORIES)}
- priority must be one of: {", ".join(PRIORITIES)}
- sentiment must be one of: {", ".join(SENTIMENTS)}
- suggested_department must be one of: {", ".join(DEPARTMENTS)}
- If customer_name or order_number is unknown, use "Not provided"
- Keep customer_request and recommended_next_step concise
- suggested_response should sound warm, professional, and human
- Do not promise a refund, replacement, delivery date, or policy exception unless the customer message already confirms it
- Never invent details the customer did not provide

CUSTOMER INQUIRY:
{message}
""".strip()


def extract_json(text: str) -> dict:
    """Parse JSON even if the model wraps it in a markdown code fence."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def validate_result(result: dict) -> dict:
    """
    Make sure every field exists and every constrained field (category,
    priority, sentiment, department) is one of our approved values.

    The AI is good at understanding messy language, but it can still
    return a value we don't recognize - a typo, a slightly different
    wording, a made-up category. Rather than trusting it blindly, we
    fall back to a safe default and let the human reviewer fix it before
    it's approved.
    """
    clean = {}

    for field in RESULT_FIELDS:
        clean[field] = str(result.get(field, "")).strip()

    if clean["category"] not in CATEGORIES:
        clean["category"] = "Other"

    if clean["priority"] not in PRIORITIES:
        clean["priority"] = "Medium"

    if clean["sentiment"] not in SENTIMENTS:
        clean["sentiment"] = "Neutral"

    if clean["suggested_department"] not in DEPARTMENTS:
        clean["suggested_department"] = "Customer Support"

    if not clean["customer_name"]:
        clean["customer_name"] = "Not provided"

    if not clean["order_number"]:
        clean["order_number"] = "Not provided"

    return clean


def describe_error(exc: Exception, provider: dict) -> str:
    """
    Turn a raw API error into something a person can act on.

    The library raises the same kind of exception for very different
    problems, so we look at the text of the message to tell them apart
    and suggest the actual fix.
    """
    text = str(exc)

    if "insufficient_quota" in text or "exceeded your current quota" in text:
        return (
            f"{provider['label']} says this account is out of credit. "
            f"Add billing credit, or switch providers by setting AI_PROVIDER."
        )

    # Providers disagree on the status code for a bad key - OpenAI returns
    # 401, Google returns 400 - so match on the wording too.
    key_problems = (
        "401",
        "api key not valid",
        "pass a valid api key",
        "invalid_api_key",
        "api_key_invalid",
    )
    if any(phrase in text.lower() for phrase in key_problems):
        return (
            f"{provider['label']} rejected the API key. Check that "
            f"{provider['key_env']} holds your real key - if you pasted a "
            "placeholder, or opened a new terminal since setting it, that's "
            f"the cause. You can create a key at {provider['signup_url']}"
        )

    if "429" in text:
        return (
            f"{provider['label']} is rate limiting this key - too many requests "
            "in a short window. Wait a moment and try again."
        )

    lowered = text.lower()
    if "model" in lowered and (
        "not found" in lowered or "not_found" in lowered or "no longer available" in lowered
    ):
        return (
            f"{provider['label']} won't serve the model \"{provider['model']}\" - "
            "it has probably been retired. Update the model name in ai.py. "
            f"Provider said: {exc}"
        )

    return f"The AI request failed: {exc}"


def analyze_inquiry(message: str) -> dict:
    """
    Send a customer message to the configured AI provider and return a
    validated dictionary.

    Raises InquiryAnalysisError with a plain-English message if anything
    goes wrong, so the UI only ever has to catch one exception type.
    """
    provider = get_provider()

    api_key = get_api_key(provider["key_env"])
    if not api_key:
        raise InquiryAnalysisError(
            f"No {provider['label']} API key was found. Set {provider['key_env']} "
            f"in your environment or Streamlit secrets, then restart the app. "
            f"You can create a free key at {provider['signup_url']}"
        )

    # base_url=None makes the library use its normal OpenAI address.
    client = OpenAI(api_key=api_key, base_url=provider["base_url"])

    try:
        response = client.chat.completions.create(
            model=provider["model"],
            messages=[{"role": "user", "content": build_prompt(message)}],
        )
    except Exception as exc:
        raise InquiryAnalysisError(describe_error(exc, provider)) from exc

    output_text = response.choices[0].message.content

    if not output_text:
        raise InquiryAnalysisError(
            "The AI returned an empty response. Please try again."
        )

    try:
        raw_result = extract_json(output_text)
    except json.JSONDecodeError as exc:
        raise InquiryAnalysisError(
            "The AI response wasn't valid JSON. Please try again."
        ) from exc

    return validate_result(raw_result)
