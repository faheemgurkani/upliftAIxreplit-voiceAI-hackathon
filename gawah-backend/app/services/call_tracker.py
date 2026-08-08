"""Merge local call records with live Uplift session status + artifacts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.services.uplift_service import UpliftService


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
        if s == "failed" or o in {
            "no_answer",
            "busy",
            "declined",
            "network_error",
            "call_failed",
            "unreachable",
            "voicemail",
            "silent_pickup",
            "wrong_number",
        }:
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
        if outcome == "unreachable":
            return "Failed — unreachable"
        return f"Failed{f' — {outcome}' if outcome else ''}"
    return status


def merge_uplift_session(
    local: Dict[str, Any],
    remote: Dict[str, Any],
    *,
    artifacts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    state = remote.get("state") or remote.get("status")
    outcome = remote.get("outcome") or remote.get("failureReason")
    failure = remote.get("failureReason")
    status = normalize_call_status(
        state=state,
        outcome=outcome,
        failure_reason=failure,
        connected=remote.get("connected"),
    )
    arts = artifacts or UpliftService.extract_session_artifacts(remote)

    # Prefer newly discovered artifacts; keep previously saved local copies.
    recording_url = arts.get("recording_url") or local.get("recording_url")
    transcript = arts.get("transcript") if arts.get("transcript") is not None else local.get("transcript")
    analysis = arts.get("analysis") if arts.get("analysis") is not None else local.get("analysis")
    local_recording = arts.get("local_recording_path") or local.get("local_recording_path")
    artifacts_status = arts.get("artifacts_status") or local.get("artifacts_status") or "pending_or_unavailable"

    return {
        **local,
        "state": state,
        "status": status,
        "outcome": outcome,
        "failure_reason": failure,
        "failure_reason_raw": remote.get("failureReasonRaw") or local.get("failure_reason_raw"),
        "connected": remote.get("connected"),
        "to": remote.get("toNumber") or local.get("to"),
        "from_number": remote.get("fromNumber") or local.get("from_number"),
        "channel": remote.get("channel") or local.get("channel"),
        "direction": remote.get("direction") or local.get("direction") or "outbound",
        "duration_sec": remote.get("durationSec")
        if remote.get("durationSec") is not None
        else local.get("duration_sec"),
        "answered_at": remote.get("answeredAt") or local.get("answered_at"),
        "ringing_at": remote.get("ringingAt") or local.get("ringing_at"),
        "connected_at": remote.get("connectedAt") or local.get("connected_at"),
        "ended_at": remote.get("endedAt") or local.get("ended_at"),
        "ended_by": remote.get("endedBy") or local.get("ended_by"),
        "transport_provider": remote.get("transportProvider") or local.get("transport_provider"),
        "participant_identity": remote.get("participantIdentity")
        or local.get("participant_identity"),
        "recording_url": recording_url,
        "transcript": transcript,
        "analysis": analysis,
        "local_recording_path": local_recording,
        "artifacts_status": artifacts_status,
        "artifacts_available": bool(recording_url or transcript or analysis or local_recording),
        "label": human_label(status, outcome if isinstance(outcome, str) else None),
        "raw_remote": {
            "sessionId": remote.get("sessionId") or remote.get("id"),
            "state": state,
            "outcome": outcome,
            "failureReason": failure,
            "connected": remote.get("connected"),
            "durationSec": remote.get("durationSec"),
            "endedBy": remote.get("endedBy"),
        },
    }


def persistable_fields(merged: Dict[str, Any]) -> Dict[str, Any]:
    """Subset safe to upsert into the local call store."""
    keys = (
        "call_id",
        "status",
        "state",
        "outcome",
        "failure_reason",
        "failure_reason_raw",
        "connected",
        "to",
        "from_number",
        "label",
        "channel",
        "direction",
        "duration_sec",
        "answered_at",
        "ringing_at",
        "connected_at",
        "ended_at",
        "ended_by",
        "transport_provider",
        "participant_identity",
        "recording_url",
        "transcript",
        "analysis",
        "local_recording_path",
        "artifacts_status",
        "artifacts_available",
        "mocked",
        "created_at",
    )
    out = {k: merged[k] for k in keys if k in merged and merged[k] is not None}
    out.setdefault("mocked", False)
    return out


def index_remote_sessions(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for item in items:
        sid = str(item.get("sessionId") or item.get("callId") or item.get("id") or "")
        if sid:
            out[sid] = item
    return out
