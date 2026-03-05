"""Pipeline orchestrator — runs parse → search → rank, yielding SSE events at each stage.

Handles both conversational input (greetings, questions) and real symptom descriptions.
"""

import json
import logging
from typing import AsyncGenerator, Any

from app.services.ai_client import get_ai_client
from app.services.llm_parser import parse_symptoms
from app.services.command_aggregator import (
    summarize_command_results,
    get_mock_query_results,
)
from app.services.llm_ranker import rank_commands

logger = logging.getLogger(__name__)

# Keywords that suggest this is a real symptom description, not casual chat
SYMPTOM_INDICATORS = {
    "mce", "bank", "error", "fail", "crash", "bsod", "ecc", "uncorrectable",
    "correctable", "fatal", "thermal", "stress", "umc", "memory", "cache",
    "l2", "l3", "fabric", "boot", "post", "hang", "timeout", "mprime",
    "linpack", "stream", "memtest", "core", "cpu", "voltage", "droop",
    "frequency", "clock", "parity", "afhc", "anc", "sdc", "0x",
    "debug", "diagnose", "workload", "bandwidth", "latency", "intermittent",
    "reproducible", "poison", "degrade", "exception", "miscompare",
}


def _is_symptom_description(text: str) -> bool:
    """Heuristic: does the text look like a CPU failure symptom description?"""
    lower = text.lower()
    # Short messages are unlikely to be symptoms
    if len(lower.split()) < 3:
        return False
    # Check for symptom-related keywords
    matches = sum(1 for kw in SYMPTOM_INDICATORS if kw in lower)
    return matches >= 1


def _format_sse(event_type: str, data: Any) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


async def run_pipeline(
    text: str,
    conversation_id: str,
    images: list | None = None,
) -> AsyncGenerator[str, None]:
    """
    Execute the full prediction pipeline, yielding SSE events:

    1. parsing_started → parsing_complete
    2. search_started → search_complete
    3. ranking_started → prediction
    4. done

    For conversational (non-symptom) input, uses the LLM to generate a
    helpful response instead of running the full pipeline.
    """

    # --- Check if this is a real symptom or conversational input ---
    if not _is_symptom_description(text):
        yield _format_sse("conversational", {"status": "generating"})

        try:
            client = get_ai_client()
            response = await client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a silicon debug assistant for AMD CPU failure analysis. "
                            "You help engineers diagnose CPU failures using AFHC/ANC debug commands. "
                            "If the user is making casual conversation or asking a question, "
                            "respond helpfully and briefly. Suggest they describe CPU failure "
                            "symptoms for analysis if appropriate. Keep responses concise."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0.7,
            )
            yield _format_sse("chat_response", {"message": response})
        except Exception as e:
            logger.error("Conversational LLM call failed: %s", e)
            yield _format_sse("chat_response", {
                "message": "I'm your silicon debug assistant. Describe CPU failure symptoms "
                "(MCE errors, thermal conditions, boot stage, etc.) and I'll recommend "
                "the best AFHC/ANC debug commands to run."
            })

        yield _format_sse("done", {})
        return

    # --- Stage 1: Parse symptoms ---
    yield _format_sse("parsing_started", {"status": "Analyzing failure symptoms..."})

    try:
        parsed_profile = await parse_symptoms(text)
    except Exception as e:
        logger.error("Parsing failed: %s", e)
        yield _format_sse("error", {"message": f"Failed to parse symptoms: {e}"})
        yield _format_sse("done", {})
        return

    yield _format_sse("parsing_complete", parsed_profile)

    # --- Stage 2: Search for similar parts ---
    yield _format_sse("search_started", {"status": "Searching for similar failed parts..."})

    failure_type = parsed_profile.get("failure_type", "UNKNOWN")

    # TODO: Replace with real Snowflake queries when connected
    try:
        query_results, tier, tier_description = get_mock_query_results(failure_type)
        command_summary = summarize_command_results(query_results)
    except Exception as e:
        logger.error("Search/aggregation failed: %s", e)
        yield _format_sse("error", {"message": f"Failed to search similar parts: {e}"})
        yield _format_sse("done", {})
        return

    yield _format_sse("search_complete", {
        "tier": tier,
        "count": command_summary["total_similar_parts"],
        "num_commands": len(command_summary["commands"]),
    })

    # --- Stage 3: Rank commands ---
    yield _format_sse("ranking_started", {"status": "Ranking debug commands..."})

    try:
        ranking = await rank_commands(
            parsed_profile=parsed_profile,
            command_summary=command_summary,
            tier=tier,
            tier_description=tier_description,
        )
    except Exception as e:
        logger.error("Ranking failed: %s", e)
        yield _format_sse("error", {"message": f"Failed to rank commands: {e}"})
        yield _format_sse("done", {})
        return

    # Build the full prediction payload
    prediction = {
        "analysis": {
            "parsed_profile": parsed_profile,
            "match_tier": tier,
            "similar_parts_count": command_summary["total_similar_parts"],
            **ranking["analysis"],
        },
        "commands": ranking["recommendations"],
        "caveats": [ranking.get("caveats", "")] if ranking.get("caveats") else [],
        "fallback_suggestion": ranking.get("fallback_suggestion", ""),
    }

    yield _format_sse("prediction", prediction)
    yield _format_sse("done", {})
