"""Merge local call records with live Uplift session status."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


ACTIVE_STATES = {
    "dispatched",
    "dialing",
    "ringing",
    "answered",
    "in_progress",
    "connected",
    "processing",
}

TERMINAL_STATES = {"completed", "failed", "ended", "cancelled"}


def normalize_call_status(
    *,
    state: Optional[str] = None,
    outcome: Optional[str] = None,
    failure_reason: Optional[str] = None,
    connected: Optional[bool] = None,
) -> str:
    s = (state or "").strip().lower()
    o = (outcome or failure_reason or "").strip().lower()

    if s in TERMINAL_STATES:
        if s == "failed" or o in {"no_answer", "busy", "declined", "network_error", "call_failed"}:
            return "failed"
        if s == "completed":
            return "completed"
        return s

    if o == "no_answer" and s in {"ringing", "dispatched", "dialing"}:
        # Uplift sometimes attaches outcome early while still ringing
        return s or "ringing"

    if connected and s not in TERMINAL_STATES:
        return "answered" if s in {"", "dispatched", "dialing", "ringing"} else s

    return s or "unknown"


def human_label(status: str, outcome: Optional[str] = None) -> str:
    status = (status or "unknown").lower()
    outcome = (outcome or "").lower()
    if status in ACTIVE_STATES:
        return {
            "dispatched": "Queued / dialing started",
            "dialing": "Dialing",
            "ringing": "Ringing — answer the phone",
            "answered": "In progress — interview live",
            "in_progress": "In progress — interview live",
            "connected": "In progress — interview live",
            "processing": "Processing",
        }.get(status, status)
    if status == "completed":
        return "Completed"
    if status == "failed":
        if outcome == "no_answer":
            return "Failed — no answer"
        if outcome == "busy":
            return "Failed — busy"
        if outcome == "declined":
            return "Failed — declined"
        return f"Failed{f' — {outcome}' if outcome else ''}"
    return status


def merge_uplift_session(local: Dict[str, Any], remote: Dict[str, Any]) -> Dict[str, Any]:
    state = remote.get("state") or remote.get("status")
    outcome = remote.get("outcome") or remote.get("failureReason")
    failure = remote.get("failureReason")
    status = normalize_call_status(
        state=state,
        outcome=outcome,
        failure_reason=failure,
        connected=remote.get("connected"),
    )
    return {
        **local,
        "state": state,
        "status": status,
        "outcome": outcome,
        "failure_reason": failure,
        "connected": remote.get("connected"),
        "to": remote.get("toNumber") or local.get("to"),
        "from_number": remote.get("fromNumber") or local.get("from_number"),
        "channel": remote.get("channel") or local.get("channel"),
        "direction": remote.get("direction") or local.get("direction") or "outbound",
        "label": human_label(status, outcome if isinstance(outcome, str) else None),
        "raw_remote": {
            "sessionId": remote.get("sessionId") or remote.get("id"),
            "state": state,
            "outcome": outcome,
            "failureReason": failure,
            "connected": remote.get("connected"),
        },
    }


def index_remote_sessions(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in items:
        sid = str(item.get("sessionId") or item.get("callId") or item.get("id") or "")
        if sid:
            out[sid] = item
    return out
