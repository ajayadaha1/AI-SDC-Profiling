"""Command Aggregator — queries real Snowflake data and summarizes command stats.

Queries 4 data sources with tiered matching:
  - MSFT_MCEFAIL (largest, ~1M rows)
  - LEVEL3DEBUG_LOGFILES (~3.8M rows, banks stored as JSON arrays)
  - AURA_PMDATA (~49K rows, lab validation)
  - PRISM_PMDATA (~98K rows, lab validation)
"""

import logging
from typing import Any

from app.services.snowflake_service import execute_query

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bank name mapping: failure_type → bank values in each table
# ---------------------------------------------------------------------------

# MSFT_MCEFAIL uses clean scalar bank names
MCEFAIL_BANK_MAP: dict[str, list[str]] = {
    "UMC_MEMORY_CONTROLLER": ["UMC"],
    "LOAD_STORE": ["LS"],
    "L3_CACHE": ["L3"],
    "L2_CACHE": ["L2"],
    "EXECUTION_UNIT": ["EX"],
    "FLOATING_POINT": ["FP"],
    "INSTRUCTION_FETCH": ["IF"],
    "COMBINED_UNIT": ["CS", "CU"],
    "FABRIC_INTERCONNECT": ["PCS_GMI", "PCS_XGMI", "GMI"],
    "POWER_MANAGEMENT": ["PIE"],
    "BOOT_FAILURE": [],
}

# LEVEL3DEBUG_LOGFILES stores banks as JSON arrays like ['L3'], ['UMC', 'UMC']
# We use LIKE matching against the stringified array
L3DEBUG_BANK_PATTERNS: dict[str, list[str]] = {
    "UMC_MEMORY_CONTROLLER": ["%UMC%"],
    "LOAD_STORE": ["%LS%"],
    "L3_CACHE": ["%L3%"],
    "L2_CACHE": ["%L2%"],
    "EXECUTION_UNIT": ["%EX%"],
    "FLOATING_POINT": ["%FP%"],
    "INSTRUCTION_FETCH": ["%IF%"],
    "COMBINED_UNIT": ["%CS%", "%CU%"],
    "FABRIC_INTERCONNECT": ["%GMI%", "%17%", "%18%"],
    "POWER_MANAGEMENT": ["%PIE%", "%30%", "%22%"],
    "BOOT_FAILURE": [],
}

# AURA/PRISM use DEFECT_TYPE as the bank-like key
DEFECT_TYPE_MAP: dict[str, list[str]] = {
    "UMC_MEMORY_CONTROLLER": ["UMC"],
    "LOAD_STORE": ["LS"],
    "L3_CACHE": ["L3"],
    "L2_CACHE": ["L2"],
    "EXECUTION_UNIT": ["EX"],
    "FLOATING_POINT": ["FP"],
    "INSTRUCTION_FETCH": ["IF", "DE"],
    "COMBINED_UNIT": ["CS", "CU"],
    "FABRIC_INTERCONNECT": ["GMI", "PCS_GMI"],
    "POWER_MANAGEMENT": ["PIE"],
    "BOOT_FAILURE": ["Boot"],
}


# ---------------------------------------------------------------------------
# Tool extraction CASE expression (reusable across queries)
# ---------------------------------------------------------------------------

def _tool_case(col: str) -> str:
    return f"""CASE
        WHEN {col} LIKE '%MaxCoreStim%' OR {col} LIKE '%MaxcoreDidt%' THEN 'MaxCoreStim'
        WHEN {col} LIKE '%AMPTTK%' OR {col} LIKE '%AMPTTKv%' THEN 'AMPTTK'
        WHEN {col} LIKE '%miidct%' OR {col} LIKE '%MIIDCT%' THEN 'miidct'
        WHEN {col} LIKE '%DIFECT%' THEN 'DIFECT'
        WHEN {col} LIKE '%cpuchecker%' THEN 'cpuchecker'
        WHEN {col} LIKE '%FP_Deluge%' THEN 'FP_Deluge'
        WHEN {col} LIKE '%crest_fft%' THEN 'crest_fft'
        WHEN {col} LIKE '%hdrt_cdl%' THEN 'hdrt_cdl'
        WHEN {col} LIKE '%crest_emulator%' THEN 'crest_emulator'
        ELSE 'other'
    END"""


