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


# =============================================================================
# REALISTIC INPUT FIXTURES
# UMC is from a real production triage. Others are synthetic but follow
# the same format engineers actually paste into the tool.
# =============================================================================

_SYMPTOM_UMC = """\
Stepping: B0

BIOS Version: TVOT1007B_DPPM_WA_BO_w_ucode_patches.tar.gz

OPN: 100-000001463
Serial P0: 9MD8775M60120
Serial P1: null
Failing Socket: P0
Failing Serial Number: 9MD8775M60120
Logical Core: 0
SoC CCD: 0
Physical CCD Core: 0
Physical Core Thread: 0
Instance: instUMCWPHY1UMC_n1_umc0

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 22
ErrorCodeExt: DramEccErr
MCA Status: 0xdc2040000400011b
MCA Syndrome: 0x8a5a0a000a800808
MCA Addr: 0x00000000299ff8c0
MCA IPID: 0x0000009600150f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:0 (1a:11:0) MC22_STATUS[Over|CE|MiscV|AddrV|-|-|SyndV|CECC|-|-|-]: 0xdc2040000400011b
[Hardware Error]: Error Addr: 0x00000000299ff8c0
[Hardware Error]: PPIN: 0x02b6f7a49d818078

Test Start Time: 2026-03-09 07:06:28.858000+00:00
Test End Time: 2026-03-09 08:54:58.003000+00:00
TTF: 0.00 hrs
TTF Failing Suite: Data is still populating, try again later, or failing test phase is not a stress test
TTF Failing Suite Cuml: Unknown
TTF Repro: NA
TTF Breakdown:
NA

Failing Command: /opt/prism/932116/894933/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 79 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 80 81 82 83 84 85 86 87 88 89 90 91 92 93 205 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 206 207 208 209 210 211 212 213 214 215 216 217 218 219
Previous Command: /opt/prism/932116/894933/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204
Workload: NA
Number of times failing command ran: Unknown

CPU Governor: NA
Aging GB Removed: true
APerf Freq MHz:
APerf IPC: Unknown

Station Name: volcano-4761
Parent Schedule ID: 932116
Rerun Number: 0
Workflow Run ID: 894933
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/932116
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/932116/894933
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/5cb7b90b-1b93-11f1-ade3-000d3a137703
Failing Iteration: Unknown
SUT Uptime: 2026-03-09 07:39:55
BMC Uptime: 2026-03-09 07:20:16

MCA Decoder Information:
{
  "Block": "UMC",
  "Bank": "UMCWPHY1UMC_n1",
  "Instance": "_instUMCWPHY1UMC_n1_umc0",
  "ErrorCodeExt": {
    "DramEccErr": {
      "ADDR": {
        "NormalizedAddress": "0x0"
      },
      "SYND": {
        "SoftwareManagedBadSymbolIdError": "0x0",
        "HardwareHistoryError": "0x0",
        "Symbol": "0x0",
        "CID": "0x0",
        "SubChannel": "0x0",
        "ChipSelect": "0x0"
      }
    }
  },
  "Status": {
    "Address": "0xdc2040000400011b",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x1",
      "PCC": "0x0",
      "SyndV": "0x1",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x0",
      "ErrorCode": "0x11b"
    }
  },
  "IPID": {
    "Address": "0x0000009600150f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x96",
      "InstanceId": "0x150f00"
    }
  },
  "SYND": {
    "Address": "0x8a5a0a000a800808",
    "Decode": {
      "Syndrome": "0x8a5a0a00",
      "Type": "0x0",
      "ErrorPriority": "0x2",
      "Length": "0x20",
      "ErrorInformation": "0x808"
    }
  },
  "ADDR": {
    "Address": "0x00000000299ff8c0",
    "Decode": {
      "ErrorAddr": "0x299ff8c0"
    }
  }
}
"""

