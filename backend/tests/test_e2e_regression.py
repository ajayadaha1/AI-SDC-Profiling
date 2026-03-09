"""
E2E Regression Test Suite: AI Predictions vs. Database Ground Truth

Queries Snowflake to build ground truth (which commands actually cause failures
for each MCA bank), then sends symptom descriptions through the AI pipeline
and validates that the AI's recommendations align with real-world data.

Usage:
    docker compose exec aisdcprofiling_backend python3 -m pytest tests/test_e2e_regression.py -v
    docker compose exec aisdcprofiling_backend python3 tests/test_e2e_regression.py
"""

import asyncio
import json
import sys
import os
import time
from dataclasses import dataclass, field

# Add parent to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.snowflake_service import execute_query
from app.services.pipeline import run_pipeline


# =============================================================================
# GROUND TRUTH: Aggregated from all 4 data sources
# For each bank, the ranked tools by total failure count across all sources.
# Built from queries run on 2026-03-09 against MFG_PROD.DATACENTER_HEALTH
# =============================================================================

@dataclass
class GroundTruthEntry:
    """Expected tools for a given MCA bank, ranked by historical fail count."""
    bank: str
    description: str
    expected_tools: list[str]  # ordered by prevalence
    total_fails: int  # approx total across all sources
    symptom_text: str  # what to feed the pipeline
    secondary_tools: list[str] = field(default_factory=list)  # also valid but less common


GROUND_TRUTH: list[GroundTruthEntry] = [
    GroundTruthEntry(
        bank="UMC",
        description="Unified Memory Controller — most common failure in MSFT fleet",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT", "miidct"],
        total_fails=995_000,
        symptom_text=(
            "MCE on MCA bank UMC during stress testing. The part shows correctable "
            "memory controller errors with MCI_STATUS 0xDC2040000400011B. "
            "Multiple UMC banks triggered simultaneously."
        ),
    ),
    GroundTruthEntry(
        bank="L3",
        description="L3 Cache errors — dominant failure in L3 debug",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT"],
        total_fails=5_900,
        symptom_text=(
            "L3 cache MCE failure. MCA bank L3 with MCI_STATUS 0xDC3040000604010B. "
            "The error is correctable, seen during core stress workloads. "
            "Single L3 bank triggered."
        ),
    ),
    GroundTruthEntry(
        bank="LS",
        description="Load/Store unit errors",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT", "miidct"],
        total_fails=4_700,
        symptom_text=(
            "Load/Store unit MCE failure on MCA bank LS. MCI_STATUS 0xDC204000000D0175. "
            "Error observed on core 189 during power stress test. "
            "Correctable error, no UC or POISON flags set."
        ),
    ),
    GroundTruthEntry(
        bank="PIE",
        description="PIE (Power, Interrupts, Etc) errors",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["miidct", "DIFECT"],
        total_fails=6_300,
        symptom_text=(
            "PIE bank MCE error during power cycling stress test. "
            "MCA bank PIE (bank 30). The error appeared during MaxCoreStim "
            "power interrupt testing. Correctable, no POISON."
        ),
    ),
    GroundTruthEntry(
        bank="L2",
        description="L2 Cache errors",
        expected_tools=["MaxCoreStim", "DIFECT", "AMPTTK"],
        secondary_tools=[],
        total_fails=340,
        symptom_text=(
            "L2 cache MCE on MCA bank 2. MCI_STATUS 0x9C30400004020166. "
            "Error during core execution stress. Multiple L2 banks fired together. "
            "Correctable error on bank L2."
        ),
    ),
    GroundTruthEntry(
        bank="DE",
        description="Decode unit errors",
        expected_tools=["MaxCoreStim", "AMPTTK", "DIFECT"],
        secondary_tools=[],
        total_fails=240,
        symptom_text=(
            "Decode unit MCE failure on MCA bank DE (bank 3). "
            "Error during instruction decode stress testing. "
            "Correctable error, seen during AFHC debug cycle."
        ),
    ),
    GroundTruthEntry(
        bank="EX",
        description="Execution unit errors (bank 5)",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT"],
        total_fails=50,
        symptom_text=(
            "Execution unit MCE on MCA bank 5 (EX). Uncorrectable FATAL error "
            "during AMPTTK workload. Core 3 failed with defect type EX. "
            "Seen on Titanite platform."
        ),
    ),
    GroundTruthEntry(
        bank="GMI",
        description="GMI/PCS_GMI interconnect errors (bank 17/18)",
        expected_tools=["AMPTTK", "miidct", "DIFECT"],
        secondary_tools=["MaxCoreStim"],
        total_fails=100,
        symptom_text=(
            "PCS GMI interconnect error on MCA bank 17. "
            "Correctable MCE during miidct testing. CCD-level failure "
            "with defect type GMI. Seen on Quartz platform."
        ),
    ),
    GroundTruthEntry(
        bank="PSP",
        description="Platform Security Processor errors",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=[],
        total_fails=1_500,
        symptom_text=(
            "PSP (Platform Security Processor) MCE during stress test. "
            "MCA bank PSP triggered during MaxCoreStim execution. "
            "Correctable error, no UC flag."
        ),
    ),
    GroundTruthEntry(
        bank="FP",
        description="Floating Point unit errors (bank 6)",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT"],
        total_fails=15,
        symptom_text=(
            "Floating point unit MCE on MCA bank 6 (FP). "
            "Error during compute-intensive stress workload. "
            "Seen during FDST testing on Prism platform."
        ),
    ),
]


