"""Regression tests for the native local read_image MVP."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import tools.read_image_tool as read_image_tool
from tools.read_image_tool import handle_read_image


def _png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQABpfZFQAAAAABJRU5ErkJggg=="
    )


def _image_url_part(result: dict) -> dict:
    return next(part for part in result["content"] if part.get("type") == "image_url")


class _FakeResponse:
    def __init__(self, content: bytes, *, url: str = "https://example.com/pixel.png", headers: dict | None = None):
        self.content = content
        self.url = url
        self.headers = headers or {}
        self.is_redirect = False
        self.next_request = None

    def raise_for_status(self) -> None:
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def iter_bytes(self):
        midpoint = max(1, len(self.content) // 2)
        yield self.content[:midpoint]
        yield self.content[midpoint:]


class _FakeRedirectResponse:
    is_redirect = True

    def __init__(self, redirect_url: str):
        self.next_request = SimpleNamespace(url=redirect_url)


class _FakeClient:
    instances: list["_FakeClient"] = []
    response = _FakeResponse(_png_bytes())
    redirect_url: str | None = None

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.get = Mock(return_value=self.response)
        self.stream = Mock(return_value=self.response)
        self.__class__.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None):  # pragma: no cover - replaced by Mock in __init__
        return self.response

    @classmethod
    def reset(cls, response: _FakeResponse | None = None, redirect_url: str | None = None) -> None:
        cls.instances = []
        cls.response = response or _FakeResponse(_png_bytes())
        cls.redirect_url = redirect_url

    @classmethod
    def make_httpx_module(cls):
        def _client_factory(**kwargs):
            client = cls(**kwargs)
            hooks = kwargs.get("event_hooks", {}).get("response", [])
            if cls.redirect_url:
                for hook in hooks:
                    hook(_FakeRedirectResponse(cls.redirect_url))
            return client

        return SimpleNamespace(Client=_client_factory)


def _json_error(result: str) -> dict:
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed["ok"] is False
    assert "base64" not in result
    assert "data:image" not in result
    return parsed


def _install_fake_http(monkeypatch, *, response: _FakeResponse | None = None, redirect_url: str | None = None):
    _FakeClient.reset(response=response, redirect_url=redirect_url)
    monkeypatch.setattr(read_image_tool, "httpx", _FakeClient.make_httpx_module(), raising=False)
    monkeypatch.setattr(read_image_tool, "is_safe_url", lambda url: "127.0.0.1" not in url, raising=False)
    monkeypatch.setattr(read_image_tool, "check_website_access", lambda url: None, raising=False)
    return _FakeClient


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
        ({"path_or_url": "ftp://example.com/image.png"}, "unsupported_url"),
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


def test_http_url_private_host_rejected_before_download(monkeypatch):
    fake_client = _install_fake_http(monkeypatch)

    result = handle_read_image({"path_or_url": "http://127.0.0.1/pixel.png"})

    parsed = _json_error(result)
    assert parsed["error"] == "unsafe_url"
    assert fake_client.instances == []


def test_http_redirect_to_private_host_is_rejected(monkeypatch):
    _install_fake_http(monkeypatch, redirect_url="http://127.0.0.1/secret.png")

    result = handle_read_image({"path_or_url": "https://example.com/pixel.png"})

    parsed = _json_error(result)
    assert parsed["error"] == "unsafe_url"


def test_http_content_length_over_cap_is_rejected(monkeypatch):
    monkeypatch.setattr(read_image_tool, "READ_IMAGE_MAX_DOWNLOAD_BYTES", 8, raising=False)
    _install_fake_http(
        monkeypatch,
        response=_FakeResponse(_png_bytes(), headers={"content-length": "9"}),
    )

    result = handle_read_image({"path_or_url": "https://example.com/pixel.png"})

    parsed = _json_error(result)
    assert parsed["error"] == "image_too_large"


def test_http_actual_body_over_cap_is_rejected(monkeypatch):
    monkeypatch.setattr(read_image_tool, "READ_IMAGE_MAX_DOWNLOAD_BYTES", 8, raising=False)
    _install_fake_http(monkeypatch, response=_FakeResponse(_png_bytes()))

    result = handle_read_image({"path_or_url": "https://example.com/pixel.png"})

    parsed = _json_error(result)
    assert parsed["error"] == "image_too_large"


def test_http_non_image_body_rejected_by_sniffing(monkeypatch):
    _install_fake_http(monkeypatch, response=_FakeResponse(b"not an image", url="https://example.com/photo.png"))

    result = handle_read_image({"path_or_url": "https://example.com/photo.png"})

    parsed = _json_error(result)
    assert parsed["error"] == "not_image"


def test_http_valid_small_png_returns_multimodal_content(monkeypatch):
    _install_fake_http(monkeypatch, response=_FakeResponse(_png_bytes(), url="https://cdn.example.com/pixel.png"))

    result = handle_read_image({"path_or_url": "https://example.com/pixel.png", "question": "Describe it"})

    assert result["_multimodal"] is True
    assert result["content"][0] == {
        "type": "text",
        "text": "Describe it\n\n[Image loaded from: https://cdn.example.com/pixel.png]",
    }
    image_part = _image_url_part(result)
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")
    assert result["meta"]["source"] == "https://cdn.example.com/pixel.png"
    assert "https://cdn.example.com/pixel.png" in result["text_summary"]
    assert "base64," not in result["text_summary"]
    assert "data:image" not in result["text_summary"]