_SYMPTOM_L3 = """\
Stepping: B0

BIOS Version: RMB1009A_DPPM_prod.tar.gz

OPN: 100-000001560
Serial P0: 9MD9112K40085
Serial P1: 9MD9112K40092
Failing Socket: P0
Failing Serial Number: 9MD9112K40085
Logical Core: 45
SoC CCD: 3
Physical CCD Core: 5
Physical Core Thread: 1
Instance: instL3_0_CCD3

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 8
ErrorCodeExt: L3CacheDataErr
MCA Status: 0xdc3040000604010b
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x000000018a3c7100
MCA IPID: 0x000000b000080200
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:45 (1a:11:0) MC8_STATUS[Over|CE|MiscV|AddrV|-|-|SyndV|CECC|-|-|-]: 0xdc3040000604010b
[Hardware Error]: Error Addr: 0x000000018a3c7100
[Hardware Error]: PPIN: 0x03a1e2b54d719021

Test Start Time: 2026-02-28 14:22:10.000000+00:00
Test End Time: 2026-02-28 16:05:33.000000+00:00
TTF: 1.72 hrs
TTF Failing Suite: MaxCoreStim
TTF Failing Suite Cuml: 1.72 hrs
TTF Repro: First occurrence
TTF Breakdown:
MaxCoreStim: 1.72 hrs

Failing Command: /opt/prism/845210/801122/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 40 41 42 43 44 45 46 47
Previous Command: /opt/prism/845210/801122/tools/TIMSUITE/AMPTTK/AMPTTKv3.70 -test L3_CacheFill -duration 600 -threads 8
Workload: MaxCoreStim v17.6.13.5
Number of times failing command ran: 3

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3450
APerf IPC: 1.82

Station Name: granite-2190
Parent Schedule ID: 845210
Rerun Number: 0
Workflow Run ID: 801122
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/845210
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/845210/801122
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/a22c4e01-e7b1-11ef-bbb3-000d3a137703
Failing Iteration: 3
SUT Uptime: 2026-02-28 14:30:22
BMC Uptime: 2026-02-28 14:10:05

MCA Decoder Information:
{
  "Block": "L3",
  "Bank": "L3_0_CCD3",
  "Instance": "_instL3_0_CCD3",
  "ErrorCodeExt": {
    "L3CacheDataErr": {
      "ADDR": {
        "NormalizedAddress": "0x18a3c7100"
      },
      "SYND": {
        "Way": "0x5",
        "ArrayId": "0x0"
      }
    }
  },
  "Status": {
    "Address": "0xdc3040000604010b",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x1",
      "PCC": "0x0",
      "SyndV": "0x1",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x6",
      "ErrorCode": "0x10b"
    }
  },
  "IPID": {
    "Address": "0x000000b000080200",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0xb0",
      "InstanceId": "0x80200"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x000000018a3c7100",
    "Decode": {
      "ErrorAddr": "0x18a3c7100"
    }
  }
}
"""

_SYMPTOM_LS = """\
Stepping: B0

BIOS Version: RMB1009A_DPPM_prod.tar.gz

OPN: 100-000001463
Serial P0: 9MD8830R50044
Serial P1: 9MD8830R50051
Failing Socket: P1
Failing Serial Number: 9MD8830R50051
Logical Core: 189
SoC CCD: 11
Physical CCD Core: 13
Physical Core Thread: 1
Instance: instLS_core189

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 0
ErrorCodeExt: SystemReadDataErr
MCA Status: 0xdc204000000d0175
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x00000003f1a82440
MCA IPID: 0x0000000000010f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:189 (1a:11:0) MC0_STATUS[Over|CE|MiscV|AddrV|-|-|-|CECC|-|-|-]: 0xdc204000000d0175
[Hardware Error]: Error Addr: 0x00000003f1a82440
[Hardware Error]: PPIN: 0x04c2d1b89e320155

Test Start Time: 2026-03-01 09:15:42.000000+00:00
Test End Time: 2026-03-01 11:30:18.000000+00:00
TTF: 2.24 hrs
TTF Failing Suite: MaxCoreStim
TTF Failing Suite Cuml: 2.24 hrs
TTF Repro: NA
TTF Breakdown:
MaxCoreStim: 2.24 hrs

Failing Command: /opt/prism/851440/805331/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 184 185 186 187 188 189 190 191
Previous Command: /opt/prism/851440/805331/tools/TIMSUITE/AMPTTK/AMPTTKv3.70 -test Hammer_LS -duration 300 -threads 16
Workload: MaxCoreStim v17.6.13.5
Number of times failing command ran: 5

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3200
APerf IPC: 1.65

Station Name: basalt-3502
Parent Schedule ID: 851440
Rerun Number: 0
Workflow Run ID: 805331
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/851440
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/851440/805331
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/b33d5f02-e811-11ef-bbb3-000d3a137703
Failing Iteration: 5
SUT Uptime: 2026-03-01 09:22:11
BMC Uptime: 2026-03-01 09:05:33

MCA Decoder Information:
{
  "Block": "LS",
  "Bank": "LS_core189",
  "Instance": "_instLS_core189",
  "ErrorCodeExt": {
    "SystemReadDataErr": {
      "ADDR": {
        "NormalizedAddress": "0x3f1a82440"
      },
      "SYND": {}
    }
  },
  "Status": {
    "Address": "0xdc204000000d0175",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x0",
      "AddrV": "0x1",
      "PCC": "0x0",
      "SyndV": "0x0",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0xd",
      "ErrorCode": "0x175"
    }
  },
  "IPID": {
    "Address": "0x0000000000010f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x00",
      "InstanceId": "0x10f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x00000003f1a82440",
    "Decode": {
      "ErrorAddr": "0x3f1a82440"
    }
  }
}
"""

