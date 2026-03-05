"""Command Aggregator — summarizes raw query results into a command stats table.

Until Snowflake is connected, provides mock data for testing.
"""

import logging
from typing import Any

from app.prompts.taxonomy import get_banks_for_failure_type

logger = logging.getLogger(__name__)


def summarize_command_results(query_results: list[dict]) -> dict[str, Any]:
    """
    Aggregate raw (cpu, command, result) rows into a command-level summary.
    This is what we send to the LLM for ranking.
    """
    similar_cpus: set[str] = set()
    command_stats: dict[str, dict] = {}

    for row in query_results:
        cpu_id = row.get("cpu_id", row.get("CPU_ID", ""))
        similar_cpus.add(cpu_id)

        cmd = row.get("command", row.get("COMMAND", ""))
        if not cmd:
            continue

        if cmd not in command_stats:
            command_stats[cmd] = {
                "command": cmd,
                "total_runs": 0,
                "fail_count": 0,
                "pass_count": 0,
                "fail_rate": 0.0,
                "cpus_failed_on": set(),
                "cpus_passed_on": set(),
                "common_fail_signatures": [],
                "thermal_at_failure": [],
            }

        stats = command_stats[cmd]
        stats["total_runs"] += 1

        result = row.get("result", row.get("RESULT", ""))
        if result == "FAIL":
            stats["fail_count"] += 1
            stats["cpus_failed_on"].add(cpu_id)
            sig = row.get("fail_signature", row.get("FAIL_SIGNATURE"))
            if sig:
                stats["common_fail_signatures"].append(sig)
            thermal = row.get("thermal_state", row.get("THERMAL_STATE"))
            if thermal:
                stats["thermal_at_failure"].append(thermal)
        else:
            stats["pass_count"] += 1
            stats["cpus_passed_on"].add(cpu_id)

        stats["fail_rate"] = stats["fail_count"] / stats["total_runs"] if stats["total_runs"] > 0 else 0.0

    # Sort by fail rate descending
    sorted_commands = sorted(command_stats.values(), key=lambda x: x["fail_rate"], reverse=True)

    return {
        "total_similar_parts": len(similar_cpus),
        "commands": sorted_commands,
    }


def format_command_table(summary: dict) -> str:
    """Format the command summary into a text table for the LLM prompt."""
    lines = []
    for cmd in summary["commands"]:
        parts_failed = len(cmd["cpus_failed_on"]) if isinstance(cmd["cpus_failed_on"], set) else cmd["cpus_failed_on"]
        line = (
            f"{cmd['command']:<30} | {cmd['total_runs']:>10} | "
            f"{cmd['fail_count']:>5} | {cmd['fail_rate']:>8.1%} | {parts_failed}"
        )
        lines.append(line)
    return "\n".join(lines) if lines else "(no command data available)"


# ---------------------------------------------------------------------------
# Mock data for testing until Snowflake is connected
# ---------------------------------------------------------------------------

MOCK_COMMAND_DATA: dict[str, list[dict]] = {
    "UMC_MEMORY_CONTROLLER": [
        {"cpu_id": f"CPU-{i:03d}", "command": "stream -t mem_band_max -v 1.2",
         "result": "FAIL" if i < 21 else "PASS", "fail_signature": "UMC_BW_DEGRADE",
         "thermal_state": "hot"} for i in range(23)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "mprime -t L3_stress_umc",
         "result": "FAIL" if i < 18 else "PASS", "fail_signature": "MPRIME_UMC_ECC",
         "thermal_state": "hot"} for i in range(23)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "membw -p read_write -s 4G",
         "result": "FAIL" if i < 15 else "PASS", "fail_signature": "MEMBW_PATTERN_FAIL",
         "thermal_state": "warm"} for i in range(23)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "memtest86 -t 7 -p 2",
         "result": "FAIL" if i < 10 else "PASS", "fail_signature": "MT86_ADDR",
         "thermal_state": "ambient"} for i in range(23)
    ],
    "EXECUTION_UNIT": [
        {"cpu_id": f"CPU-{i:03d}", "command": "prime95 -t smallfft",
         "result": "FAIL" if i < 14 else "PASS", "fail_signature": "P95_ROUNDING",
         "thermal_state": "hot"} for i in range(18)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "ycruncher -t swi",
         "result": "FAIL" if i < 12 else "PASS", "fail_signature": "YC_MISCOMPARE",
         "thermal_state": "warm"} for i in range(18)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "linpack -t stress_int",
         "result": "FAIL" if i < 8 else "PASS", "fail_signature": "LP_ALU_ERR",
         "thermal_state": "ambient"} for i in range(18)
    ],
    "FLOATING_POINT": [
        {"cpu_id": f"CPU-{i:03d}", "command": "linpack -n 50000",
         "result": "FAIL" if i < 16 else "PASS", "fail_signature": "LP_FP_RESIDUAL",
         "thermal_state": "hot"} for i in range(20)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "prime95 -t largefft",
         "result": "FAIL" if i < 13 else "PASS", "fail_signature": "P95_FMA_ERR",
         "thermal_state": "warm"} for i in range(20)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "ycruncher -t bkt",
         "result": "FAIL" if i < 9 else "PASS", "fail_signature": "YC_FP_DIFF",
         "thermal_state": "ambient"} for i in range(20)
    ],
    "L3_CACHE": [
        {"cpu_id": f"CPU-{i:03d}", "command": "cache_test -L3 -p chase",
         "result": "FAIL" if i < 11 else "PASS", "fail_signature": "L3_TAG_PARITY",
         "thermal_state": "hot"} for i in range(15)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "stream -t l3_sweep",
         "result": "FAIL" if i < 9 else "PASS", "fail_signature": "L3_BW_DROP",
         "thermal_state": "warm"} for i in range(15)
    ] + [
        {"cpu_id": f"CPU-{i:03d}", "command": "mlc -t latency_matrix",
         "result": "FAIL" if i < 6 else "PASS", "fail_signature": "MLC_L3_LAT",
         "thermal_state": "ambient"} for i in range(15)
    ],
}

# Default mock for any failure type not explicitly listed
_DEFAULT_MOCK = [
    {"cpu_id": f"CPU-{i:03d}", "command": "stress-ng --cpu 16 --timeout 60",
     "result": "FAIL" if i < 7 else "PASS", "fail_signature": "STRESS_GENERAL",
     "thermal_state": "warm"} for i in range(12)
] + [
    {"cpu_id": f"CPU-{i:03d}", "command": "memtest86 -t all",
     "result": "FAIL" if i < 5 else "PASS", "fail_signature": "MT86_GENERAL",
     "thermal_state": "ambient"} for i in range(12)
]


def get_mock_query_results(failure_type: str) -> tuple[list[dict], int, str]:
    """
    Return (rows, tier, tier_description) mock data for a given failure type.
    Used until Snowflake is connected.
    """
    rows = MOCK_COMMAND_DATA.get(failure_type, _DEFAULT_MOCK)
    tier = 1
    desc = f"Tier 1: Mock data for {failure_type} (Snowflake not connected)"
    return rows, tier, desc