# =============================================================================
# LIVE GROUND TRUTH QUERIES (run against Snowflake at test time)
# =============================================================================

def query_live_ground_truth_for_bank(bank_name: str) -> dict:
    """Query Snowflake at test time for the actual tool distribution for a bank."""
    # MSFT_MCEFAIL uses clean scalar bank names
    mcefail_banks: dict[str, list[str]] = {
        "UMC": ["UMC"],
        "L3": ["L3"],
        "LS": ["LS"],
        "PIE": ["PIE"],
        "L2": ["L2"],
        "DE": ["DE"],
        "EX": ["EX"],
        "GMI": ["PCS_GMI", "PCS_XGMI"],
        "PSP": ["PSP"],
        "FP": ["FP"],
    }
    # LEVEL3DEBUG_LOGFILES stores banks as JSON arrays — use LIKE patterns
    l3debug_patterns: dict[str, list[str]] = {
        "UMC": ["%UMC%"],
        "L3": ["%L3%"],
        "LS": ["%LS%"],
        "PIE": ["%PIE%", "%30%", "%22%"],
        "L2": ["%L2%"],
        "DE": ["%DE%"],
        "EX": ["%EX%"],
        "GMI": ["%GMI%", "%17%", "%18%"],
        "PSP": ["%PSP%"],
        "FP": ["%FP%"],
    }

    result = {"tools": {}, "total": 0}

    # Query MSFT_MCEFAIL (biggest dataset, clean bank names)
    banks = mcefail_banks.get(bank_name, [bank_name])
    if banks:
        try:
            bank_filter = " OR ".join(f"MCA_BANK = '{b}'" for b in banks)
            r = execute_query(f"""
                SELECT
                    CASE
                        WHEN COMMAND LIKE '%MaxCoreStim%' OR COMMAND LIKE '%MaxcoreDidt%' THEN 'MaxCoreStim'
                        WHEN COMMAND LIKE '%AMPTTK%' OR COMMAND LIKE '%AMPTTKv%' THEN 'AMPTTK'
                        WHEN COMMAND LIKE '%miidct%' OR COMMAND LIKE '%MIIDCT%' THEN 'miidct'
                        WHEN COMMAND LIKE '%DIFECT%' THEN 'DIFECT'
                        WHEN COMMAND LIKE '%cpuchecker%' THEN 'cpuchecker'
                        ELSE 'other'
                    END as TOOL,
                    COUNT(*) as CNT
                FROM MSFT_MCEFAIL
                WHERE ({bank_filter})
                GROUP BY TOOL
                ORDER BY CNT DESC
            """)
            for row in r["rows"]:
                tool = row["TOOL"]
                cnt = int(row["CNT"])
                result["tools"][tool] = result["tools"].get(tool, 0) + cnt
                result["total"] += cnt
        except Exception as e:
            print(f"  [warn] MSFT_MCEFAIL query failed for {bank_name}: {e}")

    # Query LEVEL3DEBUG_LOGFILES
    patterns = l3debug_patterns.get(bank_name, [f"%{bank_name}%"])
    if patterns:
        try:
            l3_bank_filter = " OR ".join(f"MCA_BANK LIKE '{p}'" for p in patterns)
            r = execute_query(f"""
                SELECT
                    CASE
                        WHEN FULL_COMMAND LIKE '%MaxCoreStim%' OR FULL_COMMAND LIKE '%MaxcoreDidt%' THEN 'MaxCoreStim'
                        WHEN FULL_COMMAND LIKE '%AMPTTK%' THEN 'AMPTTK'
                        WHEN FULL_COMMAND LIKE '%miidct%' OR FULL_COMMAND LIKE '%MIIDCT%' THEN 'miidct'
                        WHEN FULL_COMMAND LIKE '%DIFECT%' THEN 'DIFECT'
                        ELSE 'other'
                    END as TOOL,
                    COUNT(*) as CNT
                FROM LEVEL3DEBUG_LOGFILES
                WHERE COMMAND_STATUS LIKE 'fail%'
                  AND MCA_BANK IS NOT NULL
                  AND MCA_BANK != '[]'
                  AND ({l3_bank_filter})
                GROUP BY TOOL
                ORDER BY CNT DESC
            """)
            for row in r["rows"]:
                tool = row["TOOL"]
                cnt = int(row["CNT"])
                result["tools"][tool] = result["tools"].get(tool, 0) + cnt
                result["total"] += cnt
        except Exception as e:
            print(f"  [warn] L3DEBUG query failed for {bank_name}: {e}")

    return result