# ---------------------------------------------------------------------------
# Tiered Snowflake queries
# ---------------------------------------------------------------------------

def _query_msft_mcefail(failure_type: str, mca_bank_name: str | None = None) -> list[dict]:
    """Query MSFT_MCEFAIL for command distribution by bank."""
    banks = list(MCEFAIL_BANK_MAP.get(failure_type, []))
    if mca_bank_name:
        upper = mca_bank_name.upper()
        if upper not in [b.upper() for b in banks]:
            banks.append(upper)
    if not banks:
        return []

    bank_filter = " OR ".join(f"MCA_BANK = '{b}'" for b in banks)

    try:
        r = execute_query(f"""
            SELECT
                {_tool_case('COMMAND')} AS TOOL,
                MCA_BANK,
                UC,
                COUNT(*) AS CNT
            FROM MSFT_MCEFAIL
            WHERE ({bank_filter})
            GROUP BY TOOL, MCA_BANK, UC
            ORDER BY CNT DESC
            LIMIT 200
        """)
        results = []
        for row in r["rows"]:
            results.append({
                "source": "MSFT_MCEFAIL",
                "tool": row["TOOL"],
                "bank": row["MCA_BANK"],
                "count": int(row["CNT"]),
                "uc_flag": row.get("UC", ""),
            })
        return results
    except Exception as e:
        logger.warning("MSFT_MCEFAIL query failed for %s: %s", failure_type, e)
        return []


def _query_l3debug_logfiles(failure_type: str) -> list[dict]:
    """Query LEVEL3DEBUG_LOGFILES for command distribution by bank."""
    patterns = L3DEBUG_BANK_PATTERNS.get(failure_type, [])
    if not patterns:
        return []

    bank_filter = " OR ".join(f"MCA_BANK LIKE '{p}'" for p in patterns)

    try:
        r = execute_query(f"""
            SELECT
                {_tool_case('FULL_COMMAND')} AS TOOL,
                COUNT(*) AS CNT,
                COUNT(DISTINCT CPU_SN) AS UNIQUE_CPUS
            FROM LEVEL3DEBUG_LOGFILES
            WHERE COMMAND_STATUS LIKE 'fail%'
              AND MCA_BANK IS NOT NULL
              AND MCA_BANK != '[]'
              AND ({bank_filter})
            GROUP BY TOOL
            ORDER BY CNT DESC
            LIMIT 50
        """)
        results = []
        for row in r["rows"]:
            results.append({
                "source": "LEVEL3DEBUG_LOGFILES",
                "tool": row["TOOL"],
                "count": int(row["CNT"]),
                "unique_cpus": int(row["UNIQUE_CPUS"]),
            })
        return results
    except Exception as e:
        logger.warning("LEVEL3DEBUG_LOGFILES query failed for %s: %s", failure_type, e)
        return []


def _query_aura_prism(failure_type: str) -> list[dict]:
    """Query AURA_PMDATA and PRISM_PMDATA for command distribution by defect type."""
    defect_types = DEFECT_TYPE_MAP.get(failure_type, [])
    if not defect_types:
        return []

    dt_filter = " OR ".join(f"DEFECT_TYPE = '{dt}'" for dt in defect_types)
    results = []

    for table in ["AURA_PMDATA", "PRISM_PMDATA"]:
        try:
            r = execute_query(f"""
                SELECT
                    {_tool_case('FAILING_COMMAND')} AS TOOL,
                    DEFECT_TYPE,
                    COUNT(*) AS CNT
                FROM {table}
                WHERE ({dt_filter})
                  AND FAILING_COMMAND IS NOT NULL
                  AND FAILING_COMMAND != ''
                  AND FAILING_COMMAND != 'Unknown'
                  AND FAILING_COMMAND != 'N/A'
                GROUP BY TOOL, DEFECT_TYPE
                ORDER BY CNT DESC
                LIMIT 50
            """)
            for row in r["rows"]:
                results.append({
                    "source": table,
                    "tool": row["TOOL"],
                    "defect_type": row["DEFECT_TYPE"],
                    "count": int(row["CNT"]),
                })
        except Exception as e:
            logger.warning("%s query failed for %s: %s", table, failure_type, e)

    return results


# ---------------------------------------------------------------------------
# Tiered query orchestrator
# ---------------------------------------------------------------------------

