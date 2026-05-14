"""Native image loader tool.

`read_image` loads a local image file or safe HTTP(S) image URL and returns an
OpenAI-style multimodal content envelope. It performs no LLM/API calls; the
active main model sees the pixels when run_agent unwraps the `_multimodal`
result into a tool message.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from agent.image_routing import _sniff_mime_from_bytes
from tools.registry import registry
from tools.url_safety import is_safe_url
from tools.website_policy import check_website_access


READ_IMAGE_MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
READ_IMAGE_DOWNLOAD_TIMEOUT = 30.0


READ_IMAGE_SCHEMA = {
    "name": "read_image",
    "description": (
        "Load a local image file or safe HTTP(S) image URL and attach its "
        "pixels to the next model call for the active vision-capable main "
        "model to inspect. Prefer this primary image-read path for "
        "agent-discovered images when the main model supports vision. "
        "With a non-vision main model, pixels were not inspected by the "
        "active main model; switch to a vision-capable main model or use "
        "vision_analyze for an auxiliary vision fallback. Blocks "
        "private/internal URLs, revalidates redirects, enforces a download "
        "cap, and does not analyze by itself or call any LLM/API."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path_or_url": {
                "type": "string",
                "description": "Local filesystem path or safe HTTP(S) URL to the image to load.",
            },
            "question": {
                "type": "string",
                "description": "Optional question or instruction to include with the image.",
            },
        },
        "required": ["path_or_url"],
    },
}


def _error(code: str, message: str) -> str:
    return json.dumps({"ok": False, "error": code, "message": message})


class _ReadImageURLRejected(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and (parsed.netloc or parsed.scheme in {"data", "file"}))


def _read_local_image(path: Path) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
    """Return (raw_bytes, mime, error_code) for a local image path."""
    if not path.exists():
        return None, None, "not_found"
    if not path.is_file():
        return None, None, "not_file"
    try:
        raw = path.read_bytes()
    except OSError:
        return None, None, "read_failed"
    mime = _sniff_mime_from_bytes(raw)
    if not mime:
        return None, None, "not_image"
    return raw, mime, None


def _validate_http_image_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise _ReadImageURLRejected(
            "unsupported_url",
            "Only http:// and https:// image URLs are supported",
        )
    if not is_safe_url(url):
        raise _ReadImageURLRejected(
            "unsafe_url",
            f"Blocked private/internal image URL: {url}",
        )
    blocked = check_website_access(url)
    if blocked:
        raise _ReadImageURLRejected(
            "policy_blocked",
            str(blocked.get("message") or "Website access is blocked by policy"),
        )


def _content_length(headers: Any) -> Optional[int]:
    try:
        raw_value = headers.get("content-length")
    except AttributeError:
        return None
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def _redirect_guard(response: Any) -> None:
    if getattr(response, "is_redirect", False) and getattr(response, "next_request", None):
        _validate_http_image_url(str(response.next_request.url))


def _body_from_response(response: Any, final_url: str) -> tuple[Optional[bytes], Optional[str], Optional[str]]:
    declared_length = _content_length(getattr(response, "headers", {}))
    if declared_length is not None and declared_length > READ_IMAGE_MAX_DOWNLOAD_BYTES:
        return (
            None,
            "image_too_large",
            f"Image URL content-length is {declared_length} bytes; max is {READ_IMAGE_MAX_DOWNLOAD_BYTES}",
        )

    chunks: list[bytes] = []
    total = 0
    if hasattr(response, "iter_bytes"):
        iterator = response.iter_bytes()
    else:
        iterator = (bytes(getattr(response, "content", b"")),)
    for chunk in iterator:
        if not chunk:
            continue
        total += len(chunk)
        if total > READ_IMAGE_MAX_DOWNLOAD_BYTES:
            return (
                None,
                "image_too_large",
                f"Downloaded image from {final_url} exceeded max size {READ_IMAGE_MAX_DOWNLOAD_BYTES} bytes",
            )
        chunks.append(bytes(chunk))
    return b"".join(chunks), None, None


def _download_url_image(url: str) -> tuple[Optional[bytes], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """Return (raw_bytes, mime, error_code, message, final_url) for a safe image URL."""
    try:
        _validate_http_image_url(url)
        headers = {
            "User-Agent": "Hermes read_image/1.0",
            "Accept": "image/*,*/*;q=0.8",
        }
        with httpx.Client(
            timeout=READ_IMAGE_DOWNLOAD_TIMEOUT,
            follow_redirects=True,
            event_hooks={"response": [_redirect_guard]},
        ) as client:
            if hasattr(client, "stream"):
                response_cm = client.stream("GET", url, headers=headers)
            else:
                response_cm = client.get(url, headers=headers)
            with response_cm as response:
                response.raise_for_status()
                final_url = str(getattr(response, "url", url))
                _validate_http_image_url(final_url)
                body, code, message = _body_from_response(response, final_url)
                if code:
                    return None, None, code, message, final_url

            assert body is not None
            mime = _sniff_mime_from_bytes(body)
            if not mime:
                return None, None, "not_image", f"URL did not return a supported image: {final_url}", final_url
            return body, mime, None, None, final_url
    except _ReadImageURLRejected as exc:
        return None, None, exc.code, exc.message, url
    except Exception as exc:
        return None, None, "download_failed", f"Could not download image URL: {exc}", url


def handle_read_image(args: Dict[str, Any], **kwargs: Any) -> Any:
    """Load a local image as a multimodal tool-result envelope.

    Returns a dict for success and a JSON string for fail-closed structured
    errors, matching existing tool-result conventions.
    """
    raw_path = str(args.get("path_or_url") or "").strip()
    if not raw_path:
        return _error("missing_path", "path_or_url is required")
    source: str
    if _looks_like_url(raw_path):
        parsed = urlparse(raw_path)
        if parsed.scheme not in {"http", "https"}:
            return _error(
                "unsupported_url",
                "read_image supports local filesystem paths or http(s) image URLs only",
            )
        image_bytes, mime, code, message, final_url = _download_url_image(raw_path)
        if code:
            return _error(code, message or f"Could not load image URL: {raw_path}")
        source = final_url or raw_path
    else:
        path = Path(raw_path).expanduser()
        image_bytes, mime, code = _read_local_image(path)
        if code:
            messages = {
                "not_found": f"Image path does not exist: {path}",
                "not_file": f"Image path is not a file: {path}",
                "read_failed": f"Could not read image path: {path}",
                "not_image": f"File is not a supported image: {path}",
            }
            return _error(code, messages.get(code, f"Could not load image: {path}"))
        source = str(path)

    assert image_bytes is not None and mime is not None  # for type checkers
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    question = str(args.get("question") or "").strip()
    base_text = question or "What do you see in this image?"
    text = f"{base_text}\n\n[Image loaded from: {source}]"
    summary = f"Loaded image from {source} ({mime}, {len(image_bytes)} bytes)."
    if question:
        summary += f" Question: {question}"

    return {
        "_multimodal": True,
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
        "text_summary": summary,
        "meta": {"source": source, "mime": mime, "bytes": len(image_bytes)},
    }


registry.register(
    name="read_image",
    toolset="vision",
    schema=READ_IMAGE_SCHEMA,
    handler=handle_read_image,
    check_fn=lambda: True,
    emoji="🖼️",
)