# =============================================================================
# PIPELINE RUNNER
# =============================================================================

async def run_pipeline_collect(symptom_text: str) -> dict:
    """Run the pipeline and collect the prediction result."""
    result = {
        "parsed_profile": None,
        "prediction": None,
        "chat_response": None,
        "error": None,
        "events": [],
    }

    async for sse_event in run_pipeline(symptom_text, "test-conv-id"):
        # Parse SSE event
        lines = sse_event.strip().split("\n")
        event_type = None
        data = None
        for line in lines:
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    data = line[6:]

        result["events"].append(event_type)

        if event_type == "parsing_complete":
            result["parsed_profile"] = data
        elif event_type == "prediction":
            result["prediction"] = data
        elif event_type == "chat_response":
            result["chat_response"] = data
        elif event_type == "error":
            result["error"] = data

    return result


def extract_ai_tools(prediction: dict) -> list[str]:
    """Extract tool names from AI prediction commands."""
    tools = []
    if not prediction or "commands" not in prediction:
        return tools

    for cmd in prediction["commands"]:
        command_str = cmd.get("command", "")
        if "MaxCoreStim" in command_str:
            tools.append("MaxCoreStim")
        elif "AMPTTK" in command_str or "AMPTTKv" in command_str:
            tools.append("AMPTTK")
        elif "miidct" in command_str:
            tools.append("miidct")
        elif "DIFECT" in command_str:
            tools.append("DIFECT")
        elif "cpuchecker" in command_str:
            tools.append("cpuchecker")
        else:
            tools.append(command_str.split()[0] if command_str else "unknown")
    return tools


# =============================================================================
# TEST CASES
# =============================================================================

@dataclass
class TestResult:
    bank: str
    passed: bool
    score: float  # 0.0 to 1.0
    ai_tools: list[str]
    expected_tools: list[str]
    live_top_tools: list[str]
    overlap_count: int
    total_expected: int
    details: str
    latency_s: float = 0.0
    parsing_correct: bool = False


def score_prediction(
    ai_tools: list[str],
    expected_tools: list[str],
    secondary_tools: list[str],
    live_tools: dict[str, int],
) -> tuple[float, int, str]:
    """
    Score the AI prediction against ground truth.

    Returns (score, overlap_count, details_string).
    Score is 0.0-1.0 based on:
    - 0.4 for each primary tool match (top 2)
    - 0.1 for each secondary tool match
    - Bonus 0.1 if ranking matches live data ordering
    """
    score = 0.0
    details = []
    overlap = 0

    all_valid = set(expected_tools + secondary_tools)

    # Remove 'other' from live tools for comparison
    live_ranked = sorted(
        [(t, c) for t, c in live_tools.items() if t != "other"],
        key=lambda x: -x[1],
    )
    live_tool_names = [t for t, _ in live_ranked]

    for i, tool in enumerate(ai_tools):
        if tool in expected_tools:
            overlap += 1
            weight = 0.4 if i < 2 else 0.2
            score += weight
            details.append(f"  [MATCH] #{i+1} '{tool}' is a PRIMARY expected tool (+{weight})")
        elif tool in secondary_tools:
            overlap += 1
            score += 0.1
            details.append(f"  [PARTIAL] #{i+1} '{tool}' is a secondary expected tool (+0.1)")
        elif tool in live_tool_names:
            overlap += 1
            score += 0.05
            details.append(f"  [LIVE] #{i+1} '{tool}' found in live Snowflake data (+0.05)")
        else:
            details.append(f"  [MISS] #{i+1} '{tool}' not in ground truth")

    # Bonus: if #1 AI pick matches #1 live data pick
    if ai_tools and live_tool_names and ai_tools[0] == live_tool_names[0]:
        score += 0.1
        details.append(f"  [BONUS] Top pick '{ai_tools[0]}' matches live #1 (+0.1)")

    # Penalty if AI returned no valid tools at all
    if overlap == 0 and ai_tools:
        details.append("  [PENALTY] No overlap with any known tools")

    score = min(score, 1.0)
    return score, overlap, "\n".join(details)