_SYMPTOM_PIE = """\
Stepping: B0

BIOS Version: TVOT1007B_DPPM_WA_BO_w_ucode_patches.tar.gz

OPN: 100-000001463
Serial P0: 9MD8901T70033
Serial P1: 9MD8901T70040
Failing Socket: P0
Failing Serial Number: 9MD8901T70033
Logical Core: 12
SoC CCD: 0
Physical CCD Core: 4
Physical Core Thread: 0
Instance: instPIE0

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 30
ErrorCodeExt: HardwareAssert
MCA Status: 0xdc20400000050072
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x0000000000000000
MCA IPID: 0x0000012e00020f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:12 (1a:11:0) MC30_STATUS[Over|CE|MiscV|-|-|-|-|CECC|-|-|-]: 0xdc20400000050072
[Hardware Error]: PPIN: 0x05d3e0c7af430188

Test Start Time: 2026-03-04 20:14:05.000000+00:00
Test End Time: 2026-03-04 22:48:12.000000+00:00
TTF: 0.55 hrs
TTF Failing Suite: MaxCoreStim
TTF Failing Suite Cuml: 0.55 hrs
TTF Repro: NA
TTF Breakdown:
MaxCoreStim: 0.55 hrs

Failing Command: /opt/prism/890122/860044/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 8 9 10 11 12 13 14 15
Previous Command: /opt/prism/890122/860044/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 0 1 2 3 4 5 6 7
Workload: MaxCoreStim v17.6.13.5
Number of times failing command ran: 2

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3550
APerf IPC: Unknown

Station Name: tundra-5120
Parent Schedule ID: 890122
Rerun Number: 0
Workflow Run ID: 860044
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/890122
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/890122/860044
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/c44e7012-f912-11ef-bbb3-000d3a137703
Failing Iteration: 2
SUT Uptime: 2026-03-04 20:22:30
BMC Uptime: 2026-03-04 20:02:18

MCA Decoder Information:
{
  "Block": "PIE",
  "Bank": "PIE0",
  "Instance": "_instPIE0",
  "ErrorCodeExt": {
    "HardwareAssert": {
      "ADDR": {},
      "SYND": {}
    }
  },
  "Status": {
    "Address": "0xdc20400000050072",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x0",
      "PCC": "0x0",
      "SyndV": "0x0",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x5",
      "ErrorCode": "0x72"
    }
  },
  "IPID": {
    "Address": "0x0000012e00020f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x12e",
      "InstanceId": "0x20f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x0000000000000000",
    "Decode": {
      "ErrorAddr": "0x0"
    }
  }
}
"""

