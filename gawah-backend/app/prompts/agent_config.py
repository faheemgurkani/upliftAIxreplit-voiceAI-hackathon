from __future__ import annotations

from pathlib import Path

_INSTRUCTIONS_PATH = Path(__file__).with_name("agent_instructions.txt")
AGENT_INSTRUCTIONS = _INSTRUCTIONS_PATH.read_text(encoding="utf-8")

GAWAH_TOOLS = [
    {
        "name": "save_witness_statement",
        "description": (
            "Save the structured witness statement once all five fields have been collected. "
            "Call this when you have enough information — do not wait for perfect answers."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "time_of_incident": {
                    "type": "string",
                    "description": "When the incident occurred. Accept approximate references.",
                },
                "location": {
                    "type": "string",
                    "description": "Where the incident occurred.",
                },
                "persons_present": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Names or descriptions of all persons present.",
                },
                "sequence_of_events": {
                    "type": "string",
                    "description": "What happened, first-person narrative from the witness.",
                },
                "relationship_to_accused": {
                    "type": "string",
                    "description": "How the witness knows the accused, if any.",
                },
                "temporal_uncertainty": {
                    "type": "boolean",
                    "description": "True if approximate time references were used.",
                },
                "language_of_call": {
                    "type": "string",
                    "enum": ["ur", "pa", "ps", "mixed"],
                },
                "witness_type": {
                    "type": "string",
                    "enum": ["eyewitness", "hearsay", "victim", "unknown"],
                },
                "corroboration_sources_mentioned": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["sequence_of_events", "location"],
        },
        "timeout": 15,
    },
    {
        "name": "flag_inconsistency",
        "description": "Silently flag an internal contradiction. Do not alert the witness.",
        "parameters": {
            "type": "object",
            "properties": {
                "contradiction_description": {"type": "string"},
                "segment_a": {"type": "string"},
                "segment_b": {"type": "string"},
                "contradiction_type": {
                    "type": "string",
                    "enum": [
                        "temporal",
                        "spatial",
                        "identity",
                        "sequence",
                        "sensory",
                        "numerical",
                    ],
                },
            },
            "required": ["contradiction_description"],
        },
        "timeout": 5,
    },
    {
        "name": "flag_intimidation",
        "description": "Silently flag intimidation/threat/coercion signals. Escalates case.",
        "parameters": {
            "type": "object",
            "properties": {
                "witness_statement": {
                    "type": "string",
                    "description": "Exact words that triggered the flag",
                }
            },
            "required": ["witness_statement"],
        },
        "timeout": 5,
    },
    {
        "name": "enable_privacy_mode",
        "description": "Switch case to anonymous mode — no personal identity stored.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
            },
            "required": [],
        },
        "timeout": 5,
    },
    {
        "name": "assess_protection_need",
        "description": (
            "Assess witness protection eligibility when serious offence or intimidation "
            "is indicated. May speak to witness via presentationInstructions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "offence_type": {
                    "type": "string",
                    "enum": [
                        "terrorism",
                        "sexual_offence",
                        "murder",
                        "kidnapping",
                        "serious_assault",
                        "other",
                    ],
                },
                "witness_is_victim": {"type": "boolean"},
                "witness_appears_under_16": {"type": "boolean"},
                "intimidation_already_flagged": {"type": "boolean"},
                "province": {
                    "type": "string",
                    "enum": [
                        "Punjab",
                        "Sindh",
                        "Balochistan",
                        "KPK",
                        "Federal",
                        "unknown",
                    ],
                },
            },
            "required": ["offence_type"],
        },
        "timeout": 10,
    },
    {
        "name": "confirm_statement",
        "description": (
            "Record the witness's spoken confirmation after readback. "
            "Call when the witness says haan / yes that the statement is correct."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "confirmed": {
                    "type": "boolean",
                    "description": "True when witness confirms the readback.",
                },
                "ref_code": {
                    "type": "string",
                    "description": "Reference code just issued, if known.",
                },
            },
            "required": [],
        },
        "timeout": 8,
    },
]

GAWAH_ASSISTANT_CONFIG = {
    "name": "Gawah Witness Agent",
    "description": (
        "Records witness statements in Urdu and Punjabi for Pakistan's legal system"
    ),
    "config": {
        "agent": {
            "instructions": AGENT_INSTRUCTIONS,
            "initialGreeting": True,
            "greetingInstructions": (
                "Assalam-u-Alaikum. Main Gawah hoon — ek digital gawahi darz karne ka nizam. "
                "Aap jo kuch bhi bolen ga, woh mehfooz ho jaye ga. Koi bhi aap ki awaaz sun nahi "
                "raha — sirf system record kar raha hai. Kya aap apna bayan dena chahte hain?"
            ),
            "tools": GAWAH_TOOLS,
        },
        "stt": {
            "default": {
                "provider": "groq",
                "model": "whisper-large-v3",
                "language": "ur",
            }
        },
        "tts": {
            "default": {
                "provider": "upliftai",
                "voiceId": "ai_lwr_f_fb",
                "outputFormat": "MP3_22050_32",
            }
        },
        "llm": {
            "default": {
                "provider": "groq",
                "model": "openai/gpt-oss-120b",
            }
        },
        "session": {"ttl": 1800},
    },
}
