"""LLM Parser — converts symptom text into a structured failure profile using GPT-4."""

import logging
from typing import Any

from app.services.ai_client import get_ai_client
from app.prompts.parsing import PARSING_SYSTEM_PROMPT, build_parsing_user_prompt

logger = logging.getLogger(__name__)

# Fields that must exist in the parsed profile (with defaults)
PROFILE_FIELDS = {
    "failure_type": "UNKNOWN",
    "mce_bank": None,
    "mce_code": None,
    "mce_code_family": None,
    "error_severity": None,
    "thermal_state": None,
    "voltage_state": None,
    "boot_stage": None,
    "frequency_context": None,
    "failing_cores": None,
    "raw_defect_type": None,
    "keywords": [],
    "confidence": 0.0,
    "reasoning": "",
}

VALID_FAILURE_TYPES = {
    "UMC_MEMORY_CONTROLLER", "EXECUTION_UNIT", "FLOATING_POINT",
    "LOAD_STORE", "INSTRUCTION_FETCH", "COMBINED_UNIT",
    "L2_CACHE", "L3_CACHE", "FABRIC_INTERCONNECT",
    "POWER_MANAGEMENT", "BOOT_FAILURE", "UNKNOWN",
}


def _sanitize_profile(raw: dict) -> dict[str, Any]:
    """Ensure all expected fields exist and values are within range."""
    profile = {}
    for key, default in PROFILE_FIELDS.items():
        profile[key] = raw.get(key, default)

    # Validate failure_type
    if profile["failure_type"] not in VALID_FAILURE_TYPES:
        profile["failure_type"] = "UNKNOWN"

    # Clamp confidence
    try:
        profile["confidence"] = max(0.0, min(1.0, float(profile["confidence"])))
    except (TypeError, ValueError):
        profile["confidence"] = 0.0

    # Ensure keywords is a list
    if not isinstance(profile["keywords"], list):
        profile["keywords"] = []

    return profile


def merge_parsed_and_structured(llm_output: dict, user_fields: dict | None) -> dict:
    """User-provided structured fields take priority over LLM extraction."""
    if not user_fields:
        return llm_output
    merged = llm_output.copy()
    for key, value in user_fields.items():
        if value is not None and value != "":
            merged[key] = value
    return merged


async def parse_symptoms(
    symptom_text: str,
    structured_fields: dict | None = None,
) -> dict[str, Any]:
    """
    Parse engineer-written symptom text into a structured failure profile.

    Returns a validated dict with all PROFILE_FIELDS populated.
    """
    client = get_ai_client()

    messages = [
        {"role": "system", "content": PARSING_SYSTEM_PROMPT},
        {"role": "user", "content": build_parsing_user_prompt(symptom_text, structured_fields)},
    ]

    logger.info("Parsing symptoms: %s", symptom_text[:120])
    raw = await client.chat_json(messages, temperature=0.2)

    profile = _sanitize_profile(raw)
    profile = merge_parsed_and_structured(profile, structured_fields)

    logger.info(
        "Parsed profile: type=%s bank=%s confidence=%.2f",
        profile["failure_type"],
        profile["mce_bank"],
        profile["confidence"],
    )
    return profile
