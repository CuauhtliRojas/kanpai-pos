"""Minimal Airtable Records API client used by the seed pipeline.

The client can list, create and update records. It intentionally exposes no
delete operation.
"""

from __future__ import annotations

import json
import os
import time
import threading
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

API_ROOT = "https://api.airtable.com/v0"
RETRY_STATUS = {429, 500, 502, 503}
MAX_BATCH_SIZE = 10
MIN_REQUEST_INTERVAL_SECONDS = 0.2
_RATE_LIMIT_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0


class AirtableRecordsError(RuntimeError):
    """Raised when the Records API cannot complete a safe operation."""


def batched(items: list[Any], size: int = MAX_BATCH_SIZE) -> Iterable[list[Any]]:
    if size < 1 or size > MAX_BATCH_SIZE:
        raise ValueError(f"El batch debe estar entre 1 y {MAX_BATCH_SIZE}.")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == []


def _as_number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def _same_value(left: Any, right: Any, *, linked: bool = False) -> bool:
    """Compare Airtable values after normalizing API representation details."""
    if linked:
        left_ids = [] if _is_empty(left) else left
        right_ids = [] if _is_empty(right) else right
        if not isinstance(left_ids, list) or not isinstance(right_ids, list):
            return False
        return sorted(str(value).strip() for value in left_ids) == sorted(
            str(value).strip() for value in right_ids
        )

    if isinstance(right, bool):
        if _is_empty(left):
            return right is False
        if isinstance(left, bool):
            return left is right
        return False

    if _is_empty(left) and _is_empty(right):
        return True

    left_number = _as_number(left)
    right_number = _as_number(right)
    if left_number is not None and right_number is not None:
        return left_number == right_number

    if isinstance(left, str) and isinstance(right, str):
        return left.strip() == right.strip()

    return left == right


KeyField = str | tuple[str, ...]
NaturalKey = str | tuple[Any, ...]


