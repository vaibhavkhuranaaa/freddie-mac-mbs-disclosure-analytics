#!/usr/bin/env python3
"""Serve the product and its authenticated loopback investigation boundary."""

from __future__ import annotations

import argparse
import hmac
import json
import os
import time
from collections.abc import Callable
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

try:
    from .cited_assistant import AssistantError, GeminiClient, answer_question
    from .investigation_store import InvestigationStore
except ImportError:  # Direct script execution.
    from cited_assistant import AssistantError, GeminiClient, answer_question
    from investigation_store import InvestigationStore


MAX_REQUEST_BYTES = 64 * 1024


class ProductHandler(SimpleHTTPRequestHandler):
    payload_path: Path
    investigation_store: InvestigationStore
    api_token: str
    trust_platform_identity: bool = False
    assistant: Callable[[str], dict[str, object]] | None = None

    def setup(self) -> None:
        self._request_started = time.perf_counter()
        self._authorized_state = False
        self._authenticated_actor = ""
        super().setup()

    def translate_path(self, path: str) -> str:
        if urlparse(path).path == "/data/dashboard.json":
            return str(self.payload_path)
        return super().translate_path(path)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/v1/health":
            self._authorized_state = True
            self._send_json(HTTPStatus.OK, {"status": "ok", "schema_version": 1})
            return
        if parsed.path.startswith("/v1/") and not self._authorized():
            return
        if parsed.path == "/v1/dashboard":
            self._send_json(HTTPStatus.OK, json.loads(self.payload_path.read_text(encoding="utf-8")))
            return
        if parsed.path == "/v1/investigations":
            status = parse_qs(parsed.query).get("status", [None])[0]
            try:
                self._send_json(HTTPStatus.OK, {"items": self.investigation_store.list(status)})
            except ValueError as error:
                self._send_error(HTTPStatus.BAD_REQUEST, str(error))
            return
        if parsed.path == "/v1/audit/requests":
            try:
                limit = int(parse_qs(parsed.query).get("limit", ["100"])[0])
                self._send_json(HTTPStatus.OK, {"items": self.investigation_store.list_api_audit(limit)})
            except ValueError as error:
                self._send_error(HTTPStatus.BAD_REQUEST, str(error))
            return
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 4 and parts[:2] == ["v1", "investigations"] and parts[3] == "audit":
            self._send_json(HTTPStatus.OK, {"items": self.investigation_store.audit(parts[2])})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path not in {"/v1/investigations", "/v1/assistant"}:
            self._send_error(HTTPStatus.NOT_FOUND, "route not found")
            return
        if not self._authorized():
            return
        if path == "/v1/assistant":
            if self.assistant is None:
                self._send_error(HTTPStatus.SERVICE_UNAVAILABLE, "assistant is not enabled")
                return
            try:
                request = self._read_json()
                if set(request) != {"question"}:
                    raise ValueError("request must contain only question")
                response = self.assistant(request["question"])
                self._send_json(HTTPStatus.OK, response)
            except (AssistantError, TypeError, ValueError) as error:
                self._send_error(HTTPStatus.BAD_REQUEST, str(error))
            return
        try:
            record = self.investigation_store.create(self._read_json(), self._actor())
            self._send_json(HTTPStatus.CREATED, record)
        except ValueError as error:
            self._send_error(HTTPStatus.BAD_REQUEST, str(error))

    def do_PATCH(self) -> None:  # noqa: N802
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[:2] != ["v1", "investigations"]:
            self._send_error(HTTPStatus.NOT_FOUND, "route not found")
            return
        if not self._authorized():
            return
        try:
            record = self.investigation_store.update(parts[2], self._read_json(), self._actor())
            self._send_json(HTTPStatus.OK, record)
        except KeyError:
            self._send_error(HTTPStatus.NOT_FOUND, "investigation not found")
        except ValueError as error:
            self._send_error(HTTPStatus.BAD_REQUEST, str(error))

    def _authorized(self) -> bool:
        platform_actor = self.headers.get("X-MS-CLIENT-PRINCIPAL-ID", "").strip()
        if self.trust_platform_identity and platform_actor:
            self._authorized_state = True
            self._authenticated_actor = platform_actor
            return True
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {self.api_token}"
        if hmac.compare_digest(supplied, expected):
            self._authorized_state = True
            return True
        self._send_error(HTTPStatus.UNAUTHORIZED, "valid bearer token required")
        return False

    def _actor(self) -> str:
        if self.trust_platform_identity:
            if not self._authenticated_actor:
                raise ValueError("authenticated platform principal is required")
            return self._authenticated_actor
        actor = self.headers.get("X-Actor", "").strip()
        if not actor:
            raise ValueError("X-Actor header is required")
        return actor

    def _read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("invalid Content-Length") from error
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise ValueError(f"request body must be between 1 and {MAX_REQUEST_BYTES} bytes")
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise ValueError("request body must be valid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def _send_error(self, status: HTTPStatus, detail: str) -> None:
        self._send_json(status, {"error": status.phrase, "detail": detail})

    def _send_json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, separators=(",", ":")).encode()
        if urlparse(self.path).path.startswith("/v1/"):
            duration_ms = (time.perf_counter() - self._request_started) * 1000
            self.investigation_store.record_api_request(
                self.command,
                urlparse(self.path).path,
                int(status),
                self._authenticated_actor or self.headers.get("X-Actor", "").strip(),
                self._authorized_state,
                duration_ms,
            )
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)


