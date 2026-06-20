"""Minimal Airtable Records API client used by the seed pipeline.

The client can list, create and update records. It intentionally exposes no
delete operation.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

API_ROOT = "https://api.airtable.com/v0"
RETRY_STATUS = {429, 500, 502, 503}
MAX_BATCH_SIZE = 10


class AirtableRecordsError(RuntimeError):
    """Raised when the Records API cannot complete a safe operation."""


def batched(items: list[Any], size: int = MAX_BATCH_SIZE) -> Iterable[list[Any]]:
    if size < 1 or size > MAX_BATCH_SIZE:
        raise ValueError(f"El batch debe estar entre 1 y {MAX_BATCH_SIZE}.")
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _same_value(left: Any, right: Any) -> bool:
    if isinstance(left, list) and isinstance(right, list):
        return sorted(left) == sorted(right)
    return left == right


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

        for attempt in range(1, self.max_attempts + 1):
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
        self, table: str, key_field: str, *, fields: list[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        requested = list(dict.fromkeys([key_field, *(fields or [])]))
        result: dict[str, dict[str, Any]] = {}
        for record in self.list_records(table, fields=requested):
            key = str(record.get("fields", {}).get(key_field, "")).strip()
            if not key:
                continue
            if key in result:
                raise AirtableRecordsError(
                    f"Clave natural duplicada en Airtable: {table}.{key_field}={key!r}"
                )
            result[key] = record
        return result

    def plan_upsert(
        self, table: str, key_field: str, records: list[dict[str, Any]]
    ) -> dict[str, Any]:
        field_names = sorted({field for record in records for field in record})
        existing = self.index_by_key(table, key_field, fields=field_names)
        creates: list[dict[str, Any]] = []
        updates: list[dict[str, Any]] = []
        unchanged: list[dict[str, Any]] = []

        for fields in records:
            key = str(fields.get(key_field, "")).strip()
            if not key:
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
                if not _same_value(remote_fields.get(field), value)
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
        self, table: str, key_field: str, records: list[dict[str, Any]]
    ) -> dict[str, Any]:
        plan = self.plan_upsert(table, key_field, records)
        created = self.create_records(table, plan["creates"])
        updated = self.update_records(table, plan["updates"])
        final_index = dict(plan["existing"])
        for record in [*created, *updated]:
            key = str(record.get("fields", {}).get(key_field, "")).strip()
            if key:
                final_index[key] = record
        return {
            "created": len(created),
            "updated": len(updated),
            "unchanged": len(plan["unchanged"]),
            "index": final_index,
        }
