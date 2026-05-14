"""Regression tests for Codex Responses multimodal payload conversion."""

from agent.codex_responses_adapter import (
    _chat_messages_to_responses_input,
    _preflight_codex_input_items,
)


_B64_MARKER = "QUJDREVGRw=="
_DATA_URL = f"data:image/png;base64,{_B64_MARKER}"


def test_tool_multimodal_content_parts_convert_image_url_to_input_image():
    """Tool results with chat-style image_url parts must not be stringified.

    Native read_image/computer_use returns list-shaped tool content after
    run_agent unwraps the _multimodal envelope. Codex Responses needs the image
    part normalized to input_image instead of the chat-only image_url shape.
    """
    items = _chat_messages_to_responses_input(
        [
            {
                "role": "tool",
                "tool_call_id": "call_image",
                "content": [
                    {"type": "text", "text": "screenshot summary"},
                    {"type": "image_url", "image_url": {"url": _DATA_URL, "detail": "high"}},
                ],
            }
        ]
    )

    assert items == [
        {
            "type": "function_call_output",
            "call_id": "call_image",
            "output": [
                {"type": "input_text", "text": "screenshot summary"},
                {"type": "input_image", "image_url": _DATA_URL, "detail": "high"},
            ],
        }
    ]


def test_preflight_preserves_function_call_output_multimodal_parts():
    """Preflight must not coerce multimodal function output back to a string."""
    normalized = _preflight_codex_input_items(
        [
            {
                "type": "function_call_output",
                "call_id": "call_image",
                "output": [
                    {"type": "text", "text": "screenshot summary"},
                    {"type": "image_url", "image_url": {"url": _DATA_URL}},
                ],
            }
        ]
    )

    assert normalized == [
        {
            "type": "function_call_output",
            "call_id": "call_image",
            "output": [
                {"type": "input_text", "text": "screenshot summary"},
                {"type": "input_image", "image_url": _DATA_URL},
            ],
        }
    ]