async def run_single_test(entry: GroundTruthEntry, use_live_query: bool = True) -> TestResult:
    """Run a single test case."""
    print(f"\n{'='*70}")
    print(f"TEST: {entry.bank} — {entry.description}")
    print(f"{'='*70}")

    # Query live ground truth
    live_data = {"tools": {}, "total": 0}
    if use_live_query:
        print(f"  Querying live Snowflake data for {entry.bank}...")
        try:
            live_data = query_live_ground_truth_for_bank(entry.bank)
            live_ranked = sorted(
                [(t, c) for t, c in live_data["tools"].items() if t != "other"],
                key=lambda x: -x[1],
            )
            print(f"  Live data: {live_data['total']} total fails")
            for t, c in live_ranked[:5]:
                print(f"    {t}: {c:,}")
        except Exception as e:
            print(f"  [warn] Live query failed: {e}")

    # Run AI pipeline
    print(f"  Running AI pipeline...")
    start = time.time()
    result = await run_pipeline_collect(entry.symptom_text)
    latency = time.time() - start
    print(f"  Pipeline completed in {latency:.1f}s")

    # Check for errors
    if result["error"]:
        print(f"  [ERROR] Pipeline error: {result['error']}")
        return TestResult(
            bank=entry.bank, passed=False, score=0.0,
            ai_tools=[], expected_tools=entry.expected_tools,
            live_top_tools=[], overlap_count=0, total_expected=len(entry.expected_tools),
            details=f"Pipeline error: {result['error']}", latency_s=latency,
        )

    # Check if it was treated as conversational (bad — it should be a symptom)
    if result["chat_response"] and not result["prediction"]:
        print(f"  [FAIL] Pipeline treated symptom as conversational chat!")
        return TestResult(
            bank=entry.bank, passed=False, score=0.0,
            ai_tools=[], expected_tools=entry.expected_tools,
            live_top_tools=[], overlap_count=0, total_expected=len(entry.expected_tools),
            details="Pipeline misclassified symptom as conversational", latency_s=latency,
        )

    # Validate parsing
    parsed = result["parsed_profile"]
    parsing_correct = False
    if parsed:
        parsed_bank = str(parsed.get("failure_type", "")).upper()
        bank_aliases = {
            "UMC": ["UMC", "UMC_MEMORY_CONTROLLER", "MEMORY"],
            "L3": ["L3", "L3_CACHE"],
            "LS": ["LS", "LOAD_STORE", "LOAD/STORE"],
            "PIE": ["PIE", "POWER_MANAGEMENT", "POWER"],
            "L2": ["L2", "L2_CACHE"],
            "DE": ["DE", "DECODE", "INSTRUCTION_FETCH"],
            "EX": ["EX", "EXECUTION", "EXECUTION_UNIT"],
            "GMI": ["GMI", "PCS_GMI", "FABRIC_INTERCONNECT", "FABRIC"],
            "PSP": ["PSP", "PLATFORM_SECURITY"],
            "FP": ["FP", "FLOATING_POINT", "FLOAT"],
        }
        valid_names = bank_aliases.get(entry.bank, [entry.bank])
        parsing_correct = any(alias in parsed_bank for alias in valid_names)
        print(f"  Parsed failure_type: '{parsed.get('failure_type')}' — {'CORRECT' if parsing_correct else 'MISMATCH'}")

    # Extract AI tools
    ai_tools = extract_ai_tools(result["prediction"])
    print(f"  AI recommended tools: {ai_tools}")
    print(f"  Expected tools: {entry.expected_tools}")

    # Score it
    live_ranked = sorted(
        [(t, c) for t, c in live_data["tools"].items() if t != "other"],
        key=lambda x: -x[1],
    )
    live_tool_names = [t for t, _ in live_ranked]

    score, overlap, details = score_prediction(
        ai_tools, entry.expected_tools, entry.secondary_tools, live_data["tools"]
    )

    # Parsing correctness counts too
    if parsing_correct:
        score = min(score + 0.1, 1.0)
        details += "\n  [BONUS] Parsing correctly identified the failure type (+0.1)"

    passed = score >= 0.3  # At least one primary tool match
    status = "PASS" if passed else "FAIL"
    print(f"\n  Score: {score:.2f}/1.00 — {status}")
    print(details)

    return TestResult(
        bank=entry.bank,
        passed=passed,
        score=score,
        ai_tools=ai_tools,
        expected_tools=entry.expected_tools,
        live_top_tools=live_tool_names[:5],
        overlap_count=overlap,
        total_expected=len(entry.expected_tools),
        details=details,
        latency_s=latency,
        parsing_correct=parsing_correct,
    )


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

