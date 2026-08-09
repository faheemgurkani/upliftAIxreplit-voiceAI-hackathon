#!/usr/bin/env python3
"""Verify web agent config parity pieces (tools + adhoc payload + arg extraction contract)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.prompts.agent_config import GAWAH_ASSISTANT_CONFIG, GAWAH_TOOLS
from app.services.phone_utils import CALL_INSTRUCTIONS, WEB_CALL_INSTRUCTIONS


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

    # Adhoc body shape
    adhoc_body = {
        "participantName": "Witness",
        "config": GAWAH_ASSISTANT_CONFIG["config"],
    }
    assert "agent" in adhoc_body["config"]
    assert "stt" in adhoc_body["config"]
    assert adhoc_body["config"]["stt"]["default"]["language"] == "ur"
    print("✓ adhoc session body uses full Gawah config (ur STT)")

    print(json.dumps({"tool_count": len(names), "ok": True}))
    print("web agent parity checks passed")


if __name__ == "__main__":
    main()