_SYMPTOM_L2 = """\
Stepping: B0

BIOS Version: RMB1009A_DPPM_prod.tar.gz

OPN: 100-000001560
Serial P0: 9MD9204N30021
Serial P1: null
Failing Socket: P0
Failing Serial Number: 9MD9204N30021
Logical Core: 67
SoC CCD: 4
Physical CCD Core: 3
Physical Core Thread: 1
Instance: instL2_core67

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 3
ErrorCodeExt: L2CacheDataErr
MCA Status: 0x9c30400004020166
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x0000000245b01a80
MCA IPID: 0x0000004300030f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:67 (1a:11:0) MC3_STATUS[CE|MiscV|AddrV|-|-|-|-|CECC|-|-|-]: 0x9c30400004020166
[Hardware Error]: Error Addr: 0x0000000245b01a80
[Hardware Error]: PPIN: 0x06a4f3c10e521099

Test Start Time: 2026-03-06 03:40:15.000000+00:00
Test End Time: 2026-03-06 05:12:48.000000+00:00
TTF: 1.54 hrs
TTF Failing Suite: MaxCoreStim
TTF Failing Suite Cuml: 1.54 hrs
TTF Repro: NA
TTF Breakdown:
MaxCoreStim: 1.54 hrs

Failing Command: /opt/prism/910233/875509/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 64 65 66 67 68 69 70 71
Previous Command: /opt/prism/910233/875509/tools/TIMSUITE/DIFECT/DIFECT_v2.4.1 -test L2_HammerCheck -duration 1200 -cores 64 65 66 67 68 69 70 71
Workload: MaxCoreStim v17.6.13.5
Number of times failing command ran: 4

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3300
APerf IPC: 1.71

Station Name: obsidian-1847
Parent Schedule ID: 910233
Rerun Number: 0
Workflow Run ID: 875509
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/910233
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/910233/875509
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/d55f8113-0a23-11f0-bbb3-000d3a137703
Failing Iteration: 4
SUT Uptime: 2026-03-06 03:48:02
BMC Uptime: 2026-03-06 03:30:45

MCA Decoder Information:
{
  "Block": "L2",
  "Bank": "L2_core67",
  "Instance": "_instL2_core67",
  "ErrorCodeExt": {
    "L2CacheDataErr": {
      "ADDR": {
        "NormalizedAddress": "0x245b01a80"
      },
      "SYND": {
        "Way": "0x3",
        "ArrayId": "0x1"
      }
    }
  },
  "Status": {
    "Address": "0x9c30400004020166",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x0",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x1",
      "PCC": "0x0",
      "SyndV": "0x0",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x4",
      "ErrorCode": "0x166"
    }
  },
  "IPID": {
    "Address": "0x0000004300030f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x43",
      "InstanceId": "0x30f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x0000000245b01a80",
    "Decode": {
      "ErrorAddr": "0x245b01a80"
    }
  }
}
"""

_SYMPTOM_DE = """\
Stepping: B0

BIOS Version: RMB1009A_DPPM_prod.tar.gz

OPN: 100-000001560
Serial P0: 9MD9055L20078
Serial P1: 9MD9055L20085
Failing Socket: P1
Failing Serial Number: 9MD9055L20085
Logical Core: 142
SoC CCD: 8
Physical CCD Core: 14
Physical Core Thread: 0
Instance: instDE_core142

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 1
ErrorCodeExt: DcTagErr
MCA Status: 0xdc20400000030071
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x0000000000000000
MCA IPID: 0x0000000100010f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:142 (1a:11:0) MC1_STATUS[Over|CE|MiscV|-|-|-|-|CECC|-|-|-]: 0xdc20400000030071
[Hardware Error]: PPIN: 0x07b501d21f630177

Test Start Time: 2026-03-02 11:05:30.000000+00:00
Test End Time: 2026-03-02 13:22:15.000000+00:00
TTF: 0.88 hrs
TTF Failing Suite: AMPTTK
TTF Failing Suite Cuml: 0.88 hrs
TTF Repro: NA
TTF Breakdown:
AMPTTK: 0.88 hrs

Failing Command: /opt/prism/862110/820455/tools/TIMSUITE/AMPTTK/AMPTTKv3.70 -test Decode_Stress -duration 600 -threads 16 -cores 136 137 138 139 140 141 142 143
Previous Command: /opt/prism/862110/820455/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 136 137 138 139 140 141 142 143
Workload: AMPTTKv3.70
Number of times failing command ran: 2

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3400
APerf IPC: 1.58

Station Name: marble-4001
Parent Schedule ID: 862110
Rerun Number: 0
Workflow Run ID: 820455
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/862110
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/862110/820455
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/e66f9214-eb22-11ef-bbb3-000d3a137703
Failing Iteration: 2
SUT Uptime: 2026-03-02 11:12:45
BMC Uptime: 2026-03-02 10:55:30

MCA Decoder Information:
{
  "Block": "IF",
  "Bank": "IF_core142",
  "Instance": "_instDE_core142",
  "ErrorCodeExt": {
    "DcTagErr": {
      "ADDR": {},
      "SYND": {}
    }
  },
  "Status": {
    "Address": "0xdc20400000030071",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x0",
      "PCC": "0x0",
      "SyndV": "0x0",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x3",
      "ErrorCode": "0x71"
    }
  },
  "IPID": {
    "Address": "0x0000000100010f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x01",
      "InstanceId": "0x10f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x0000000000000000",
    "Decode": {
      "ErrorAddr": "0x0"
    }
  }
}
"""