def _key_part(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return tuple(sorted((_key_part(item) for item in value), key=str))
    return value


def record_natural_key(
    fields: dict[str, Any], key_field: KeyField
) -> NaturalKey | None:
    key_fields = (key_field,) if isinstance(key_field, str) else key_field
    parts = tuple(_key_part(fields.get(field)) for field in key_fields)
    if any(part in (None, "", ()) for part in parts):
        return None
    return parts[0] if isinstance(key_field, str) else parts


class AirtableRecordsClient:
    def __init__(self, base_id: str, token: str, *, max_attempts: int = 5) -> None:
        if not base_id or not token:
            raise ValueError("base_id y token son obligatorios.")
        self.base_id = base_id
        self._token = token
        self.max_attempts = max_attempts

    @classmethod
    def from_env(cls) -> AirtableRecordsClient:
        load_dotenv()
        token = os.getenv("AIRTABLE_API_TOKEN", "").strip()
        base_id = os.getenv("AIRTABLE_BASE_ID", "").strip()
        if not token:
            raise AirtableRecordsError("Falta AIRTABLE_API_TOKEN.")
        if not base_id:
            raise AirtableRecordsError("Falta AIRTABLE_BASE_ID.")
        return cls(base_id, token)

    def _url(self, table: str, query: list[tuple[str, str]] | None = None) -> str:
        url = f"{API_ROOT}/{quote(self.base_id, safe='')}/{quote(table, safe='')}"
        return f"{url}?{urlencode(query)}" if query else url

    def _request(
        self,
        method: str,
        table: str,
        *,
        query: list[tuple[str, str]] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        url = self._url(table, query)

        global _LAST_REQUEST_AT

        for attempt in range(1, self.max_attempts + 1):
            with _RATE_LIMIT_LOCK:
                wait = MIN_REQUEST_INTERVAL_SECONDS - (time.monotonic() - _LAST_REQUEST_AT)
                if wait > 0:
                    time.sleep(wait)
                _LAST_REQUEST_AT = time.monotonic()
            request = Request(url, data=data, headers=headers, method=method)
            try:
                with urlopen(request, timeout=30) as response:  # noqa: S310
                    body = response.read().decode("utf-8")
                    return json.loads(body) if body else {}
            except HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                if error.code in RETRY_STATUS and attempt < self.max_attempts:
                    retry_after = error.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else min(2**attempt, 10)
                    time.sleep(max(0.25, min(delay, 30)))
                    continue
                raise AirtableRecordsError(
                    f"Airtable HTTP {error.code}: {method} {table}: {detail}"
                ) from error
            except URLError as error:
                if attempt < self.max_attempts:
                    time.sleep(min(2**attempt, 10))
                    continue
                raise AirtableRecordsError(
                    f"Airtable network error: {method} {table}: {error}"
                ) from error

        raise AirtableRecordsError(f"No se pudo completar {method} {table}.")

    def list_records(
        self,
        table: str,
        *,
        fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        offset = ""
        while True:
            query: list[tuple[str, str]] = [("pageSize", "100")]
            query.extend(("fields[]", field) for field in fields or [])
            if offset:
                query.append(("offset", offset))
            response = self._request("GET", table, query=query)
            records.extend(response.get("records", []))
            offset = response.get("offset", "")
            if not offset:
                return records

    def create_records(
        self, table: str, fields_by_record: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        for group in batched(fields_by_record):
            response = self._request(
                "POST",
                table,
                payload={"records": [{"fields": fields} for fields in group]},
            )
            created.extend(response.get("records", []))
        return created

    def update_records(
        self, table: str, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        updated: list[dict[str, Any]] = []
        for group in batched(records):
            response = self._request("PATCH", table, payload={"records": group})
            updated.extend(response.get("records", []))
        return updated

    def index_by_key(
        self, table: str, key_field: KeyField, *, fields: list[str] | None = None
    ) -> dict[NaturalKey, dict[str, Any]]:
        key_fields = (key_field,) if isinstance(key_field, str) else key_field
        requested = list(dict.fromkeys([*key_fields, *(fields or [])]))
        result: dict[NaturalKey, dict[str, Any]] = {}
        for record in self.list_records(table, fields=requested):
            key = record_natural_key(record.get("fields", {}), key_field)
            if key is None:
                continue
            if key in result:
                raise AirtableRecordsError(
                    f"Clave natural duplicada en Airtable: {table}.{key_field}={key!r}"
                )
            result[key] = record
        return result

    def plan_upsert(
        self,
        table: str,
        key_field: KeyField,
        records: list[dict[str, Any]],
        *,
        linked_fields: set[str] | None = None,
        excluded_fields: set[str] | None = None,
        existing: dict[NaturalKey, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        linked_fields = linked_fields or set()
        excluded_fields = excluded_fields or set()
        key_fields = (key_field,) if isinstance(key_field, str) else key_field
        if set(key_fields) & excluded_fields:
            raise ValueError("La clave natural no puede excluirse del upsert.")
        writable_records = [
            {field: value for field, value in record.items() if field not in excluded_fields}
            for record in records
        ]
        field_names = sorted({field for record in writable_records for field in record})
        if existing is None:
            existing = self.index_by_key(table, key_field, fields=field_names)
        creates: list[dict[str, Any]] = []
        updates: list[dict[str, Any]] = []
        unchanged: list[dict[str, Any]] = []

        for fields in writable_records:
            key = record_natural_key(fields, key_field)
            if key is None:
                raise AirtableRecordsError(
                    f"Registro sin clave natural: {table}.{key_field}"
                )
            remote = existing.get(key)
            if remote is None:
                creates.append(fields)
                continue
            remote_fields = remote.get("fields", {})
            changed = {
                field: value
                for field, value in fields.items()
                if not _same_value(
                    remote_fields.get(field), value, linked=field in linked_fields
                )
            }
            if changed:
                updates.append({"id": remote["id"], "fields": changed})
            else:
                unchanged.append(remote)

        return {
            "creates": creates,
            "updates": updates,
            "unchanged": unchanged,
            "existing": existing,
        }

    def upsert_by_key(
        self,
        table: str,
        key_field: KeyField,
        records: list[dict[str, Any]],
        *,
        linked_fields: set[str] | None = None,
        excluded_fields: set[str] | None = None,
    ) -> dict[str, Any]:
        plan = self.plan_upsert(
            table,
            key_field,
            records,
            linked_fields=linked_fields,
            excluded_fields=excluded_fields,
        )
        created = self.create_records(table, plan["creates"])
        updated = self.update_records(table, plan["updates"])
        final_index = dict(plan["existing"])
        for record in [*created, *updated]:
            key = record_natural_key(record.get("fields", {}), key_field)
            if key is not None:
                final_index[key] = record
        return {
            "created": len(created),
            "updated": len(updated),
            "unchanged": len(plan["unchanged"]),
            "index": final_index,
        }
