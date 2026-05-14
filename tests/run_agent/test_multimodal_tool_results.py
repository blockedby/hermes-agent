"""Regression tests for multimodal tool-result handling.

These lock down the native read_image/computer_use contract: tool handlers may
return a ``_multimodal`` envelope, but the next model call must see list-shaped
content parts while logs/previews/persistence paths use a text-only summary.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from run_agent import AIAgent


_B64_MARKER = "QUJDREVGRw=="
_DATA_URL = f"data:image/png;base64,{_B64_MARKER}"


def _make_tool_defs(*names: str) -> list:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": f"{name} tool",
                "parameters": {"type": "object", "properties": {}},
            },
        }
        for name in names
    ]


@pytest.fixture()
def agent():
    with (
        patch("run_agent.get_tool_definitions", return_value=_make_tool_defs("web_search", "read_file")),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        a = AIAgent(
            api_key="test-key-1234567890",
            base_url="https://openrouter.ai/api/v1",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
        a.client = MagicMock()
        return a


def _tool_call(name: str, call_id: str, arguments: str = "{}"):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _assistant_msg(*tool_calls):
    return SimpleNamespace(content="", tool_calls=list(tool_calls))


def _multimodal_result(summary: str = "screenshot summary"):
    return {
        "_multimodal": True,
        "text_summary": summary,
        "content": [
            {"type": "text", "text": summary},
            {"type": "image_url", "image_url": {"url": _DATA_URL}},
        ],
    }


def test_sequential_multimodal_tool_result_appends_list_content_without_preview_base64(agent, capsys):
    """Sequential tool execution must preserve multipart content for the next LLM call.

    The human/CLI preview is a text-only path; it must not stringify the
    envelope and leak embedded image bytes.
    """
    agent.quiet_mode = False
    agent.verbose_logging = False
    agent.log_prefix_chars = 500
    messages = []

    with patch("run_agent.handle_function_call", return_value=_multimodal_result()):
        agent._execute_tool_calls_sequential(
            _assistant_msg(_tool_call("web_search", "call_seq")),
            messages,
            "task-1",
        )

    assert len(messages) == 1
    tool_content = messages[0]["content"]
    assert isinstance(tool_content, list)
    assert tool_content[0] == {"type": "text", "text": "screenshot summary"}
    assert tool_content[1]["type"] == "image_url"
    assert _DATA_URL in json.dumps(tool_content)

    preview = capsys.readouterr().out
    assert "screenshot summary" in preview
    assert _B64_MARKER not in preview
    assert "_multimodal" not in preview


def test_concurrent_multimodal_tool_result_appends_list_content(agent):
    """Concurrent tool execution must unwrap _multimodal envelopes in call order."""
    messages = []

    def fake_handle(name, args, task_id, **kwargs):
        return _multimodal_result(f"summary for {args['q']}")

    msg = _assistant_msg(
        _tool_call("web_search", "call_a", '{"q":"alpha"}'),
        _tool_call("web_search", "call_b", '{"q":"beta"}'),
    )
    with patch("run_agent.handle_function_call", side_effect=fake_handle):
        agent._execute_tool_calls_concurrent(msg, messages, "task-1")

    assert [m["tool_call_id"] for m in messages] == ["call_a", "call_b"]
    assert all(isinstance(m["content"], list) for m in messages)
    assert messages[0]["content"][0]["text"] == "summary for alpha"
    assert messages[1]["content"][0]["text"] == "summary for beta"


def test_multimodal_trajectory_summary_strips_base64(agent):
    """Trajectory persistence must use text_summary instead of image bytes."""
    messages = [
        {"role": "user", "content": "capture screen"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_img",
                    "type": "function",
                    "function": {"name": "computer_use", "arguments": "{}"},
                }
            ],
        },
        {
            "role": "tool",
            "name": "computer_use",
            "tool_call_id": "call_img",
            "content": _multimodal_result("safe screenshot summary"),
        },
    ]

    trajectory = agent._convert_to_trajectory_format(messages, "capture screen", completed=True)
    dumped = json.dumps(trajectory, ensure_ascii=False)
    assert "safe screenshot summary" in dumped
    assert _B64_MARKER not in dumped
    assert "data:image/png;base64" not in dumped