async def run_all_tests(use_live_query: bool = True):
    """Run all regression tests and print summary."""
    print("=" * 70)
    print("AI-SDC-Profiling E2E Regression Test Suite")
    print(f"Testing {len(GROUND_TRUTH)} failure scenarios against ground truth")
    print(f"Live Snowflake queries: {'enabled' if use_live_query else 'disabled (using static fixtures)'}")
    print("=" * 70)

    results: list[TestResult] = []

    for entry in GROUND_TRUTH:
        try:
            result = await run_single_test(entry, use_live_query)
            results.append(result)
        except Exception as e:
            print(f"\n  [EXCEPTION] Test for {entry.bank} crashed: {e}")
            results.append(TestResult(
                bank=entry.bank, passed=False, score=0.0,
                ai_tools=[], expected_tools=entry.expected_tools,
                live_top_tools=[], overlap_count=0, total_expected=len(entry.expected_tools),
                details=f"Exception: {e}", latency_s=0.0,
            ))

    # Print summary
    print("\n")
    print("=" * 70)
    print("REGRESSION TEST SUMMARY")
    print("=" * 70)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    avg_score = sum(r.score for r in results) / total if total else 0
    avg_latency = sum(r.latency_s for r in results) / total if total else 0
    parsing_correct = sum(1 for r in results if r.parsing_correct)

    print(f"\n{'Bank':<10} {'Status':<8} {'Score':<8} {'AI Tools':<40} {'Expected':<25} {'Latency':<8}")
    print("-" * 99)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        ai_str = ", ".join(r.ai_tools[:3]) if r.ai_tools else "(none)"
        exp_str = ", ".join(r.expected_tools[:3])
        print(f"{r.bank:<10} {status:<8} {r.score:<8.2f} {ai_str:<40} {exp_str:<25} {r.latency_s:<8.1f}s")

    print(f"\n{'='*70}")
    print(f"  Tests passed:   {passed}/{total} ({100*passed/total:.0f}%)")
    print(f"  Average score:  {avg_score:.2f}/1.00")
    print(f"  Parsing correct: {parsing_correct}/{total}")
    print(f"  Avg latency:    {avg_latency:.1f}s per test")
    print(f"  Total time:     {sum(r.latency_s for r in results):.0f}s")
    print(f"{'='*70}")

    # Detailed failures
    failures = [r for r in results if not r.passed]
    if failures:
        print(f"\nFailed tests ({len(failures)}):")
        for r in failures:
            print(f"\n  {r.bank}: score={r.score:.2f}")
            print(f"    AI suggested: {r.ai_tools}")
            print(f"    Expected:     {r.expected_tools}")
            print(f"    Live top:     {r.live_top_tools}")
            print(r.details)

    return results


# =============================================================================
# PYTEST INTEGRATION
# =============================================================================

def test_e2e_regression():
    """Pytest entry point — runs all tests and asserts minimum pass rate."""
    results = asyncio.run(run_all_tests(use_live_query=True))
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    # We expect at least 60% of tests to pass
    assert passed / total >= 0.6, (
        f"Regression: only {passed}/{total} tests passed ({100*passed/total:.0f}%). "
        f"Minimum threshold is 60%."
    )


if __name__ == "__main__":
    asyncio.run(run_all_tests(use_live_query=True))