_SYMPTOM_EX = """\
Stepping: A0

BIOS Version: TIT_0.14.2_DPPM_prod.tar.gz

OPN: 100-000001322
Serial P0: 9MD7441G80010
Serial P1: 9MD7441G80017
Failing Socket: P0
Failing Serial Number: 9MD7441G80010
Logical Core: 3
SoC CCD: 0
Physical CCD Core: 3
Physical Core Thread: 0
Instance: instEX_core3

Defect Type: MCE
MCE Type: Uncorrectable MCE
Bank: 5
ErrorCodeExt: WatchdogTimeout
MCA Status: 0xbc20400000060135
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x0000000000000000
MCA IPID: 0x0000005000050f00
Fatal: true
Corrective Action: TBD

Failing log:
[Hardware Error]: Machine check error, action required.
[Hardware Error]: CPU:3 (1a:11:0) MC5_STATUS[Val|UC|EN|MiscV|-|-|-|-|PCC|-|-]: 0xbc20400000060135
[Hardware Error]: This system has experienced an uncorrectable hardware error
[Hardware Error]: PPIN: 0x08c6e4d30a740200

Test Start Time: 2026-02-20 06:30:00.000000+00:00
Test End Time: 2026-02-20 07:15:22.000000+00:00
TTF: 0.75 hrs
TTF Failing Suite: AMPTTK
TTF Failing Suite Cuml: 0.75 hrs
TTF Repro: 2nd occurrence
TTF Breakdown:
AMPTTK: 0.75 hrs

Failing Command: /opt/prism/780505/745010/tools/TIMSUITE/AMPTTK/AMPTTKv3.70 -test EX_WatchdogHammer -duration 1800 -threads 4 -cores 0 1 2 3
Previous Command: /opt/prism/780505/745010/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 0 1 2 3 4 5 6 7
Workload: AMPTTKv3.70
Number of times failing command ran: 2

CPU Governor: performance
Aging GB Removed: false
APerf Freq MHz: 2800
APerf IPC: 1.42

Station Name: titanite-0091
Parent Schedule ID: 780505
Rerun Number: 1
Workflow Run ID: 745010
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/780505
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/780505/745010
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/f77fa325-d433-11ef-bbb3-000d3a137703
Failing Iteration: 2
SUT Uptime: 2026-02-20 06:38:10
BMC Uptime: 2026-02-20 06:20:02

MCA Decoder Information:
{
  "Block": "EX",
  "Bank": "EX_core3",
  "Instance": "_instEX_core3",
  "ErrorCodeExt": {
    "WatchdogTimeout": {
      "ADDR": {},
      "SYND": {}
    }
  },
  "Status": {
    "Address": "0xbc20400000060135",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x0",
      "UC": "0x1",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x0",
      "PCC": "0x1",
      "SyndV": "0x0",
      "CECC": "0x0",
      "UECC": "0x1",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x6",
      "ErrorCode": "0x135"
    }
  },
  "IPID": {
    "Address": "0x0000005000050f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x50",
      "InstanceId": "0x50f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x0000000000000000",
    "Decode": {
      "ErrorAddr": "0x0"
    }
  }
}
"""

