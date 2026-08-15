"""Exact-byte capture for narrow MLB Stats API source snapshots.

`python-mlb-statsapi` remains the transport/error-handling utility. Its public
`MlbResult` intentionally exposes parsed JSON rather than raw response bytes, so
this module uses the package's documented Session-injection API plus a Requests
response hook to retain the exact successful response body before parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from mlbstatsapi import MlbDataAdapter, create_retry_policy
import requests
from requests.adapters import HTTPAdapter


DEFAULT_USER_AGENT = "universal-baseball-model/0.0.1"


@dataclass(frozen=True, slots=True)
class CapturedOfficialJson:
    endpoint: str
    url: str
    status_code: int
    retrieved_at_utc: datetime
    raw_bytes: bytes
    content_sha256: str
    data: Any

    def write_raw(self, path: Path) -> None:
        """Persist the exact response bytes without re-serializing JSON."""

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.raw_bytes)


def _new_retrying_session() -> requests.Session:
    """Create a caller-owned Session using the package's public retry policy."""

    session = requests.Session()
    retry_adapter = HTTPAdapter(max_retries=create_retry_policy())
    session.mount("https://", retry_adapter)
    session.mount("http://", retry_adapter)
    session.headers["User-Agent"] = DEFAULT_USER_AGENT
    return session


def capture_official_json(
    endpoint: str,
    *,
    session: requests.Session | None = None,
) -> CapturedOfficialJson:
    """Fetch one Stats API endpoint while retaining exact successful bytes.

    When ``session`` is omitted, this function owns a caller-managed Requests
    Session configured with `python-mlb-statsapi`'s public retry policy. When a
    Session is injected, its adapters/headers/ownership remain the caller's; only
    a temporary response hook is appended and removed.

    The returned ``data`` is parsed directly from the captured raw bytes, not
    from ``MlbResult.data``. This matters because the package deliberately drops
    the top-level MLB copyright field from its convenience result.
    """

    target = endpoint.strip().lstrip("/")
    if not target:
        raise ValueError("official endpoint cannot be blank")

    owned_session = session is None
    active_session = session or _new_retrying_session()
    captured: dict[str, Any] = {}

    def record_response(response: requests.Response, *args: Any, **kwargs: Any) -> requests.Response:
        captured["raw_bytes"] = bytes(response.content)
        captured["url"] = str(response.url)
        captured["status_code"] = int(response.status_code)
        return response

    response_hooks = active_session.hooks.setdefault("response", [])
    response_hooks.append(record_response)
    adapter = MlbDataAdapter(ver="v1", session=active_session)
    retrieved_at = datetime.now(UTC)
    try:
        adapter.get(target)
    finally:
        # MlbDataAdapter does not close injected Sessions. Remove only our hook
        # so caller-owned Session behavior is restored exactly.
        if record_response in response_hooks:
            response_hooks.remove(record_response)
        adapter.close()
        if owned_session:
            active_session.close()

    if not captured:
        raise RuntimeError(f"official transport returned no capturable response for {target}")
    status_code = int(captured["status_code"])
    if not 200 <= status_code <= 299:
        # The adapter already raises structured errors for most non-2xx statuses;
        # make its special 404-empty-result path unsuitable for source promotion.
        raise RuntimeError(
            f"official source snapshot requires successful 2xx response; got {status_code}"
        )

    raw_bytes = bytes(captured["raw_bytes"])
    try:
        data = json.loads(raw_bytes) if raw_bytes else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("captured official response is not valid JSON") from exc

    return CapturedOfficialJson(
        endpoint=target,
        url=str(captured["url"]),
        status_code=status_code,
        retrieved_at_utc=retrieved_at,
        raw_bytes=raw_bytes,
        content_sha256=sha256(raw_bytes).hexdigest(),
        data=data,
    )
