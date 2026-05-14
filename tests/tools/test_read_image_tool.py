"""Regression tests for the native local read_image MVP."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from tools.read_image_tool import handle_read_image


def _png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQABpfZFQAAAAABJRU5ErkJggg=="
    )


def _image_url_part(result: dict) -> dict:
    return next(part for part in result["content"] if part.get("type") == "image_url")


def test_local_png_returns_multimodal_content_parts(tmp_path: Path):
    image_path = tmp_path / "pixel.png"
    image_path.write_bytes(_png_bytes())

    result = handle_read_image({"path_or_url": str(image_path), "question": "What is shown?"})

    assert result["_multimodal"] is True
    assert len(result["content"]) == 2
    assert result["content"][0] == {
        "type": "text",
        "text": f"What is shown?\n\n[Image loaded from: {image_path}]",
    }
    image_part = _image_url_part(result)
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")
    assert result["text_summary"]
    assert "base64," not in result["text_summary"]
    assert "data:image" not in result["text_summary"]


def test_mime_is_sniffed_from_bytes_not_extension(tmp_path: Path):
    image_path = tmp_path / "misleading.jpg"
    image_path.write_bytes(_png_bytes())

    result = handle_read_image({"path_or_url": str(image_path)})

    image_part = _image_url_part(result)
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")


def test_blank_question_uses_neutral_text_part(tmp_path: Path):
    image_path = tmp_path / "pixel.png"
    image_path.write_bytes(_png_bytes())

    result = handle_read_image({"path_or_url": str(image_path)})

    assert result["content"][0] == {
        "type": "text",
        "text": f"What do you see in this image?\n\n[Image loaded from: {image_path}]",
    }


def test_invalid_local_inputs_fail_closed(tmp_path: Path):
    missing = tmp_path / "missing.png"
    directory = tmp_path / "images"
    directory.mkdir()
    not_image = tmp_path / "note.txt"
    not_image.write_text("not an image", encoding="utf-8")

    cases = [
        ({"path_or_url": str(missing)}, "not_found"),
        ({"path_or_url": str(directory)}, "not_file"),
        ({"path_or_url": str(not_image)}, "not_image"),
        ({"path_or_url": "https://example.com/image.png"}, "unsupported_url"),
        ({"path_or_url": ""}, "missing_path"),
    ]

    for args, code in cases:
        raw = handle_read_image(args)
        assert isinstance(raw, str)
        parsed = json.loads(raw)
        assert parsed["ok"] is False
        assert parsed["error"] == code
        assert "message" in parsed
        assert "base64" not in raw
        assert "data:image" not in raw
