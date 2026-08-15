from __future__ import annotations

from hashlib import sha256

import requests
from requests.adapters import BaseAdapter
from requests.models import PreparedRequest, Response

from universal_baseball.official_capture import capture_official_json


class StaticAdapter(BaseAdapter):
    def __init__(self, body: bytes, status_code: int = 200) -> None:
        super().__init__()
        self.body = body
        self.status_code = status_code
        self.closed = False

    def send(self, request: PreparedRequest, **kwargs: object) -> Response:
        response = Response()
        response.status_code = self.status_code
        response._content = self.body
        response.url = request.url
        response.request = request
        response.reason = "OK" if self.status_code == 200 else "Not Found"
        response.headers["Content-Type"] = "application/json"
        return response

    def close(self) -> None:
        self.closed = True


def test_capture_preserves_exact_bytes_and_top_level_copyright() -> None:
    body = b'{"copyright":"keep exact source bytes","allPlays":[],"x":1}'
    static = StaticAdapter(body)
    session = requests.Session()
    session.mount("https://", static)
    existing_hook_calls: list[int] = []

    def existing_hook(response: Response, *args: object, **kwargs: object) -> Response:
        existing_hook_calls.append(response.status_code)
        return response

    session.hooks["response"].append(existing_hook)
    try:
        captured = capture_official_json(
            "game/123/playByPlay",
            session=session,
        )

        assert captured.raw_bytes == body
        assert captured.content_sha256 == sha256(body).hexdigest()
        assert captured.data["copyright"] == "keep exact source bytes"
        assert captured.data["allPlays"] == []
        assert captured.status_code == 200
        assert existing_hook_calls == [200]
        # Our temporary response hook is removed; the caller's remains.
        assert session.hooks["response"] == [existing_hook]
        # Caller-owned Session/adapters are not closed by capture_official_json.
        assert static.closed is False
    finally:
        session.close()


def test_capture_rejects_adapter_404_empty_result_as_source_snapshot() -> None:
    body = b'{"message":"not found"}'
    static = StaticAdapter(body, status_code=404)
    session = requests.Session()
    session.mount("https://", static)
    try:
        try:
            capture_official_json("game/999/playByPlay", session=session)
        except RuntimeError as exc:
            assert "requires successful 2xx" in str(exc)
        else:
            raise AssertionError("expected non-2xx source capture to fail")
    finally:
        session.close()