def query_snowflake_for_commands(
    failure_type: str,
    mca_bank_name: str | None = None,
) -> tuple[list[dict], int, str]:
    """
    Query all Snowflake sources for command data matching a failure type.

    Returns: (aggregated_rows, tier, tier_description)

    All tiers are always queried (they're complementary data sources, not fallbacks).
    The 'tier' number reflects how many sources returned data.
    """
    all_results: list[dict] = []
    tier = 0
    tier_desc_parts = []

    # Source 1: MSFT_MCEFAIL (most reliable, clean data)
    msft_results = _query_msft_mcefail(failure_type, mca_bank_name)
    if msft_results:
        all_results.extend(msft_results)
        msft_total = sum(r["count"] for r in msft_results)
        tier_desc_parts.append(f"MSFT_MCEFAIL: {msft_total:,} records")
        tier += 1
        logger.info("MSFT_MCEFAIL: %d groups, %d total", len(msft_results), msft_total)

    # Source 2: LEVEL3DEBUG_LOGFILES
    l3_results = _query_l3debug_logfiles(failure_type)
    if l3_results:
        all_results.extend(l3_results)
        l3_total = sum(r["count"] for r in l3_results)
        tier_desc_parts.append(f"LEVEL3DEBUG: {l3_total:,} records")
        tier += 1
        logger.info("L3DEBUG: %d groups, %d total", len(l3_results), l3_total)

    # Source 3: AURA/PRISM lab data
    aura_prism_results = _query_aura_prism(failure_type)
    if aura_prism_results:
        all_results.extend(aura_prism_results)
        ap_total = sum(r["count"] for r in aura_prism_results)
        tier_desc_parts.append(f"AURA/PRISM: {ap_total:,} records")
        tier += 1
        logger.info("AURA/PRISM: %d groups, %d total", len(aura_prism_results), ap_total)

    if not all_results:
        tier_desc_parts.append("No matching records found in any source")
        tier = 0

    tier_description = f"{tier} source(s): " + " + ".join(tier_desc_parts) if tier_desc_parts else "No data"
    return all_results, tier, tier_description


# ---------------------------------------------------------------------------
# Aggregation: merge data from all sources into a command summary
# ---------------------------------------------------------------------------

def summarize_multi_source_results(raw_results: list[dict]) -> dict[str, Any]:
    """
    Aggregate results from multiple Snowflake sources into a unified command summary.

    Each raw_result has: source, tool, count, and optionally unique_cpus, bank, etc.
    We merge by tool name across all sources.
    """
    tool_stats: dict[str, dict] = {}
    total_records = 0
    sources_seen: set[str] = set()

    for row in raw_results:
        tool = row["tool"]
        count = row["count"]
        source = row["source"]
        total_records += count
        sources_seen.add(source)

        if tool not in tool_stats:
            tool_stats[tool] = {
                "command": tool,
                "total_fails": 0,
                "unique_cpus": 0,
                "sources": set(),
                "banks": set(),
                "details": [],
            }

        stats = tool_stats[tool]
        stats["total_fails"] += count
        stats["sources"].add(source)
        if "unique_cpus" in row:
            stats["unique_cpus"] += row["unique_cpus"]
        if "bank" in row:
            stats["banks"].add(row["bank"])
        stats["details"].append(f"{source}: {count:,}")

    # Sort by total failures descending
    sorted_tools = sorted(tool_stats.values(), key=lambda x: x["total_fails"], reverse=True)

    # Calculate fail rates relative to total
    for tool in sorted_tools:
        tool["fail_rate"] = tool["total_fails"] / total_records if total_records > 0 else 0.0

    return {
        "total_records": total_records,
        "total_sources": len(sources_seen),
        "sources": list(sources_seen),
        "commands": sorted_tools,
    }


def format_command_table(summary: dict) -> str:
    """Format the command summary into a text table for the LLM prompt."""
    lines = []
    for cmd in summary["commands"]:
        sources = len(cmd["sources"]) if isinstance(cmd["sources"], set) else cmd["sources"]
        line = (
            f"{cmd['command']:<20} | {cmd['total_fails']:>10,} | "
            f"{cmd['fail_rate']:>8.1%} | {sources} source(s)"
        )
        lines.append(line)
    return "\n".join(lines) if lines else "(no command data available)"
