"""FAILURE_TAXONOMY — maps failure categories to MCE banks and symptoms."""

FAILURE_TAXONOMY: dict[str, dict] = {
    "UMC_MEMORY_CONTROLLER": {
        "banks": [10, 11],
        "description": "Unified Memory Controller faults",
        "typical_symptoms": ["memory bandwidth failures", "ECC errors", "DRAM access faults"],
    },
    "EXECUTION_UNIT": {
        "banks": [5],
        "description": "Integer/ALU execution pipeline faults",
        "typical_symptoms": ["compute errors", "ALU miscompare", "integer workload failures"],
    },
    "FLOATING_POINT": {
        "banks": [6],
        "description": "FP/FMA unit faults",
        "typical_symptoms": ["FP exceptions", "FMA errors", "linpack failures"],
    },
    "LOAD_STORE": {
        "banks": [0],
        "description": "Load-Store unit faults",
        "typical_symptoms": ["data corruption on load/store", "cache coherency", "memory ordering"],
    },
    "INSTRUCTION_FETCH": {
        "banks": [1],
        "description": "Instruction fetch / branch prediction faults",
        "typical_symptoms": ["instruction corruption", "branch mispredict", "IF pipeline errors"],
    },
    "COMBINED_UNIT": {
        "banks": [2],
        "description": "Combined unit (mixed integer + FP path) faults",
        "typical_symptoms": ["mixed workload failures", "scheduler errors"],
    },
    "L2_CACHE": {
        "banks": [3],
        "description": "L2 cache faults",
        "typical_symptoms": ["cache parity", "L2 ECC", "stale cache line"],
    },
    "L3_CACHE": {
        "banks": [7, 8],
        "description": "L3 / Last-level cache faults",
        "typical_symptoms": ["L3 tag errors", "snoop filter faults", "LLC access failures"],
    },
    "FABRIC_INTERCONNECT": {
        "banks": [12, 13, 14],
        "description": "Data Fabric / Interconnect faults",
        "typical_symptoms": ["cross-CCD failures", "NUMA errors", "fabric timeout"],
    },
    "POWER_MANAGEMENT": {
        "banks": [],
        "description": "Voltage / frequency / power state faults",
        "typical_symptoms": ["VID errors", "P-state transitions", "voltage droop", "clock stretch"],
    },
    "BOOT_FAILURE": {
        "banks": [],
        "description": "Fails to POST or boot OS",
        "typical_symptoms": ["no POST", "BSOD on boot", "hang at BIOS", "reset loop"],
    },
    "UNKNOWN": {
        "banks": [],
        "description": "Cannot confidently classify",
        "typical_symptoms": [],
    },
}


# Reverse map: bank number → failure type(s)
BANK_TO_FAILURE_TYPE: dict[int, list[str]] = {}
for ftype, info in FAILURE_TAXONOMY.items():
    for bank in info["banks"]:
        BANK_TO_FAILURE_TYPE.setdefault(bank, []).append(ftype)


def get_banks_for_failure_type(failure_type: str) -> list[int]:
    """Return all MCE banks associated with a failure type."""
    entry = FAILURE_TAXONOMY.get(failure_type)
    return entry["banks"] if entry else []
