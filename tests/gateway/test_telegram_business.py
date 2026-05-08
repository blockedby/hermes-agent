"""Focused tests for Telegram Business assistant-mode MVP support."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import HomeChannel, Platform, PlatformConfig
from gateway.platforms import telegram as telegram_mod
from gateway.platforms.base import MessageEvent, MessageType, ProcessingOutcome, SendResult
from gateway.platforms.telegram import ApplicationHandlerStop, TelegramAdapter
from gateway.session import SessionSource, build_session_key
from telegram.constants import ChatType


def _make_adapter(*, owner_chat_id: str = "999") -> TelegramAdapter:
    adapter = object.__new__(TelegramAdapter)
    adapter.platform = Platform.TELEGRAM
    adapter.config = PlatformConfig(
        enabled=True,
        token="test-token",
        home_channel=HomeChannel(Platform.TELEGRAM, owner_chat_id, "Owner"),
        extra={},
    )
    adapter._bot = SimpleNamespace(username="hermesbot", send_message=AsyncMock(), send_chat_action=AsyncMock())
    adapter._bot.send_message.return_value = SimpleNamespace(message_id=101)
    adapter._approval_state = {}
    adapter._slash_confirm_state = {}
    adapter._business_approval_state = {}
    adapter._business_can_reply = {}
    adapter._pending_text_batches = {}
    adapter._pending_text_batch_tasks = {}
    adapter._text_batch_delay_seconds = 0
    adapter._message_handler = AsyncMock()
    adapter._model_picker_state = {}
    adapter._disable_link_previews = False
    return adapter


def _telegram_message(*, text: str = "hello"):
    return SimpleNamespace(
        text=text,
        caption=None,
        chat=SimpleNamespace(id=12345, type=ChatType.PRIVATE, title=None, full_name="Customer"),
        from_user=SimpleNamespace(id=67890, full_name="Customer User"),
        message_thread_id=None,
        message_id=55,
        reply_to_message=None,
        date=None,
    )


def _business_message(*, text: str = "hello", connection_id: str = "bc-1"):
    msg = _telegram_message(text=text)
    msg.business_connection_id = connection_id
    return msg


def _allow_business_reply(adapter: TelegramAdapter, connection_id: str = "bc-1") -> None:
    adapter._business_can_reply[connection_id] = True


def test_record_business_connection_can_reply_rights():
    adapter = _make_adapter()

    enabled = SimpleNamespace(id="bc-enabled", is_enabled=True, rights=SimpleNamespace(can_reply=True))
    disabled = SimpleNamespace(id="bc-disabled", is_enabled=False, rights=SimpleNamespace(can_reply=True))
    no_reply = SimpleNamespace(id="bc-no-reply", is_enabled=True, rights=SimpleNamespace(can_reply=False))

    assert adapter._record_business_connection(enabled) == "bc-enabled"
    assert adapter._record_business_connection(disabled) == "bc-disabled"
    assert adapter._record_business_connection(no_reply) == "bc-no-reply"

    assert adapter._business_can_reply["bc-enabled"] is True
    assert adapter._business_can_reply["bc-disabled"] is False
    assert adapter._business_can_reply["bc-no-reply"] is False


def test_build_message_event_marks_business_session_thread():
    adapter = _make_adapter()

    event = adapter._build_message_event(_business_message(connection_id="bc-42"), MessageType.TEXT, update_id=7)

    assert event.source.chat_type == "dm"
    assert event.source.chat_id == "12345"
    assert event.source.thread_id == "business:bc-42"
    assert event.source.chat_topic == "Telegram Business"
    assert event.platform_update_id == 7


def test_business_session_key_is_isolated_from_normal_dm():
    adapter = _make_adapter()

    normal_event = adapter._build_message_event(_telegram_message(), MessageType.TEXT, update_id=6)
    business_event = adapter._build_message_event(_business_message(connection_id="bc-42"), MessageType.TEXT, update_id=7)

    assert normal_event.source.thread_id is None
    assert normal_event.source.chat_topic is None
    assert business_event.source.thread_id == "business:bc-42"
    assert business_event.source.to_dict()["chat_topic"] == "Telegram Business"
    assert build_session_key(normal_event.source) == "agent:main:telegram:dm:12345"
    assert build_session_key(business_event.source) == "agent:main:telegram:dm:12345:business:bc-42"


@pytest.mark.asyncio
async def test_business_update_enqueues_text_and_stops_normal_handlers():
    adapter = _make_adapter()
    adapter._enqueue_text_event = MagicMock()
    update = SimpleNamespace(
        update_id=88,
        business_connection=None,
        business_message=_business_message(text="hi there", connection_id="bc-9"),
        edited_business_message=None,
        deleted_business_messages=None,
    )

    with pytest.raises(ApplicationHandlerStop):
        await adapter._handle_business_update(update, None)

    adapter._enqueue_text_event.assert_called_once()
    event = adapter._enqueue_text_event.call_args.args[0]
    assert event.text == "hi there"
    assert event.source.thread_id == "business:bc-9"
    assert adapter._message_from_update(update) is None


@pytest.mark.asyncio
async def test_business_send_creates_owner_draft_not_customer_send():
    adapter = _make_adapter(owner_chat_id="999")
    _allow_business_reply(adapter)

    result = await adapter.send("12345", "Draft to approve", metadata={"thread_id": "business:bc-1"})

    assert result.success is True
    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
    assert "business_connection_id" not in call_kwargs
    assert "Draft to approve" in call_kwargs["text"]
    assert len(adapter._business_approval_state) == 1
    approval = next(iter(adapter._business_approval_state.values()))
    assert approval == {
        "chat_id": "12345",
        "business_connection_id": "bc-1",
        "draft": "Draft to approve",
    }


@pytest.mark.asyncio
async def test_business_owner_draft_includes_clickable_customer_and_quoted_question(monkeypatch):
    monkeypatch.setattr(
        telegram_mod,
        "InlineKeyboardButton",
        lambda text, callback_data=None, url=None: SimpleNamespace(
            text=text,
            callback_data=callback_data,
            url=url,
        ),
    )
    monkeypatch.setattr(
        telegram_mod,
        "InlineKeyboardMarkup",
        lambda rows: SimpleNamespace(inline_keyboard=rows),
    )

    adapter = _make_adapter(owner_chat_id="999")
    _allow_business_reply(adapter)

    result = await adapter.send(
        "12345",
        "Антананариву.",
        metadata={
            "thread_id": "business:bc-1",
            "inbound_text": "Столица Мадагаскара?",
            "source_user_id": "67890",
            "source_user_name": "Customer User",
            "telegram_username": "ggg69",
        },
    )

    assert result.success is True
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["parse_mode"] == "HTML"
    assert '<a href="https://t.me/ggg69">@ggg69</a>' in call_kwargs["text"]
    assert "Question:" in call_kwargs["text"]
    assert "<blockquote>Столица Мадагаскара?</blockquote>" in call_kwargs["text"]
    assert "Draft:" in call_kwargs["text"]
    assert "<blockquote>Антананариву.</blockquote>" in call_kwargs["text"]
    keyboard = call_kwargs["reply_markup"].inline_keyboard
    assert keyboard[0][0].text == "👤 Open chat"
    assert keyboard[0][0].url == "https://t.me/ggg69"


@pytest.mark.asyncio
async def test_business_unknown_can_reply_suppresses_draft_until_connection_update():
    adapter = _make_adapter(owner_chat_id="999")

    result = await adapter.send("12345", "Draft to approve", metadata={"thread_id": "business:bc-1"})

    assert result.success is True
    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
    assert "cannot currently reply" in call_kwargs["text"]
    assert adapter._business_approval_state == {}


@pytest.mark.asyncio
async def test_business_unknown_can_reply_refreshes_connection_before_suppressing():
    adapter = _make_adapter(owner_chat_id="999")
    adapter._bot.get_business_connection = AsyncMock(
        return_value=SimpleNamespace(id="bc-1", is_enabled=True, rights=SimpleNamespace(can_reply=True))
    )

    result = await adapter.send("12345", "Draft to approve", metadata={"thread_id": "business:bc-1"})

    assert result.success is True
    adapter._bot.get_business_connection.assert_awaited_once_with("bc-1")
    assert adapter._business_can_reply["bc-1"] is True
    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
    assert "Draft to approve" in call_kwargs["text"]
    assert "cannot currently reply" not in call_kwargs["text"]
    assert len(adapter._business_approval_state) == 1


@pytest.mark.asyncio
async def test_business_approval_send_uses_business_connection_id():
    adapter = _make_adapter()
    _allow_business_reply(adapter)
    adapter._is_callback_user_authorized = MagicMock(return_value=True)
    adapter._business_approval_state["approve-1"] = {
        "chat_id": "12345",
        "business_connection_id": "bc-1",
        "draft": "Approved text",
    }
    query = SimpleNamespace(
        data="ba:s:approve-1",
        from_user=SimpleNamespace(id=111, first_name="Owner"),
        message=SimpleNamespace(
            chat_id=999,
            chat=SimpleNamespace(type=ChatType.PRIVATE),
            message_thread_id=None,
        ),
        answer=AsyncMock(),
        edit_message_text=AsyncMock(),
    )
    update = SimpleNamespace(callback_query=query)

    await adapter._handle_callback_query(update, None)

    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 12345
    assert call_kwargs["business_connection_id"] == "bc-1"
    assert call_kwargs["text"] == "Approved text"
    query.answer.assert_awaited_with(text="Sent")


@pytest.mark.asyncio
async def test_business_approval_denies_without_explicit_authorization():
    adapter = _make_adapter(owner_chat_id="999")
    _allow_business_reply(adapter)
    adapter._business_approval_state["approve-1"] = {
        "chat_id": "12345",
        "business_connection_id": "bc-1",
        "draft": "Approved text",
    }
    query = SimpleNamespace(
        data="ba:s:approve-1",
        from_user=SimpleNamespace(id=111, first_name="Owner", username=None),
        message=SimpleNamespace(
            chat_id=999,
            chat=SimpleNamespace(type=ChatType.PRIVATE),
            message_thread_id=None,
        ),
        answer=AsyncMock(),
        edit_message_text=AsyncMock(),
    )

    await adapter._handle_callback_query(SimpleNamespace(callback_query=query), None)

    adapter._bot.send_message.assert_not_called()
    query.answer.assert_awaited_with(text="⛔ You are not authorized to approve business drafts.")
    assert "approve-1" in adapter._business_approval_state


@pytest.mark.asyncio
async def test_business_approval_cancel_does_not_send_to_customer():
    adapter = _make_adapter()
    adapter._is_callback_user_authorized = MagicMock(return_value=True)
    adapter._business_approval_state["approve-1"] = {
        "chat_id": "12345",
        "business_connection_id": "bc-1",
        "draft": "Cancelled text",
    }
    query = SimpleNamespace(
        data="ba:c:approve-1",
        from_user=SimpleNamespace(id=111, first_name="Owner"),
        message=SimpleNamespace(
            chat_id=999,
            chat=SimpleNamespace(type=ChatType.PRIVATE),
            message_thread_id=None,
        ),
        answer=AsyncMock(),
        edit_message_text=AsyncMock(),
    )
    update = SimpleNamespace(callback_query=query)

    await adapter._handle_callback_query(update, None)

    adapter._bot.send_message.assert_not_called()
    assert "approve-1" not in adapter._business_approval_state
    query.answer.assert_awaited_with(text="Cancelled")
    query.edit_message_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_business_typing_is_suppressed_before_owner_approval():
    adapter = _make_adapter()

    await adapter.send_typing("12345", metadata={"thread_id": "business:bc-1"})

    adapter._bot.send_chat_action.assert_not_awaited()


@pytest.mark.asyncio
async def test_normal_telegram_send_does_not_include_business_connection_id():
    adapter = _make_adapter()

    result = await adapter.send("12345", "Normal Telegram reply", metadata={})

    assert result.success is True
    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 12345
    assert call_kwargs["text"]
    assert "business_connection_id" not in call_kwargs


@pytest.mark.asyncio
async def test_business_reactions_are_suppressed():
    adapter = _make_adapter()
    adapter._bot.set_message_reaction = AsyncMock()
    event = MessageEvent(
        text="hello",
        source=SessionSource(
            platform=Platform.TELEGRAM,
            chat_id="12345",
            chat_type="dm",
            user_id="67890",
            thread_id="business:bc-1",
            chat_topic="Telegram Business",
        ),
        message_id="55",
    )
    adapter._reactions_enabled = MagicMock(return_value=True)

    await adapter.on_processing_start(event)
    await adapter.on_processing_complete(event, ProcessingOutcome.SUCCESS)

    adapter._bot.set_message_reaction.assert_not_called()


@pytest.mark.asyncio
async def test_business_exec_approval_routes_to_owner_not_customer():
    adapter = _make_adapter(owner_chat_id="999")

    result = await adapter.send_exec_approval(
        "12345",
        "rm -rf /tmp/example",
        session_key="agent:main:telegram:dm:12345:business:bc-1",
        metadata={"thread_id": "business:bc-1"},
    )

    assert result.success is True
    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
    assert "business_connection_id" not in call_kwargs
    assert "rm -rf" in call_kwargs["text"]
    assert adapter._approval_state == {1: "agent:main:telegram:dm:12345:business:bc-1"}


@pytest.mark.asyncio
async def test_business_update_prompt_routes_to_owner_not_customer():
    adapter = _make_adapter(owner_chat_id="999")

    result = await adapter.send_update_prompt(
        "12345",
        "Proceed with update?",
        default="n",
        metadata={"thread_id": "business:bc-1"},
    )

    assert result.success is True
    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
    assert "business_connection_id" not in call_kwargs
    assert "Proceed with update?" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_business_slash_confirm_routes_to_owner_not_customer():
    adapter = _make_adapter(owner_chat_id="999")

    result = await adapter.send_slash_confirm(
        "12345",
        "Confirm",
        "Reload MCP?",
        session_key="agent:main:telegram:dm:12345:business:bc-1",
        confirm_id="c1",
        metadata={"thread_id": "business:bc-1"},
    )

    assert result.success is True
    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 999
    assert "business_connection_id" not in call_kwargs
    assert "Reload MCP?" in call_kwargs["text"]
    assert adapter._slash_confirm_state == {"c1": "agent:main:telegram:dm:12345:business:bc-1"}


@pytest.mark.asyncio
async def test_unauthorized_business_pairing_notice_routes_to_owner_not_customer():
    from gateway.run import GatewayRunner

    adapter = _make_adapter(owner_chat_id="999")
    adapter._notify_business_owner = AsyncMock(return_value=SendResult(success=True))
    adapter.send = AsyncMock(side_effect=AssertionError("must not send directly to business customer"))

    runner = object.__new__(GatewayRunner)
    runner.adapters = {Platform.TELEGRAM: adapter}
    runner._is_user_authorized = MagicMock(return_value=False)
    runner._get_unauthorized_dm_behavior = MagicMock(return_value="pair")
    runner.pairing_store = SimpleNamespace(
        _is_rate_limited=MagicMock(return_value=False),
        generate_code=MagicMock(return_value="abc123"),
    )

    source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="12345",
        chat_type="dm",
        user_id="67890",
        user_name="Customer User",
        thread_id="business:bc-1",
        chat_topic="Telegram Business",
    )
    event = MessageEvent(text="hello", source=source)

    result = await runner._handle_message(event)

    assert result is None
    adapter.send.assert_not_called()
    adapter._notify_business_owner.assert_awaited_once()
    notice = adapter._notify_business_owner.call_args.args[0]
    assert "pairing approve telegram abc123" in notice
    assert "Customer chat: 12345" in notice