def make_handler(
    static_root: Path,
    payload: Path,
    database: Path,
    token: str,
    assistant: Callable[[str], dict[str, object]] | None = None,
    trust_platform_identity: bool = False,
) -> type[ProductHandler]:
    store = InvestigationStore(database)
    store.initialize()
    bound_assistant = assistant
    platform_identity = trust_platform_identity

    class BoundProductHandler(ProductHandler):
        payload_path = payload.resolve()
        investigation_store = store
        api_token = token
        platform_identity_enabled = platform_identity
        cited_assistant = bound_assistant

        def __init__(self, *args: object, **kwargs: object):
            super().__init__(*args, directory=str(static_root), **kwargs)

        @property
        def assistant(self) -> Callable[[str], dict[str, object]] | None:
            return self.cited_assistant

        @property
        def trust_platform_identity(self) -> bool:
            return self.platform_identity_enabled

    return BoundProductHandler


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_root = Path(os.environ.get("MBS_DATA_ROOT", root.parent / f"{root.name}-data"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, default=data_root / "product/dashboard.json")
    parser.add_argument("--database", type=Path, default=data_root / "product/investigations.sqlite")
    parser.add_argument("--host", default=os.environ.get("MBS_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    if not args.payload.is_file():
        raise FileNotFoundError(f"build the governed payload first: {args.payload}")
    token = os.environ.get("MBS_API_TOKEN", "")
    trust_platform_identity = os.environ.get("MBS_TRUST_PLATFORM_IDENTITY") == "1"
    if not trust_platform_identity and len(token) < 16:
        raise RuntimeError("MBS_API_TOKEN must contain at least 16 characters")
    assistant = None
    if os.environ.get("MBS_AI_ENABLED") == "1":
        max_requests = int(os.environ.get("MBS_AI_MAX_REQUESTS", "0"))
        max_cost_usd = float(os.environ.get("MBS_AI_MAX_COST_USD", "0"))
        client = GeminiClient(
            os.environ.get("GEMINI_API_KEY", ""),
            model=os.environ.get("MBS_AI_MODEL", "gemini-3.5-flash-lite"),
            max_requests=max_requests,
            max_cost_usd=max_cost_usd,
        )
        product_payload = json.loads(args.payload.read_text(encoding="utf-8"))
        assistant = lambda question: answer_question(question, product_payload, client)
    handler = make_handler(
        root / "app",
        args.payload,
        args.database,
        token,
        assistant,
        trust_platform_identity,
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Product preview: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