_SYMPTOM_GMI = """\
Stepping: B0

BIOS Version: QRZ1004B_DPPM_prod.tar.gz

OPN: 100-000001644
Serial P0: 9MD9308P10055
Serial P1: 9MD9308P10062
Failing Socket: P0
Failing Serial Number: 9MD9308P10055
Logical Core: 88
SoC CCD: 5
Physical CCD Core: 8
Physical Core Thread: 0
Instance: instPCS_GMI0

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 17
ErrorCodeExt: GmiLinkErr
MCA Status: 0xdc20400000040111
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x0000000000000000
MCA IPID: 0x000000a700110f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:88 (1a:11:0) MC17_STATUS[Over|CE|MiscV|-|-|-|-|CECC|-|-|-]: 0xdc20400000040111
[Hardware Error]: PPIN: 0x09d7f5e41b850233

Test Start Time: 2026-03-07 18:02:30.000000+00:00
Test End Time: 2026-03-07 21:15:44.000000+00:00
TTF: 1.10 hrs
TTF Failing Suite: miidct
TTF Failing Suite Cuml: 1.10 hrs
TTF Repro: NA
TTF Breakdown:
miidct: 1.10 hrs

Failing Command: /opt/prism/920555/882203/tools/TIMSUITE/miidct/miidct_v5.2.8 -test GMI_LinkStress -duration 3600 -iterations 100
Previous Command: /opt/prism/920555/882203/tools/TIMSUITE/AMPTTK/AMPTTKv3.70 -test Fabric_Hammer -duration 600 -threads 16
Workload: miidct v5.2.8
Number of times failing command ran: 1

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3100
APerf IPC: 1.55

Station Name: quartz-7703
Parent Schedule ID: 920555
Rerun Number: 0
Workflow Run ID: 882203
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/920555
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/920555/882203
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/a88b0326-1534-11f0-bbb3-000d3a137703
Failing Iteration: 1
SUT Uptime: 2026-03-07 18:10:15
BMC Uptime: 2026-03-07 17:50:02

MCA Decoder Information:
{
  "Block": "PCS_GMI",
  "Bank": "PCS_GMI0",
  "Instance": "_instPCS_GMI0",
  "ErrorCodeExt": {
    "GmiLinkErr": {
      "ADDR": {},
      "SYND": {}
    }
  },
  "Status": {
    "Address": "0xdc20400000040111",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x0",
      "PCC": "0x0",
      "SyndV": "0x0",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x4",
      "ErrorCode": "0x111"
    }
  },
  "IPID": {
    "Address": "0x000000a700110f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0xa7",
      "InstanceId": "0x110f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x0000000000000000",
    "Decode": {
      "ErrorAddr": "0x0"
    }
  }
}
"""

