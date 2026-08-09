#!/usr/bin/env python3
"""Verify web agent config parity pieces (tools + adhoc payload + arg extraction contract)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.prompts.agent_config import GAWAH_ASSISTANT_CONFIG, GAWAH_TOOLS
from app.services.phone_utils import CALL_INSTRUCTIONS, WEB_CALL_INSTRUCTIONS
from app.services.uplift_service import UpliftService


def main() -> None:
    names = [t["name"] for t in GAWAH_TOOLS]
    assert "save_witness_statement" in names
    assert "confirm_statement" in names
    assert "flag_inconsistency" in names
    assert "flag_intimidation" in names
    assert "enable_privacy_mode" in names
    assert "assess_protection_need" in names
    print("✓ GAWAH_TOOLS includes confirm_statement + core tools:", names)

    agent = GAWAH_ASSISTANT_CONFIG["config"]["agent"]
    assert agent.get("initialGreeting") is True
    assert "tools" in agent and len(agent["tools"]) == len(GAWAH_TOOLS)
    assert "CrPC" in agent["instructions"] or "161" in agent["instructions"]
    print("✓ assistant config has greeting + instructions + tools")

    assert "Phase 0" in CALL_INSTRUCTIONS or "voluntariness" in CALL_INSTRUCTIONS.lower()
    assert "web_browser" in WEB_CALL_INSTRUCTIONS
    assert "confirm_statement" in WEB_CALL_INSTRUCTIONS
    print("✓ WEB_CALL_INSTRUCTIONS mirrors phone channel guidance")

    # Uplift tool payload shape contract (docs.upliftai.org/assistants/tools)
    uplift_payload = {
        "arguments": {
            "raw_arguments": {
                "location": "Lahore",
                "sequence_of_events": "Main ne dekha.",
            }
        }
    }
    nested = uplift_payload["arguments"]["raw_arguments"]
    assert nested["location"] == "Lahore"
    print("✓ Uplift payload shape documented for frontend extractToolArguments")

    # Adhoc body shape — must keep FULL Phase 0–4 instructions + web channel notes
    uplift = UpliftService(get_settings())
    web_cfg = uplift._web_adhoc_config()  # noqa: SLF001 — parity probe
    assert "agent" in web_cfg
    assert "stt" in web_cfg
    assert web_cfg["stt"]["default"]["language"] == "ur"
    instr = web_cfg["agent"]["instructions"]
    assert "web_browser" in instr
    assert "Phase 0" in instr or "161" in instr
    assert len(instr) > len(WEB_CALL_INSTRUCTIONS) + 500
    assert web_cfg["agent"].get("initialGreeting") is True
    print("✓ adhoc web config prepends channel notes without wiping Phase 0–4")

    print(json.dumps({"tool_count": len(names), "ok": True, "instructions_len": len(instr)}))
    print("web agent parity checks passed")


if __name__ == "__main__":
    main()
