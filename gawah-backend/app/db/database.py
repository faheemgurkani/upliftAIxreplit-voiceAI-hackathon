from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import Settings, get_settings
from app.models.case import CaseCreate, CaseRecord
from app.models.statement import StatementRecord, StructuredStatement


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | str | None) -> str:
    if value is None:
        return _now().isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class Database:
    """Persistence layer with Supabase primary and local JSON fallback."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._lock = threading.Lock()
        self._supabase = None
        self._store_path = Path(settings.local_db_path)

        if settings.use_supabase:
            from supabase import create_client

            self._supabase = create_client(settings.supabase_url, settings.supabase_key)
        else:
            self._ensure_local_store()

    @property
    def backend(self) -> str:
        return "supabase" if self._supabase is not None else "local_json"

    def _ensure_local_store(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._store_path.exists():
            self._write_local({"cases": [], "statements": []})

    def _read_local(self) -> Dict[str, List[Dict[str, Any]]]:
        with self._store_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_local(self, payload: Dict[str, List[Dict[str, Any]]]) -> None:
        with self._store_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)

    # --- Cases ---

    def create_case(self, payload: CaseCreate, case_id: str) -> CaseRecord:
        record = CaseRecord(
            case_id=case_id,
            status=payload.status,
            station_id=payload.station_id,
            title=payload.title,
            description=payload.description,
        )
        data = record.model_dump(mode="json")

        if self._supabase is not None:
            result = self._supabase.table("cases").insert(data).execute()
            row = result.data[0] if result.data else data
            return CaseRecord.model_validate(row)

        with self._lock:
            store = self._read_local()
            store["cases"].append(data)
            self._write_local(store)
        return record

    def get_case(self, case_id: str) -> Optional[CaseRecord]:
        if self._supabase is not None:
            result = (
                self._supabase.table("cases")
                .select("*")
                .eq("case_id", case_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return CaseRecord.model_validate(result.data[0])

        with self._lock:
            store = self._read_local()
            for item in store["cases"]:
                if item.get("case_id") == case_id:
                    return CaseRecord.model_validate(item)
        return None

    def update_case_status(self, case_id: str, status: str) -> Optional[CaseRecord]:
        now = _iso(_now())
        if self._supabase is not None:
            result = (
                self._supabase.table("cases")
                .update({"status": status, "updated_at": now})
                .eq("case_id", case_id)
                .execute()
            )
            if not result.data:
                return None
            return CaseRecord.model_validate(result.data[0])

        with self._lock:
            store = self._read_local()
            for item in store["cases"]:
                if item.get("case_id") == case_id:
                    item["status"] = status
                    item["updated_at"] = now
                    self._write_local(store)
                    return CaseRecord.model_validate(item)
        return None

    # --- Statements ---

    def save_statement(self, record: StatementRecord) -> StatementRecord:
        data = record.model_dump(mode="json")
        data["updated_at"] = _iso(_now())

        if self._supabase is not None:
            # Ensure parent case exists for FK safety in demo mode.
            existing = self.get_case(record.case_id)
            if existing is None:
                self.create_case(CaseCreate(case_id=record.case_id, status="in_progress"), record.case_id)

            result = (
                self._supabase.table("statements")
                .upsert(data, on_conflict="id")
                .execute()
            )
            row = result.data[0] if result.data else data
            return StatementRecord.model_validate(row)

        with self._lock:
            store = self._read_local()
            # Auto-create case shell if missing
            if not any(c.get("case_id") == record.case_id for c in store["cases"]):
                store["cases"].append(
                    CaseRecord(case_id=record.case_id, status="in_progress").model_dump(mode="json")
                )

            replaced = False
            for idx, item in enumerate(store["statements"]):
                if item.get("id") == record.id or (
                    record.call_sid and item.get("call_sid") == record.call_sid
                ):
                    data["id"] = item["id"]
                    store["statements"][idx] = data
                    replaced = True
                    break
            if not replaced:
                store["statements"].append(data)
            self._write_local(store)
        return StatementRecord.model_validate(data)

    def get_statement_by_id(self, statement_id: str) -> Optional[StatementRecord]:
        if self._supabase is not None:
            result = (
                self._supabase.table("statements")
                .select("*")
                .eq("id", statement_id)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return StatementRecord.model_validate(result.data[0])

        with self._lock:
            store = self._read_local()
            for item in store["statements"]:
                if item.get("id") == statement_id:
                    return StatementRecord.model_validate(item)
        return None

    def get_statement_by_case(self, case_id: str) -> Optional[StatementRecord]:
        if self._supabase is not None:
            result = (
                self._supabase.table("statements")
                .select("*")
                .eq("case_id", case_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return StatementRecord.model_validate(result.data[0])

        with self._lock:
            store = self._read_local()
            matches = [s for s in store["statements"] if s.get("case_id") == case_id]
            if not matches:
                return None
            matches.sort(key=lambda s: s.get("created_at", ""), reverse=True)
            return StatementRecord.model_validate(matches[0])

    def get_statement_by_call(self, call_sid: str) -> Optional[StatementRecord]:
        if self._supabase is not None:
            result = (
                self._supabase.table("statements")
                .select("*")
                .eq("call_sid", call_sid)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if not result.data:
                return None
            return StatementRecord.model_validate(result.data[0])

        with self._lock:
            store = self._read_local()
            matches = [s for s in store["statements"] if s.get("call_sid") == call_sid]
            if not matches:
                return None
            matches.sort(key=lambda s: s.get("created_at", ""), reverse=True)
            return StatementRecord.model_validate(matches[0])

    def list_statements(self, page: int = 1, page_size: int = 20) -> tuple[List[StatementRecord], int]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        offset = (page - 1) * page_size

        if self._supabase is not None:
            count_result = (
                self._supabase.table("statements")
                .select("id", count="exact")
                .execute()
            )
            total = count_result.count or 0
            result = (
                self._supabase.table("statements")
                .select("*")
                .order("created_at", desc=True)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            items = [StatementRecord.model_validate(row) for row in (result.data or [])]
            return items, total

        with self._lock:
            store = self._read_local()
            rows = sorted(
                store["statements"],
                key=lambda s: s.get("created_at", ""),
                reverse=True,
            )
            total = len(rows)
            slice_rows = rows[offset : offset + page_size]
            return [StatementRecord.model_validate(r) for r in slice_rows], total

    def confirm_statement(
        self,
        statement_id: str,
        *,
        witness: bool = False,
        officer: bool = False,
    ) -> Optional[StatementRecord]:
        existing = self.get_statement_by_id(statement_id)
        if existing is None:
            return None

        if witness:
            existing.confirmed = True
        if officer:
            existing.officer_confirmed = True
        existing.updated_at = _now()
        return self.save_statement(existing)

    def append_transcript(self, call_sid: str, chunk: str, case_id: str, language: str) -> StatementRecord:
        existing = self.get_statement_by_call(call_sid)
        if existing is None:
            existing = StatementRecord(
                case_id=case_id,
                call_sid=call_sid,
                witness_language=language,  # type: ignore[arg-type]
                raw_transcript=chunk.strip(),
            )
        else:
            joined = f"{existing.raw_transcript} {chunk}".strip()
            existing.raw_transcript = joined
            existing.updated_at = _now()
        return self.save_statement(existing)


_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database(get_settings())
    return _db


def reset_db_for_tests() -> None:
    global _db
    _db = None
