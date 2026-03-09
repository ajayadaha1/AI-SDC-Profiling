# AI Failure Profiling — First Pass Design Document

## LLM-in-the-Loop Predictive Debug System for AFHC/ANC

---

## Table of Contents

1. [Overview & Philosophy](#1-overview--philosophy)
2. [System Architecture](#2-system-architecture)
3. [Step 1: User Interface — Symptom Intake](#3-step-1-user-interface--symptom-intake)
4. [Step 2: LLM Parsing — Failure Type Extraction](#4-step-2-llm-parsing--failure-type-extraction)
5. [Step 3: Database Query — Finding Similar Failed Parts](#5-step-3-database-query--finding-similar-failed-parts)
6. [Step 4: AI Ranking — Top 3 Command Prediction](#6-step-4-ai-ranking--top-3-command-prediction)
7. [End-to-End Data Flow](#7-end-to-end-data-flow)
8. [Database Schema & Queries](#8-database-schema--queries)
9. [LLM Prompt Engineering](#9-llm-prompt-engineering)
10. [Handling Edge Cases](#10-handling-edge-cases)
11. [Feedback Loop](#11-feedback-loop)
12. [Technology Choices](#12-technology-choices)
13. [Implementation Plan](#13-implementation-plan)

---

## 1. Overview & Philosophy

### Why LLM-in-the-Loop for First Pass?

Instead of jumping straight to training a custom ML model (which requires extensive feature engineering, labeled data validation, and weeks of iteration), we take a **pragmatic first-pass approach**:

> **Use an LLM as both the parser and the ranker, with the database as the knowledge backbone.**

This gives us:
- **Speed to deploy**: No model training. Ship in days, not months.
- **Flexibility**: Engineers can describe symptoms however they want — messy free-text, structured codes, or a mix. The LLM handles it.
- **Explainability for free**: The LLM can articulate *why* it recommends each command in plain English.
- **Data collection**: Every interaction generates structured data we can later use to train a dedicated ML model (Phase 2).

### The Core Insight

The problem has two fundamentally different sub-tasks:

| Sub-task | Nature | Best Tool |
|----------|--------|-----------|
| **Parse symptoms** → structured failure type | Natural language understanding + domain knowledge | **LLM** |
| **Find similar parts** → historical matches | Exact/fuzzy search over structured data | **Database (SQL)** |
| **Rank commands** → top 3 most likely to fail | Reasoning over tabular evidence + domain context | **LLM** |

An LLM excels at the *soft* parts (parsing messy input, reasoning over evidence). A database excels at the *hard* part (finding exact matches at scale). We combine both.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (Web UI)                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  "Part shows intermittent MCE Bank 10 errors, 0xBEEF0010,       │  │
│  │   under hot thermal stress. UMC-related. Fails during membw."   │  │
│  └──────────────────────────────┬────────────────────────────────────┘  │
└─────────────────────────────────┼──────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 1: LLM PARSING LAYER                            │
│                                                                         │
│  Input:  Raw symptom text from engineer                                 │
│  Action: Extract structured failure profile                             │
│  Output: {                                                              │
│            "failure_type": "UMC_MEMORY_CONTROLLER",                     │
│            "mce_bank": 10,                                              │
│            "mce_code": "0xBEEF0010",                                    │
│            "error_severity": "uncorrectable",                           │
│            "thermal_state": "hot",                                      │
│            "boot_stage": "stress",                                      │
│            "confidence": 0.92                                           │
│          }                                                              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  STEP 2: DATABASE QUERY LAYER                           │
│                                                                         │
│  Input:  Parsed failure profile (structured fields)                     │
│  Action: Query Snowflake for parts with matching failure signatures     │
│  Output: [                                                              │
│            { cpu: "CPU_A", commands_run: [...], results: [...] },       │
│            { cpu: "CPU_B", commands_run: [...], results: [...] },       │
│            ... (20-50 similar parts)                                    │
│          ]                                                              │
│                                                                         │
│  Key: We retrieve ALL commands run on similar parts + their PASS/FAIL  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  STEP 3: LLM RANKING LAYER                              │
│                                                                         │
│  Input:  Original symptoms + matched parts + all command results        │
│  Action: Reason over evidence → rank commands by failure likelihood     │
│  Output: {                                                              │
│            "recommendations": [                                         │
│              { "rank": 1, "command": "stream -t mem_band_max",          │
│                "confidence": 0.94,                                      │
│                "reasoning": "Failed on 21/23 similar UMC parts..." },  │
│              { "rank": 2, ... },                                        │
│              { "rank": 3, ... }                                         │
│            ]                                                            │
│          }                                                              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     RESPONSE TO USER                                    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  Parsed Failure: UMC_MEMORY_CONTROLLER (Bank 10, hot, stress)  │    │
│  │  Similar Parts Found: 23                                       │    │
│  │                                                                 │    │
│  │  #1  94% — stream -t mem_band_max -v 1.2                       │    │
│  │     → Failed on 21/23 similar parts. UMC faults strongly       │    │
│  │       correlate with memory bandwidth stress under thermal.    │    │
│  │                                                                 │    │
│  │  #2  87% — mprime -t L3_stress_umc                             │    │
│  │     → Failed on 18/23 similar parts. L3-UMC interface test.   │    │
│  │                                                                 │    │
│  │  #3  71% — membw -p read_write -s 4G                           │    │
│  │     → Failed on 14/23 similar parts. Direct memory path test. │    │
│  │                                                                 │    │
│  │  [Run These Commands]  [Provide Feedback]                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step 1: User Interface — Symptom Intake

### What the UI Needs to Do

The UI is the **single entry point** where a debug engineer describes what they see on the failing part. It must handle both:

1. **Free-form text** — engineers describing symptoms naturally:
   > *"This part keeps throwing MCEs on bank 10 when we run memory stress under hot. MCE code is 0xBEEF0010. Seems like a UMC issue. It passed POST fine but fails under load."*

2. **Optional structured fields** — for engineers who prefer to fill in specifics directly, or to supplement the free text.

### UI Design

```
╔══════════════════════════════════════════════════════════════════════╗
║  AI SDC Profiler — Symptom Intake                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Describe the failure (free text):                                   ║
║  ┌──────────────────────────────────────────────────────────────┐    ║
║  │  Part shows intermittent MCE Bank 10 errors, code            │    ║
║  │  0xBEEF0010, under hot thermal stress. Appears to be UMC    │    ║
║  │  related. Fails during memory bandwidth tests.              │    ║
║  └──────────────────────────────────────────────────────────────┘    ║
║                                                                      ║
║  ── Optional: Fill known fields directly ──                          ║
║                                                                      ║
║  MCE Code: [0xBEEF0010    ]    MCA Bank: [10 - UMC         ▼]      ║
║  Error Type: [Uncorrectable ▼]  Thermal: [Hot (75°C+)      ▼]      ║
║  Boot Stage: [Stress Test   ▼]  Stepping: [B2              ▼]      ║
║  Part ID:    [SDC-2026-0451 ]                                        ║
║                                                                      ║
║  ── Optional: Upload log files ──                                    ║
║  [📎 Upload MCE dump / BIOS log / dmesg]                            ║
║                                                                      ║
║                    [ ⚡ Analyze & Predict ]                           ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Primary input** | Free text | Engineers think in natural language. Removing friction → higher adoption. |
| **Structured fields** | Optional, supplementary | If provided, they override/supplement LLM parsing → higher accuracy. |
| **Log upload** | Optional | Future enhancement: LLM can parse raw MCE dumps directly. |
| **Part ID** | Optional but encouraged | Links prediction to the physical unit for feedback tracking. |

### What Gets Sent to the Backend

```json
{
  "symptom_text": "Part shows intermittent MCE Bank 10 errors, code 0xBEEF0010, under hot thermal stress...",
  "structured_fields": {
    "mce_code": "0xBEEF0010",
    "mce_bank": 10,
    "error_type": "uncorrectable",
    "thermal_state": "hot",
    "boot_stage": "stress",
    "stepping": "B2",
    "part_id": "SDC-2026-0451"
  },
  "uploaded_logs": null
}
```

---

## 4. Step 2: LLM Parsing — Failure Type Extraction

### What Problem Does This Solve?

Engineers describe failures inconsistently:
- *"Bank 10 MCE"* vs *"UMC error"* vs *"memory controller fault"* → **same thing**
- *"It's hot"* vs *"thermal stress at 85C"* vs *"high temp"* → **same thing**
- *"0xBEEF0010"* → needs to be decomposed into error family, model-specific code

The LLM normalizes all of this into a **canonical failure profile** that we can query against the database.

### How It Works

```
                     ┌─────────────────────────┐
  Raw symptom text   │                         │   Structured failure profile
  + any structured ──►    LLM (GPT-4 / etc)    ├──►  (JSON)
    fields provided  │    + System Prompt       │
                     │    + Field Definitions   │
                     └─────────────────────────┘
```

### The LLM's Job (Precisely)

Given the raw input, the LLM must:

1. **Extract** specific hardware fields:
   - `failure_type` — canonical category (see taxonomy below)
   - `mce_bank` — integer bank number
   - `mce_code` — hex code (if mentioned)
   - `error_severity` — correctable / uncorrectable / fatal / poison
   - `thermal_state` — ambient / warm / hot / extreme
   - `voltage_state` — nominal / low / high / marginal (if mentioned)
   - `boot_stage` — POST / OS boot / idle / light load / stress
   - `failing_cores` — core list/count (if mentioned)
   - `keywords` — additional domain-specific terms

2. **Classify** into a failure type from a predefined taxonomy

3. **Merge** with any structured fields the user explicitly provided (structured fields take priority over LLM extraction)

4. **Express confidence** — how certain is the LLM about its classification?

### Failure Type Taxonomy

This is the **canonical set of failure categories** the LLM classifies into. These map directly to database query patterns.

```
FAILURE_TAXONOMY = {
    "UMC_MEMORY_CONTROLLER": {
        "banks": [10, 11],
        "description": "Unified Memory Controller faults",
        "typical_symptoms": ["memory bandwidth failures", "ECC errors", "DRAM access faults"]
    },
    "EXECUTION_UNIT": {
        "banks": [5],
        "description": "Integer/ALU execution pipeline faults",
        "typical_symptoms": ["compute errors", "ALU miscompare", "integer workload failures"]
    },
    "FLOATING_POINT": {
        "banks": [6],
        "description": "FP/FMA unit faults",
        "typical_symptoms": ["FP exceptions", "FMA errors", "linpack failures"]
    },
    "LOAD_STORE": {
        "banks": [0],
        "description": "Load-Store unit faults",
        "typical_symptoms": ["data corruption on load/store", "cache coherency", "memory ordering"]
    },
    "INSTRUCTION_FETCH": {
        "banks": [1],
        "description": "Instruction fetch / branch prediction faults",
        "typical_symptoms": ["instruction corruption", "branch mispredict", "IF pipeline errors"]
    },
    "COMBINED_UNIT": {
        "banks": [2],
        "description": "Combined unit (mixed integer + FP path) faults",
        "typical_symptoms": ["mixed workload failures", "scheduler errors"]
    },
    "L2_CACHE": {
        "banks": [3],
        "description": "L2 cache faults",
        "typical_symptoms": ["cache parity", "L2 ECC", "stale cache line"]
    },
    "L3_CACHE": {
        "banks": [7, 8],
        "description": "L3 / Last-level cache faults",
        "typical_symptoms": ["L3 tag errors", "snoop filter faults", "LLC access failures"]
    },
    "FABRIC_INTERCONNECT": {
        "banks": [12, 13, 14],
        "description": "Data Fabric / Interconnect faults",
        "typical_symptoms": ["cross-CCD failures", "NUMA errors", "fabric timeout"]
    },
    "POWER_MANAGEMENT": {
        "banks": [],
        "description": "Voltage / frequency / power state faults",
        "typical_symptoms": ["VID errors", "P-state transitions", "voltage droop", "clock stretch"]
    },
    "BOOT_FAILURE": {
        "banks": [],
        "description": "Fails to POST or boot OS",
        "typical_symptoms": ["no POST", "BSOD on boot", "hang at BIOS", "reset loop"]
    },
    "UNKNOWN": {
        "banks": [],
        "description": "Cannot confidently classify",
        "typical_symptoms": []
    }
}
```

### LLM Output Schema

```json
{
  "failure_type": "UMC_MEMORY_CONTROLLER",
  "mce_bank": 10,
  "mce_code": "0xBEEF0010",
  "mce_code_family": "BEEF",
  "error_severity": "uncorrectable",
  "thermal_state": "hot",
  "voltage_state": null,
  "boot_stage": "stress",
  "frequency_context": null,
  "failing_cores": null,
  "stepping": "B2",
  "keywords": ["UMC", "memory bandwidth", "thermal stress", "intermittent"],
  "confidence": 0.92,
  "reasoning": "Bank 10 is the UMC (Unified Memory Controller). The MCE code 0xBEEF0010 falls in the UMC error family. Symptoms during memory bandwidth stress under thermal load are classic UMC failure patterns."
}
```

### What If the User Already Provided Structured Fields?

**Merge strategy: explicit fields override LLM extraction.**

```python
def merge_parsed_and_structured(llm_output: dict, user_fields: dict) -> dict:
    """
    User-provided structured fields take priority over LLM extraction.
    LLM fills in the gaps from free text.
    """
    merged = llm_output.copy()
    for key, value in user_fields.items():
        if value is not None and value != "":
            merged[key] = value  # User override wins
    return merged
```

This means an engineer who types *"it's a memory issue"* in the text box but also selects **Bank 10** and **Uncorrectable** from the dropdowns gets the best of both worlds — the LLM interprets the vague text, but the explicit selections anchor the classification.

---

## 5. Step 3: Database Query — Finding Similar Failed Parts

### The Goal

Given the parsed failure profile from Step 2, find historical parts in Snowflake that had **similar symptoms** and retrieve **all commands that were run on them** along with pass/fail results.

### Query Strategy: Tiered Similarity Search

We don't do a single rigid query. Instead, we use a **tiered approach** — start strict, loosen if we don't get enough matches:

```
Tier 1 (Strict):  Same bank + same MCE family + same error severity + similar thermal
                   → Expect: 5-30 matches
                   → If < 5 matches, fall through to Tier 2

Tier 2 (Relaxed): Same bank + same error severity
                   → Expect: 20-100 matches
                   → If < 5 matches, fall through to Tier 3

Tier 3 (Broad):   Same failure_type category (any bank in that family)
                   → Expect: 50-200+ matches
                   → Always returns something (unless category is brand new)
```

### Why Tiered?

- **Too strict** → not enough matches → LLM has no evidence to rank commands
- **Too loose** → too many irrelevant matches → LLM gets noisy data, predictions degrade
- **Tiered** → we get the *tightest relevant set* possible

### SQL Queries

#### Tier 1: Strict Match

```sql
-- Find parts with matching bank, MCE family, error severity, and similar thermal conditions
SELECT
    i.cpu_id,
    i.stepping,
    i.mce_code,
    i.mce_bank,
    i.error_type,
    i.thermal_state,
    i.boot_stage,
    e.command,
    e.command_params,
    e.result,
    e.fail_signature,
    e.execution_timestamp
FROM sdc_intake_logs i
JOIN afhc_anc_executions e ON i.cpu_id = e.cpu_id
WHERE i.mce_bank = :parsed_bank                           -- exact bank match
  AND SUBSTR(i.mce_code, 3, 4) = :parsed_mce_family       -- MCE family match (first 4 hex digits)
  AND i.error_type = :parsed_error_severity                -- same error severity
  AND i.thermal_state = :parsed_thermal                    -- similar thermal context
ORDER BY e.execution_timestamp DESC
LIMIT 2000;  -- cap to avoid overwhelming the LLM
```

#### Tier 2: Relaxed Match

```sql
SELECT
    i.cpu_id, i.stepping, i.mce_code, i.mce_bank,
    i.error_type, i.thermal_state, i.boot_stage,
    e.command, e.command_params, e.result, e.fail_signature
FROM sdc_intake_logs i
JOIN afhc_anc_executions e ON i.cpu_id = e.cpu_id
WHERE i.mce_bank = :parsed_bank
  AND i.error_type = :parsed_error_severity
ORDER BY e.execution_timestamp DESC
LIMIT 2000;
```

#### Tier 3: Broad Category Match

```sql
SELECT
    i.cpu_id, i.stepping, i.mce_code, i.mce_bank,
    i.error_type, i.thermal_state, i.boot_stage,
    e.command, e.command_params, e.result, e.fail_signature
FROM sdc_intake_logs i
JOIN afhc_anc_executions e ON i.cpu_id = e.cpu_id
WHERE i.mce_bank IN (:banks_for_failure_type)  -- all banks in the category
ORDER BY e.execution_timestamp DESC
LIMIT 2000;
```

### What We Extract From the Results

From the raw query results, we compute a **command summary table** before sending to the LLM:

```python
def summarize_command_results(query_results: list[dict]) -> dict:
    """
    Aggregate raw (cpu, command, result) rows into a command-level summary.
    This is what we send to the LLM for ranking.
    """
    similar_cpus = set(row['cpu_id'] for row in query_results)
    
    command_stats = {}
    for row in query_results:
        cmd = row['command']
        if cmd not in command_stats:
            command_stats[cmd] = {
                'command': cmd,
                'common_params': [],
                'total_runs': 0,
                'fail_count': 0,
                'pass_count': 0,
                'fail_rate': 0.0,
                'cpus_failed_on': set(),
                'cpus_passed_on': set(),
                'common_fail_signatures': [],
                'thermal_at_failure': [],
            }
        
        stats = command_stats[cmd]
        stats['total_runs'] += 1
        
        if row['result'] == 'FAIL':
            stats['fail_count'] += 1
            stats['cpus_failed_on'].add(row['cpu_id'])
            if row['fail_signature']:
                stats['common_fail_signatures'].append(row['fail_signature'])
            if row['thermal_state']:
                stats['thermal_at_failure'].append(row['thermal_state'])
        else:
            stats['pass_count'] += 1
            stats['cpus_passed_on'].add(row['cpu_id'])
        
        stats['fail_rate'] = stats['fail_count'] / stats['total_runs']
    
    # Sort by fail rate descending
    sorted_commands = sorted(
        command_stats.values(),
        key=lambda x: x['fail_rate'],
        reverse=True
    )
    
    return {
        'total_similar_parts': len(similar_cpus),
        'query_tier': 1,  # which tier matched
        'commands': sorted_commands
    }
```

### Example Summary Sent to LLM

```
Similar Parts Found: 23 (Tier 1: Bank 10 + MCE family BEEF + uncorrectable + hot)

Command                          | Runs | Fails | Fail Rate | Parts Failed
─────────────────────────────────┼──────┼───────┼───────────┼─────────────
stream -t mem_band_max -v 1.2    |  23  |  21   |   91.3%   |  21/23
mprime -t L3_stress_umc          |  22  |  18   |   81.8%   |  18/22
membw -p read_write -s 4G        |  20  |  14   |   70.0%   |  14/20
linpack -c all_cores -fpu_only   |  23  |  11   |   47.8%   |  11/23
prime95 -t blend -c all          |  21  |   8   |   38.1%   |   8/21
y-cruncher -t swp_stress         |  19  |   6   |   31.6%   |   6/19
stressapptest -M 4096 -s 300     |  23  |   4   |   17.4%   |   4/23
coremark -t integer_heavy        |  18  |   2   |   11.1%   |   2/18
redis_bench -t pipeline_heavy    |  15  |   0   |    0.0%   |   0/15
nginx_bench -t high_rps          |  12  |   0   |    0.0%   |   0/12
```

---

## 6. Step 4: AI Ranking — Top 3 Command Prediction

### Why Not Just Take the Top 3 by Fail Rate?

You might think: *"The command summary already has fail rates sorted. Just return the top 3."*

**That's a reasonable baseline**, but the LLM adds significant value:

| Factor | Pure SQL Sort | LLM Ranking |
|--------|--------------|-------------|
| Historic fail rate | ✅ | ✅ |
| Symptom-command affinity | ❌ | ✅ The LLM understands that a *thermal* failure + UMC fault should weight memory-thermal tests higher |
| Command diversity | ❌ Top 3 might all test the same thing | ✅ LLM can diversify: "stream, mprime, and membw all test memory differently" |
| Speed of failure | ❌ | ✅ LLM can factor in that `stream` takes 30s but `stressapptest` takes 300s — faster is better |
| Contextual reasoning | ❌ | ✅ If engineer says "fails early in test", LLM can bias toward commands that fail quickly |
| Explanation | ❌ | ✅ LLM explains *why* each command was selected |

### What the LLM Receives

We send the LLM:

1. **Original symptoms** (the user's raw text + parsed profile)
2. **Command summary table** (from Step 3)
3. **Instructions** to select top 3 and explain

### LLM's Ranking Logic (What We Want It to Reason About)

The system prompt instructs the LLM to consider:

1. **Fail rate on similar parts** — primary signal. Higher fail rate = more likely to reproduce.
2. **Symptom-command relevance** — does the command specifically target the suspected fault area?
   - UMC faults → memory tests rank higher than compute tests
   - FP faults → FPU/FMA tests rank higher than memory tests
3. **Speed to failure** — prefer commands that fail quickly. If `stream` takes 30s and `stressapptest` takes 300s, and both have ~90% fail rate, prefer `stream`.
4. **Diversity** — the 3 commands should test *different aspects* of the fault. Don't recommend 3 variations of the same memory test.
5. **Confidence calibration** — if only 5 similar parts were found (Tier 3 match), confidence should be lower.
6. **Edge signals** — if the engineer mentioned specific details (e.g., "fails after 5 minutes", "only on core 3"), factor that in.

### LLM Output Schema

```json
{
  "analysis": {
    "total_similar_parts": 23,
    "match_quality": "strong",
    "match_tier": 1,
    "dominant_failure_pattern": "UMC memory controller faults under thermal stress, primarily on Bank 10"
  },
  "recommendations": [
    {
      "rank": 1,
      "command": "stream -t mem_band_max -v 1.2",
      "confidence": 0.94,
      "fail_rate_on_similar": "91.3% (21/23 parts)",
      "estimated_time_to_fail": "~30 seconds",
      "reasoning": "Highest historical fail rate (91.3%) on parts with matching UMC Bank 10 symptoms. This command maximizes memory bandwidth which directly stresses the UMC — the suspected fault area. It's also fast-running (~30s), meaning you'll know quickly if it reproduces."
    },
    {
      "rank": 2,
      "command": "mprime -t L3_stress_umc",
      "confidence": 0.87,
      "fail_rate_on_similar": "81.8% (18/22 parts)",
      "estimated_time_to_fail": "~2 minutes",
      "reasoning": "Tests a different failure path — the L3-to-UMC interface rather than direct memory bandwidth. High fail rate (81.8%) and targets a different vector than #1, increasing the chance of catching the fault if stream passes."
    },
    {
      "rank": 3,
      "command": "membw -p read_write -s 4G",
      "confidence": 0.71,
      "fail_rate_on_similar": "70.0% (14/20 parts)",
      "estimated_time_to_fail": "~1 minute",
      "reasoning": "Complementary to #1 — uses a different memory access pattern (explicit read/write vs streaming). Some UMC faults only trigger under specific access patterns. Provides diagnostic diversity."
    }
  ],
  "fallback_suggestion": "If all 3 pass, consider running linpack (47.8% fail rate) which tests FPU+memory interaction — some UMC intermittent faults only surface under combined compute+memory pressure.",
  "caveats": "Confidence is high (Tier 1 match, 23 similar parts). However, the MCE code 0xBEEF0010 was only observed on 15 of the 23 parts — the exact code may indicate a sub-variant. Monitor for different fail signatures."
}
```

---

## 7. End-to-End Data Flow

### Sequence Diagram

```
Engineer          UI            Backend          LLM              Snowflake
   │               │               │               │                  │
   │──enters───────►│               │               │                  │
   │  symptoms      │               │               │                  │
   │               │──POST /api────►│               │                  │
   │               │  /predict      │               │                  │
   │               │               │                │                  │
   │               │               │──────────────► │                  │
   │               │               │  "Parse these   │                  │
   │               │               │   symptoms"     │                  │
   │               │               │                │                  │
   │               │               │◄────────────── │                  │
   │               │               │  Parsed profile │                  │
   │               │               │  (JSON)         │                  │
   │               │               │                │                  │
   │               │               │──────────────────────────────────►│
   │               │               │  SELECT ... WHERE bank=10        │
   │               │               │  AND mce_family='BEEF' ...       │
   │               │               │                │                  │
   │               │               │◄──────────────────────────────── │
   │               │               │  23 similar parts               │
   │               │               │  + all command results           │
   │               │               │                │                  │
   │               │               │──aggregate ────│                  │
   │               │               │  command stats  │                  │
   │               │               │                │                  │
   │               │               │──────────────► │                  │
   │               │               │  "Rank top 3    │                  │
   │               │               │   commands"     │                  │
   │               │               │                │                  │
   │               │               │◄────────────── │                  │
   │               │               │  Top 3 ranked   │                  │
   │               │               │  + explanations │                  │
   │               │               │                │                  │
   │               │◄──JSON────────│               │                  │
   │               │  response      │               │                  │
   │◄──display─────│               │               │                  │
   │  results       │               │               │                  │
   │               │               │               │                  │
   │──runs cmds──► │               │               │                  │
   │  on bench      │               │               │                  │
   │               │               │               │                  │
   │──feedback─────►│──────────────►│──────────────────────────────────►│
   │  pass/fail     │               │  INSERT INTO feedback ...        │
```

### Latency Budget

| Step | Expected Latency | Notes |
|------|-----------------|-------|
| UI → Backend | ~50ms | Local network |
| LLM Parse (Step 2) | ~1-2 seconds | Single LLM call, structured output |
| Database Query (Step 3) | ~200-500ms | Snowflake query on indexed table |
| Aggregate command stats | ~50ms | In-memory Python processing |
| LLM Rank (Step 4) | ~2-3 seconds | More complex reasoning call |
| **Total** | **~3-6 seconds** | Acceptable for interactive debug workflow |

---

## 8. Database Schema & Queries

### Core Tables

#### `sdc_intake_logs` — When a part enters debug

```sql
CREATE TABLE sdc_intake_logs (
    cpu_id          VARCHAR(64) PRIMARY KEY,
    stepping        VARCHAR(8),
    sku             VARCHAR(32),
    mce_code        VARCHAR(20),
    mce_bank        INTEGER,
    error_type      VARCHAR(20),      -- correctable, uncorrectable, fatal, poison
    boot_stage      VARCHAR(20),      -- POST, OS boot, idle, light load, stress
    thermal_state   VARCHAR(20),      -- ambient, warm, hot, extreme
    voltage_state   FLOAT,
    frequency_mhz   INTEGER,
    failing_cores   VARCHAR(128),
    symptom_text    TEXT,              -- free-form engineer notes
    intake_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `afhc_anc_executions` — Every command ever run on every part

```sql
CREATE TABLE afhc_anc_executions (
    execution_id        INTEGER AUTOINCREMENT PRIMARY KEY,
    cpu_id              VARCHAR(64) REFERENCES sdc_intake_logs(cpu_id),
    command             VARCHAR(128),
    command_params      VARCHAR(256),
    result              VARCHAR(10),   -- PASS, FAIL
    fail_signature      TEXT,          -- detailed failure output when FAIL
    execution_duration  INTEGER,       -- seconds
    execution_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Critical index for our queries
CREATE INDEX idx_exec_bank ON afhc_anc_executions(cpu_id);
```

#### `sdc_predictions` — Log every prediction we make (for feedback loop)

```sql
CREATE TABLE sdc_predictions (
    prediction_id       INTEGER AUTOINCREMENT PRIMARY KEY,
    cpu_id              VARCHAR(64),
    symptom_text        TEXT,
    parsed_failure_type VARCHAR(64),
    parsed_mce_bank     INTEGER,
    match_tier          INTEGER,
    similar_parts_count INTEGER,
    
    -- Predicted commands
    rank1_command       VARCHAR(128),
    rank1_confidence    FLOAT,
    rank2_command       VARCHAR(128),
    rank2_confidence    FLOAT,
    rank3_command       VARCHAR(128),
    rank3_confidence    FLOAT,
    
    -- Feedback (filled later when engineer reports back)
    rank1_actual_result VARCHAR(10),   -- PASS, FAIL, NOT_RUN
    rank2_actual_result VARCHAR(10),
    rank3_actual_result VARCHAR(10),
    
    model_version       VARCHAR(20),
    prediction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    feedback_timestamp   TIMESTAMP
);
```

---

## 9. LLM Prompt Engineering

### Prompt 1: Symptom Parsing

```
SYSTEM:
You are a silicon debug expert specializing in CPU failure analysis for AMD processors.
Your job is to parse engineer-written symptom descriptions and extract a structured failure profile.

You MUST output valid JSON matching this schema:
{
  "failure_type": "<one of: UMC_MEMORY_CONTROLLER, EXECUTION_UNIT, FLOATING_POINT, LOAD_STORE, INSTRUCTION_FETCH, COMBINED_UNIT, L2_CACHE, L3_CACHE, FABRIC_INTERCONNECT, POWER_MANAGEMENT, BOOT_FAILURE, UNKNOWN>",
  "mce_bank": <integer or null>,
  "mce_code": "<hex string or null>",
  "mce_code_family": "<first 4 hex digits of MCE code, or null>",
  "error_severity": "<correctable|uncorrectable|fatal|poison|null>",
  "thermal_state": "<ambient|warm|hot|extreme|null>",
  "voltage_state": "<nominal|low|high|marginal|null>",
  "boot_stage": "<POST|OS_boot|idle|light_load|stress|null>",
  "frequency_context": "<string description or null>",
  "failing_cores": "<core list string or null>",
  "keywords": ["<relevant domain keywords>"],
  "confidence": <float 0.0-1.0>,
  "reasoning": "<brief explanation of your classification>"
}

Bank reference:
- Bank 0: LS (Load-Store)
- Bank 1: IF (Instruction Fetch)
- Bank 2: CU (Combined Unit)
- Bank 3: L2 Cache
- Bank 5: EX (Execution Unit)
- Bank 6: FP (Floating Point)
- Banks 7-8: L3 Cache
- Banks 10-11: UMC (Unified Memory Controller)
- Banks 12-14: Data Fabric

If the engineer mentions structured values like specific bank numbers or MCE codes, extract them exactly.
If information is ambiguous or missing, set the field to null.
Set confidence based on how clearly the symptoms map to a single failure category.
```

```
USER:
Symptom description: "{user_symptom_text}"

Additional structured fields provided:
{json_structured_fields or "None"}

Parse this into a structured failure profile.
```

### Prompt 2: Command Ranking

```
SYSTEM:
You are a silicon debug expert analyzing AFHC/ANC test command results to help
diagnose a failing CPU. You will be given:

1. A failure profile for the current CPU under test
2. A table of historical command results from similar failed parts

Your job: Select the TOP 3 commands most likely to FAIL on this CPU, optimizing for:
- Highest historical fail rate on similar parts
- Relevance to the specific failure type and symptoms
- Speed to failure (prefer fast-running commands)
- Diversity (don't recommend 3 variants of the same test — cover different failure vectors)

You MUST output valid JSON matching this schema:
{
  "analysis": {
    "total_similar_parts": <int>,
    "match_quality": "<strong|moderate|weak>",
    "match_tier": <int>,
    "dominant_failure_pattern": "<string>"
  },
  "recommendations": [
    {
      "rank": 1,
      "command": "<full command string>",
      "confidence": <float 0.0-1.0>,
      "fail_rate_on_similar": "<string like '91.3% (21/23 parts)'>",
      "estimated_time_to_fail": "<string>",
      "reasoning": "<2-3 sentences explaining why>"
    },
    { "rank": 2, ... },
    { "rank": 3, ... }
  ],
  "fallback_suggestion": "<what to try if all 3 pass>",
  "caveats": "<any warnings or limitations>"
}

Confidence calibration:
- If 20+ similar parts with Tier 1 match → high confidence (0.8-0.95)
- If 10-20 parts with Tier 2 match → moderate confidence (0.6-0.8)
- If <10 parts or Tier 3 → low confidence (0.3-0.6)
```

```
USER:
=== CURRENT CPU FAILURE PROFILE ===
{json_parsed_profile}

=== HISTORICAL COMMAND RESULTS FROM {N} SIMILAR PARTS ===
Match criteria: {tier_description}

Command                        | Total Runs | Fails | Fail Rate | Parts Failed On
{formatted_command_table}

Select the top 3 commands to run first on this CPU to reproduce the failure as fast as possible.
```

---

## 10. Handling Edge Cases

### Edge Case 1: No Similar Parts Found

**Scenario:** Tier 3 query returns 0 results. Completely novel failure.

**Handling:**
```python
if similar_parts_count == 0:
    return {
        "status": "no_match",
        "message": "No historical parts found with similar failure profile.",
        "suggestion": "This appears to be a novel failure. Recommend running the standard full AFHC/ANC sweep.",
        "parsed_profile": parsed_profile  # Still return the LLM's parsing — it's useful context
    }
```

### Edge Case 2: Ambiguous / Low-Confidence Parsing

**Scenario:** LLM confidence < 0.5 on failure type classification.

**Handling:**
```python
if parsed_profile['confidence'] < 0.5:
    # Ask the user to clarify or provide more info
    return {
        "status": "low_confidence",
        "message": "The symptoms are ambiguous. The most likely classification is {type} but confidence is low.",
        "parsed_profile": parsed_profile,
        "clarification_needed": [
            "Can you confirm the MCA bank number?",
            "Is this a correctable or uncorrectable error?",
            "At what stage does the failure occur?"
        ]
    }
```

### Edge Case 3: All Commands Have ~Same Fail Rate

**Scenario:** Everything fails on similar parts (defective part) or nothing fails (wrong match).

**Handling:**
- If all fail rates > 80% → likely a severely defective part. Recommend the 3 *fastest* commands.
- If all fail rates < 10% → match quality is poor. Widen to next tier or flag as weak prediction.

### Edge Case 4: Free-Text-Only Input (No Structured Fields)

**Scenario:** Engineer just types: *"part is bad, keeps crashing"*

**Handling:** The LLM does its best, likely returns `UNKNOWN` failure type with low confidence. We fall through to Tier 3 broad query and flag low confidence. The system still returns something useful (the most commonly failing commands across all part types), but with appropriate caveats.

### Edge Case 5: Extremely Common Part Variant (Too Many Matches)

**Scenario:** Tier 1 returns 500+ similar parts.

**Handling:** Cap at most recent 50-100 parts (sort by timestamp desc). More recent parts are more relevant due to process/stepping consistency.

---

## 11. Feedback Loop

### How It Works

After the engineer runs the recommended commands:

```
╔════════════════════════════════════════════════════════════════╗
║  Feedback: How did the predictions perform?                    ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  #1 stream -t mem_band_max -v 1.2 (94% predicted)            ║
║      ○ FAIL ✓    ○ PASS    ○ Did not run                      ║
║                                                                ║
║  #2 mprime -t L3_stress_umc (87% predicted)                   ║
║      ○ FAIL ✓    ○ PASS    ○ Did not run                      ║
║                                                                ║
║  #3 membw -p read_write -s 4G (71% predicted)                 ║
║      ○ FAIL      ○ PASS ✓ ○ Did not run                      ║
║                                                                ║
║  Additional notes: [Stream failed within 10 seconds.       ]   ║
║                    [mprime hit different MCE - Bank 7.     ]   ║
║                                                                ║
║                      [ Submit Feedback ]                       ║
╚════════════════════════════════════════════════════════════════╝
```

### What Feedback Gives Us

1. **Immediate value:** Updates the `sdc_predictions` table → we can measure prediction accuracy over time
2. **Training data:** Each feedback creates validated (symptom, command, result) rows for the future ML model
3. **Prompt improvement signal:** If predictions are consistently wrong for certain failure types, we tune the LLM prompts

### Accuracy Tracking

```sql
-- How accurate are our predictions this month?
SELECT
    DATE_TRUNC('month', prediction_timestamp) as month,
    COUNT(*) as total_predictions,
    
    -- Hit@3: did at least one of our 3 predictions actually fail?
    SUM(CASE WHEN rank1_actual_result='FAIL' 
              OR rank2_actual_result='FAIL' 
              OR rank3_actual_result='FAIL' THEN 1 ELSE 0 END) as hit_at_3,
    
    -- Hit@1: was our top prediction correct?
    SUM(CASE WHEN rank1_actual_result='FAIL' THEN 1 ELSE 0 END) as hit_at_1,
    
    -- Hit@3 rate
    ROUND(hit_at_3::FLOAT / total_predictions * 100, 1) as hit_at_3_pct,
    ROUND(hit_at_1::FLOAT / total_predictions * 100, 1) as hit_at_1_pct

FROM sdc_predictions
WHERE rank1_actual_result IS NOT NULL  -- only scored predictions
GROUP BY 1
ORDER BY 1 DESC;
```

---

## 12. Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **UI** | Web (HTML/JS) or Streamlit | Fast to build, accessible from any machine on the debug bench |
| **Backend** | Python + FastAPI | Lightweight, async, easy LLM integration |
| **LLM** | GPT-4o / Claude / internal LLM | Structured output support, strong reasoning, fast |
| **Database** | Snowflake (existing) | Data already lives here — no migration needed |
| **LLM Framework** | LangChain or raw API calls | For structured output parsing + retry logic |
| **Deployment** | Docker container | Portable, easy to deploy on-prem |
| **Feedback Storage** | Snowflake (same DB) | Keep everything in one place |

### Minimal Dependency Stack

```
python >= 3.10
fastapi
uvicorn
snowflake-connector-python
openai (or anthropic or litellm)
pydantic  # for structured output validation
jinja2    # for prompt templating
```

---

## 13. Implementation Plan

### Week 1: Core Pipeline (Backend Only)

- [ ] Set up FastAPI project scaffold
- [ ] Implement Snowflake connector + test queries
- [ ] Write LLM parsing prompt (Step 2) + test on 10 sample symptom descriptions
- [ ] Write database query layer (tiered queries)
- [ ] Write command aggregation logic
- [ ] Write LLM ranking prompt (Step 4) + test on aggregated data
- [ ] Wire end-to-end: symptom text → parsed profile → DB query → ranked commands
- [ ] Test with 5-10 real historical cases (manually verify predictions make sense)

### Week 2: UI + Feedback + Polish

- [ ] Build web UI (symptom intake form)
- [ ] Connect UI → backend API
- [ ] Build results display (ranked commands + explanations)
- [ ] Implement feedback form UI
- [ ] Wire feedback → `sdc_predictions` table writes
- [ ] Add error handling for all edge cases
- [ ] Build accuracy tracking dashboard (SQL queries + simple chart)
- [ ] Deploy containerized version for pilot testing

### Week 3: Pilot with Engineers

- [ ] Deploy to 2-3 debug engineers
- [ ] Collect feedback on prediction quality
- [ ] Tune prompts based on failure cases
- [ ] Measure Hit@3 accuracy on real predictions
- [ ] Document lessons learned

---

## Summary

This first-pass approach is intentionally **simple and fast to ship**:

```
User Input → LLM Parse → Database Query → LLM Rank → Top 3 Commands
```

**No model training. No feature engineering. No hyperparameter tuning.** Just an LLM that understands hardware + a database full of history + smart prompt engineering.

The key bet: **an LLM with access to historical evidence can reason about failure patterns well enough to beat an engineer's unaided intuition, especially for less experienced engineers or unfamiliar failure modes.**

The feedback loop then gives us the data to build a custom ML model in Phase 2 — but only after we've validated the approach works in practice.
