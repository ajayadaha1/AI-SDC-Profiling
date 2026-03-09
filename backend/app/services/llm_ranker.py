"""LLM Ranker — ranks commands using GPT-4 based on failure profile and historical data."""

import json
import logging
from typing import Any

from app.services.ai_client import get_ai_client
from app.prompts.ranking import RANKING_SYSTEM_PROMPT, build_ranking_user_prompt

logger = logging.getLogger(__name__)


def _sanitize_ranking(raw: dict) -> dict[str, Any]:
    """Ensure the ranking output has the expected structure."""
    result: dict[str, Any] = {}

    # Analysis section
    analysis = raw.get("analysis", {})
    result["analysis"] = {
        "total_similar_parts": analysis.get("total_similar_parts", 0),
        "match_quality": analysis.get("match_quality", "weak"),
        "match_tier": analysis.get("match_tier", 1),
        "dominant_failure_pattern": analysis.get("dominant_failure_pattern", ""),
    }

    # Recommendations
    recs = raw.get("recommendations", [])
    result["recommendations"] = []
    for i, rec in enumerate(recs[:5]):  # cap at 5
        result["recommendations"].append({
            "rank": rec.get("rank", i + 1),
            "command": rec.get("command", ""),
            "confidence": max(0.0, min(1.0, float(rec.get("confidence", 0.0)))),
            "fail_rate_on_similar": rec.get("fail_rate_on_similar", "N/A"),
            "estimated_time_to_fail": rec.get("estimated_time_to_fail", "unknown"),
            "reasoning": rec.get("reasoning", ""),
        })

    result["fallback_suggestion"] = raw.get("fallback_suggestion", "Run full AFHC suite if all recommended commands pass.")
    result["caveats"] = raw.get("caveats", "")

    return result


async def rank_commands(
    parsed_profile: dict,
    command_summary: dict,
    tier: int,
    tier_description: str,
) -> dict[str, Any]:
    """
    Use GPT-4 to rank commands based on failure profile and historical data.

    Args:
        parsed_profile: Structured failure profile from llm_parser.
        command_summary: Output of summarize_command_results().
        tier: Which query tier matched (1, 2, or 3).
        tier_description: Human-readable tier description.

    Returns:
        Validated ranking result dict.
    """
    client = get_ai_client()

    # Format the profile as JSON for the prompt
    profile_json = json.dumps(parsed_profile, indent=2)

    # Format command table — convert sets to counts for serialization
    from app.services.command_aggregator import format_command_table
    table_str = format_command_table(command_summary)

    num_parts = command_summary.get("total_records", 0)

    messages = [
        {"role": "system", "content": RANKING_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_ranking_user_prompt(
                profile_json, num_parts, tier_description, table_str,
            ),
        },
    ]

    logger.info(
        "Ranking commands: %d parts, tier %d, %d commands",
        num_parts, tier, len(command_summary.get("commands", [])),
    )

    raw = await client.chat_json(messages, temperature=0.2)
    result = _sanitize_ranking(raw)

    # Inject tier info into analysis
    result["analysis"]["match_tier"] = tier
    result["analysis"]["total_similar_parts"] = num_parts

    logger.info(
        "Ranking complete: %d recommendations, top confidence=%.2f",
        len(result["recommendations"]),
        result["recommendations"][0]["confidence"] if result["recommendations"] else 0,
    )

    return result