_SYMPTOM_PSP = """\
Stepping: B0

BIOS Version: TVOT1007B_DPPM_WA_BO_w_ucode_patches.tar.gz

OPN: 100-000001463
Serial P0: 9MD8660S90110
Serial P1: 9MD8660S90117
Failing Socket: P1
Failing Serial Number: 9MD8660S90117
Logical Core: 200
SoC CCD: 12
Physical CCD Core: 8
Physical Core Thread: 0
Instance: instPSP0

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 29
ErrorCodeExt: PspSecureBootErr
MCA Status: 0xdc20400000070062
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x0000000000000000
MCA IPID: 0x0000011d001d0f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:200 (1a:11:0) MC29_STATUS[Over|CE|MiscV|-|-|-|-|CECC|-|-|-]: 0xdc20400000070062
[Hardware Error]: PPIN: 0x0ae806f52c960266

Test Start Time: 2026-03-05 15:30:00.000000+00:00
Test End Time: 2026-03-05 18:45:22.000000+00:00
TTF: 0.42 hrs
TTF Failing Suite: MaxCoreStim
TTF Failing Suite Cuml: 0.42 hrs
TTF Repro: NA
TTF Breakdown:
MaxCoreStim: 0.42 hrs

Failing Command: /opt/prism/901888/868110/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207
Previous Command: /opt/prism/901888/868110/tools/TIMSUITE/AMPTTK/AMPTTKv3.70 -test PSP_SecureBoot -duration 300 -threads 8
Workload: MaxCoreStim v17.6.13.5
Number of times failing command ran: 1

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3500
APerf IPC: 1.80

Station Name: glacier-6290
Parent Schedule ID: 901888
Rerun Number: 0
Workflow Run ID: 868110
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/901888
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/901888/868110
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/b99c1437-0233-11f0-bbb3-000d3a137703
Failing Iteration: 1
SUT Uptime: 2026-03-05 15:38:20
BMC Uptime: 2026-03-05 15:18:10

MCA Decoder Information:
{
  "Block": "PSP",
  "Bank": "PSP0",
  "Instance": "_instPSP0",
  "ErrorCodeExt": {
    "PspSecureBootErr": {
      "ADDR": {},
      "SYND": {}
    }
  },
  "Status": {
    "Address": "0xdc20400000070062",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x0",
      "PCC": "0x0",
      "SyndV": "0x0",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x7",
      "ErrorCode": "0x62"
    }
  },
  "IPID": {
    "Address": "0x0000011d001d0f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x11d",
      "InstanceId": "0x1d0f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x0000000000000000",
    "Decode": {
      "ErrorAddr": "0x0"
    }
  }
}
"""

_SYMPTOM_FP = """\
Stepping: B0

BIOS Version: RMB1009A_DPPM_prod.tar.gz

OPN: 100-000001560
Serial P0: 9MD9150M50099
Serial P1: null
Failing Socket: P0
Failing Serial Number: 9MD9150M50099
Logical Core: 22
SoC CCD: 1
Physical CCD Core: 6
Physical Core Thread: 0
Instance: instFP_core22

Defect Type: MCE
MCE Type: Correctable MCE
Bank: 6
ErrorCodeExt: FpRegFileParityErr
MCA Status: 0xdc20400000020136
MCA Syndrome: 0x0000000000000000
MCA Addr: 0x0000000000000000
MCA IPID: 0x0000006000060f00
Fatal: false
Corrective Action: TBD

Failing log:
[Hardware Error]: Corrected error, no action required.
[Hardware Error]: CPU:22 (1a:11:0) MC6_STATUS[Over|CE|MiscV|-|-|-|-|CECC|-|-|-]: 0xdc20400000020136
[Hardware Error]: PPIN: 0x0bf917064d070299

Test Start Time: 2026-03-08 22:10:05.000000+00:00
Test End Time: 2026-03-09 00:35:10.000000+00:00
TTF: 1.95 hrs
TTF Failing Suite: MaxCoreStim
TTF Failing Suite Cuml: 1.95 hrs
TTF Repro: NA
TTF Breakdown:
MaxCoreStim: 1.95 hrs

Failing Command: /opt/prism/928044/891200/tools/TIMSUITE/MaxCoreStim/MaxCoreStim_v17.6.13.5 -tox 15 -pwrTest 32,62 -idleTest 2 -interval 10ms -intervalPerSync 40 -pwrIntervalPct 99 -msr -cores 16 17 18 19 20 21 22 23
Previous Command: /opt/prism/928044/891200/tools/TIMSUITE/AMPTTK/AMPTTKv3.70 -test FP_Stress -duration 600 -threads 8
Workload: MaxCoreStim v17.6.13.5
Number of times failing command ran: 6

CPU Governor: performance
Aging GB Removed: true
APerf Freq MHz: 3350
APerf IPC: 1.69

Station Name: prism-4422
Parent Schedule ID: 928044
Rerun Number: 0
Workflow Run ID: 891200
Suite: Run_DART_SLT_Commands
Link to Workflow Run: https://prism.amd.com/prism-web/workflow-runs/workflow/928044
Link to log: https://prism.amd.com/prism-web/workflow-runs/logs/928044/891200
Triage Link: http://serverdebugtriage.amd.com/viewer/triage/cab41548-1c44-11f1-bbb3-000d3a137703
Failing Iteration: 6
SUT Uptime: 2026-03-08 22:18:30
BMC Uptime: 2026-03-08 22:00:15

MCA Decoder Information:
{
  "Block": "FP",
  "Bank": "FP_core22",
  "Instance": "_instFP_core22",
  "ErrorCodeExt": {
    "FpRegFileParityErr": {
      "ADDR": {},
      "SYND": {}
    }
  },
  "Status": {
    "Address": "0xdc20400000020136",
    "Decode": {
      "Val": "0x1",
      "Overflow": "0x1",
      "UC": "0x0",
      "EN": "0x1",
      "MiscV": "0x1",
      "AddrV": "0x0",
      "PCC": "0x0",
      "SyndV": "0x0",
      "CECC": "0x1",
      "UECC": "0x0",
      "Deferred": "0x0",
      "Poison": "0x0",
      "ErrorCodeExt": "0x2",
      "ErrorCode": "0x136"
    }
  },
  "IPID": {
    "Address": "0x0000006000060f00",
    "Decode": {
      "McaType": "0x0",
      "HardwareId": "0x60",
      "InstanceId": "0x60f00"
    }
  },
  "SYND": {
    "Address": "0x0000000000000000",
    "Decode": {
      "Syndrome": "0x0",
      "Type": "0x0",
      "ErrorPriority": "0x0",
      "Length": "0x0",
      "ErrorInformation": "0x0"
    }
  },
  "ADDR": {
    "Address": "0x0000000000000000",
    "Decode": {
      "ErrorAddr": "0x0"
    }
  }
}
"""


