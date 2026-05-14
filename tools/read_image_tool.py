"""Native local image loader tool.

`read_image` loads a local image file and returns an OpenAI-style multimodal
content envelope. It performs no LLM/API calls; the active main model sees the
pixels when run_agent unwraps the `_multimodal` result into a tool message.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from agent.image_routing import _sniff_mime_from_bytes
from tools.registry import registry


READ_IMAGE_SCHEMA = {
    "name": "read_image",
    "description": (
        "Load a local image file and attach its pixels to the conversation for "
        "the active main model to inspect. Supports local files only and does "
        "not call an external vision model."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path_or_url": {
                "type": "string",
                "description": "Local filesystem path to the image to load.",
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


def handle_read_image(args: Dict[str, Any], **kwargs: Any) -> Any:
    """Load a local image as a multimodal tool-result envelope.

    Returns a dict for success and a JSON string for fail-closed structured
    errors, matching existing tool-result conventions.
    """
    raw_path = str(args.get("path_or_url") or "").strip()
    if not raw_path:
        return _error("missing_path", "path_or_url is required")
    if _looks_like_url(raw_path):
        return _error("unsupported_url", "read_image supports local filesystem paths only")

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

    assert image_bytes is not None and mime is not None  # for type checkers
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    question = str(args.get("question") or "").strip()
    base_text = question or "What do you see in this image?"
    text = f"{base_text}\n\n[Image loaded from: {path}]"
    summary = f"Loaded image from {path} ({mime}, {len(image_bytes)} bytes)."
    if question:
        summary += f" Question: {question}"

    return {
        "_multimodal": True,
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
        "text_summary": summary,
    }


registry.register(
    name="read_image",
    toolset="vision",
    schema=READ_IMAGE_SCHEMA,
    handler=handle_read_image,
    check_fn=lambda: True,
    emoji="🖼️",
)