GROUND_TRUTH: list[GroundTruthEntry] = [
    GroundTruthEntry(
        bank="UMC",
        description="Unified Memory Controller — most common failure in MSFT fleet",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT", "miidct"],
        total_fails=995_000,
        symptom_text=_SYMPTOM_UMC,
    ),
    GroundTruthEntry(
        bank="L3",
        description="L3 Cache errors — dominant failure in L3 debug",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT"],
        total_fails=5_900,
        symptom_text=_SYMPTOM_L3,
    ),
    GroundTruthEntry(
        bank="LS",
        description="Load/Store unit errors",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT", "miidct"],
        total_fails=4_700,
        symptom_text=_SYMPTOM_LS,
    ),
    GroundTruthEntry(
        bank="PIE",
        description="PIE (Power, Interrupts, Etc) errors",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["miidct", "DIFECT"],
        total_fails=6_300,
        symptom_text=_SYMPTOM_PIE,
    ),
    GroundTruthEntry(
        bank="L2",
        description="L2 Cache errors",
        expected_tools=["MaxCoreStim", "DIFECT", "AMPTTK"],
        secondary_tools=[],
        total_fails=340,
        symptom_text=_SYMPTOM_L2,
    ),
    GroundTruthEntry(
        bank="DE",
        description="Decode unit errors",
        expected_tools=["MaxCoreStim", "AMPTTK", "DIFECT"],
        secondary_tools=[],
        total_fails=240,
        symptom_text=_SYMPTOM_DE,
    ),
    GroundTruthEntry(
        bank="EX",
        description="Execution unit errors (bank 5)",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT"],
        total_fails=50,
        symptom_text=_SYMPTOM_EX,
    ),
    GroundTruthEntry(
        bank="GMI",
        description="GMI/PCS_GMI interconnect errors (bank 17/18)",
        expected_tools=["AMPTTK", "miidct", "DIFECT"],
        secondary_tools=["MaxCoreStim"],
        total_fails=100,
        symptom_text=_SYMPTOM_GMI,
    ),
    GroundTruthEntry(
        bank="PSP",
        description="Platform Security Processor errors",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=[],
        total_fails=1_500,
        symptom_text=_SYMPTOM_PSP,
    ),
    GroundTruthEntry(
        bank="FP",
        description="Floating Point unit errors (bank 6)",
        expected_tools=["MaxCoreStim", "AMPTTK"],
        secondary_tools=["DIFECT"],
        total_fails=15,
        symptom_text=_SYMPTOM_FP,
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
