"""Focused tests for Telegram Business assistant-mode MVP support."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import HomeChannel, Platform, PlatformConfig
from gateway.platforms import telegram as telegram_mod
from gateway.platforms.base import MessageEvent, MessageType, ProcessingOutcome, SendResult
from gateway.platforms.telegram import ApplicationHandlerStop, TelegramAdapter
from gateway.run import GatewayRunner
from gateway.session import SessionSource, build_session_key
from telegram.constants import ChatType
from telegram.error import BadRequest


def _make_adapter(*, owner_chat_id: str = "999", owner_thread_id: str | None = None) -> TelegramAdapter:
    adapter = object.__new__(TelegramAdapter)
    adapter.platform = Platform.TELEGRAM
    adapter.config = PlatformConfig(
        enabled=True,
        token="test-token",
        home_channel=HomeChannel(Platform.TELEGRAM, owner_chat_id, "Owner", thread_id=owner_thread_id),
        extra={},
    )
    adapter._bot = SimpleNamespace(id=1215244879, username="hermesbot", send_message=AsyncMock(), send_chat_action=AsyncMock())
    adapter._bot.send_message.return_value = SimpleNamespace(message_id=101)
    adapter._approval_state = {}
    adapter._slash_confirm_state = {}
    adapter._business_approval_state = {}
    adapter._business_can_reply = {}
    adapter._business_owner_user_ids = {}
    adapter._business_ignore_self_messages = True
    adapter._business_ignored_chat_ids = set()
    adapter._pending_text_batches = {}
    adapter._pending_text_batch_tasks = {}
    adapter._text_batch_delay_seconds = 0
    adapter._message_handler = AsyncMock()
    adapter._model_picker_state = {}
    adapter._dm_topics = {}
    adapter._dm_topics_config = []
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


def _business_message(
    *,
    text: str = "hello",
    connection_id: str = "bc-1",
    chat_id: int = 12345,
    from_user_id: int = 67890,
):
    msg = _telegram_message(text=text)
    msg.chat.id = chat_id
    msg.from_user.id = from_user_id
    msg.business_connection_id = connection_id
    return msg


def _allow_business_reply(adapter: TelegramAdapter, connection_id: str = "bc-1") -> None:
    adapter._business_can_reply[connection_id] = True


def test_business_thread_id_helpers_include_direct_messages_topic_identity():
    non_topic_thread = TelegramAdapter._business_thread_id("bc-42")
    topic_thread = TelegramAdapter._business_thread_id("bc-42", "338575")

    assert non_topic_thread == "business:bc-42"
    assert topic_thread == "business:bc-42:topic:338575"
    assert topic_thread != non_topic_thread

    assert TelegramAdapter._business_connection_id_from_thread(non_topic_thread) == "bc-42"
    assert TelegramAdapter._business_connection_id_from_thread(topic_thread) == "bc-42"

    assert TelegramAdapter._business_connection_id_from_thread(None) is None
    assert TelegramAdapter._business_connection_id_from_thread("") is None
    assert TelegramAdapter._business_connection_id_from_thread("338575") is None
    assert TelegramAdapter._business_connection_id_from_thread("forum:338575") is None


def test_record_business_connection_can_reply_rights():
    adapter = _make_adapter()

    enabled = SimpleNamespace(
        id="bc-enabled",
        is_enabled=True,
        rights=SimpleNamespace(can_reply=True),
        user=SimpleNamespace(id=227049836),
    )
    disabled = SimpleNamespace(id="bc-disabled", is_enabled=False, rights=SimpleNamespace(can_reply=True))
    no_reply = SimpleNamespace(id="bc-no-reply", is_enabled=True, rights=SimpleNamespace(can_reply=False))

    assert adapter._record_business_connection(enabled) == "bc-enabled"
    assert adapter._record_business_connection(disabled) == "bc-disabled"
    assert adapter._record_business_connection(no_reply) == "bc-no-reply"

    assert adapter._business_can_reply["bc-enabled"] is True
    assert adapter._business_can_reply["bc-disabled"] is False
    assert adapter._business_can_reply["bc-no-reply"] is False
    assert adapter._business_owner_user_ids["bc-enabled"] == "227049836"


@pytest.mark.asyncio
async def test_business_update_ignores_owner_self_message_by_default():
    adapter = _make_adapter(owner_chat_id="227049836")
    adapter._enqueue_text_event = MagicMock()
    update = SimpleNamespace(
        update_id=89,
        business_connection=SimpleNamespace(
            id="bc-9",
            is_enabled=True,
            rights=SimpleNamespace(can_reply=True),
            user=SimpleNamespace(id=227049836),
        ),
        business_message=_business_message(text="my own outgoing note", connection_id="bc-9", from_user_id=227049836),
        edited_business_message=None,
        deleted_business_messages=None,
    )

    with pytest.raises(ApplicationHandlerStop):
        await adapter._handle_business_update(update, None)

    adapter._enqueue_text_event.assert_not_called()


@pytest.mark.asyncio
async def test_business_update_can_process_owner_self_message_when_flag_disabled():
    adapter = _make_adapter(owner_chat_id="227049836")
    adapter._business_ignore_self_messages = False
    adapter._enqueue_text_event = MagicMock()
    update = SimpleNamespace(
        update_id=90,
        business_connection=SimpleNamespace(
            id="bc-9",
            is_enabled=True,
            rights=SimpleNamespace(can_reply=True),
            user=SimpleNamespace(id=227049836),
        ),
        business_message=_business_message(text="process me", connection_id="bc-9", from_user_id=227049836),
        edited_business_message=None,
        deleted_business_messages=None,
    )

    with pytest.raises(ApplicationHandlerStop):
        await adapter._handle_business_update(update, None)

    adapter._enqueue_text_event.assert_called_once()


@pytest.mark.asyncio
async def test_business_update_ignores_configured_business_chat_id():
    adapter = _make_adapter()
    adapter._business_ignored_chat_ids = {"227049836"}
    adapter._enqueue_text_event = MagicMock()
    update = SimpleNamespace(
        update_id=91,
        business_connection=None,
        business_message=_business_message(text="ignored chat", connection_id="bc-9", chat_id=227049836),
        edited_business_message=None,
        deleted_business_messages=None,
    )

    with pytest.raises(ApplicationHandlerStop):
        await adapter._handle_business_update(update, None)

    adapter._enqueue_text_event.assert_not_called()


@pytest.mark.asyncio
async def test_business_update_ignores_bot_echo_message_by_default():
    adapter = _make_adapter(owner_chat_id="227049836")
    adapter._enqueue_text_event = MagicMock()
    update = SimpleNamespace(
        update_id=92,
        business_connection=SimpleNamespace(
            id="bc-9",
            is_enabled=True,
            rights=SimpleNamespace(can_reply=True),
            user=SimpleNamespace(id=227049836),
        ),
        business_message=_business_message(
            text="⏳ Retrying in 5.9s (attempt 2/3)...",
            connection_id="bc-9",
            chat_id=1215244879,
            from_user_id=1215244879,
        ),
        edited_business_message=None,
        deleted_business_messages=None,
    )

    with pytest.raises(ApplicationHandlerStop):
        await adapter._handle_business_update(update, None)

    adapter._enqueue_text_event.assert_not_called()


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


def test_business_direct_messages_topic_session_key_isolated_per_topic():
    adapter = _make_adapter()
    first = _business_message(connection_id="bc-42", text="first topic")
    first.direct_messages_topic = SimpleNamespace(topic_id=338575)
    second = _business_message(connection_id="bc-42", text="second topic")
    second.direct_messages_topic = SimpleNamespace(topic_id=338576)

    first_event = adapter._build_message_event(first, MessageType.TEXT, update_id=8)
    second_event = adapter._build_message_event(second, MessageType.TEXT, update_id=9)

    assert first_event.source.thread_id == "business:bc-42:topic:338575"
    assert second_event.source.thread_id == "business:bc-42:topic:338576"
    assert build_session_key(first_event.source) == "agent:main:telegram:dm:12345:business:bc-42:topic:338575"
    assert build_session_key(second_event.source) == "agent:main:telegram:dm:12345:business:bc-42:topic:338576"
    assert build_session_key(first_event.source) != build_session_key(second_event.source)

    metadata = adapter._message_event_metadata(first_event)
    assert metadata["business_connection_id"] == "bc-42"
    assert metadata["direct_messages_topic_id"] == "338575"


def test_direct_messages_topic_builds_thread_and_metadata():
    adapter = _make_adapter()
    msg = _telegram_message(text="topic hello")
    msg.message_thread_id = None
    msg.direct_messages_topic = SimpleNamespace(topic_id=338575)

    event = adapter._build_message_event(msg, MessageType.TEXT, update_id=8)
    metadata = adapter._message_event_metadata(event)

    assert event.source.chat_type == "dm"
    assert event.source.thread_id == "338575"
    assert metadata["thread_id"] == "338575"
    assert metadata["direct_messages_topic_id"] == "338575"


def test_direct_messages_topic_session_key_isolated_per_topic():
    adapter = _make_adapter()
    first = _telegram_message(text="first topic")
    first.direct_messages_topic = SimpleNamespace(topic_id=338575)
    second = _telegram_message(text="second topic")
    second.direct_messages_topic = SimpleNamespace(topic_id=338576)

    first_event = adapter._build_message_event(first, MessageType.TEXT, update_id=9)
    second_event = adapter._build_message_event(second, MessageType.TEXT, update_id=10)

    assert build_session_key(first_event.source) == "agent:main:telegram:dm:12345:338575"
    assert build_session_key(second_event.source) == "agent:main:telegram:dm:12345:338576"
    assert build_session_key(first_event.source) != build_session_key(second_event.source)


def test_business_customer_bypasses_generic_dm_allowlist(monkeypatch):
    runner = object.__new__(GatewayRunner)
    runner.pairing_store = SimpleNamespace(is_approved=lambda *_a, **_kw: False)
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "227049836")

    business_source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="1215244879",
        chat_type="dm",
        user_id="1215244879",
        user_name="Customer",
        thread_id="business:bc-42",
    )
    normal_source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="1215244879",
        chat_type="dm",
        user_id="1215244879",
        user_name="Customer",
    )

    assert runner._is_user_authorized(business_source) is True
    assert runner._is_user_authorized(normal_source) is False


@pytest.mark.asyncio
async def test_business_busy_ack_is_suppressed_but_interrupt_still_happens():
    runner = object.__new__(GatewayRunner)
    runner._busy_input_mode = "interrupt"
    runner._running_agents = {}
    runner._running_agents_ts = {}
    runner._pending_messages = {}
    runner._busy_ack_ts = {}
    runner._draining = False
    runner.adapters = {}

    source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="1215244879",
        chat_type="dm",
        user_id="1215244879",
        user_name="Customer",
        thread_id="business:bc-42",
    )
    event = MessageEvent(text="new customer text", source=source, message_id="m1")
    session_key = build_session_key(source)
    agent = MagicMock()
    adapter = SimpleNamespace(_pending_messages={}, _send_with_retry=AsyncMock())
    runner._running_agents[session_key] = agent
    runner.adapters[Platform.TELEGRAM] = adapter

    result = await runner._handle_active_session_busy_message(event, session_key)

    assert result is True
    agent.interrupt.assert_called_once_with("new customer text")
    adapter._send_with_retry.assert_not_awaited()
    assert session_key not in runner._busy_ack_ts


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
async def test_business_owner_draft_does_not_retry_missing_thread_unthreaded():
    adapter = _make_adapter(owner_chat_id="-100999", owner_thread_id="338512")
    _allow_business_reply(adapter)
    adapter._bot.send_message.side_effect = BadRequest("Message thread not found")

    result = await adapter.send("12345", "Draft to approve", metadata={"thread_id": "business:bc-1"})

    assert result.success is True
    assert adapter._bot.send_message.call_count == 1
    first_kwargs = adapter._bot.send_message.call_args.kwargs
    assert first_kwargs["message_thread_id"] == 338512
    assert "direct_messages_topic_id" not in first_kwargs
    assert adapter._business_approval_state == {}


@pytest.mark.asyncio
async def test_business_owner_notice_does_not_retry_missing_thread_unthreaded():
    adapter = _make_adapter(owner_chat_id="-100999", owner_thread_id="338512")
    adapter._business_can_reply["bc-1"] = False
    adapter._bot.send_message.side_effect = BadRequest("Message thread not found")

    result = await adapter.send("12345", "Draft to approve", metadata={"thread_id": "business:bc-1"})

    assert result.success is True
    assert adapter._bot.send_message.call_count == 1
    first_kwargs = adapter._bot.send_message.call_args.kwargs
    assert first_kwargs["message_thread_id"] == 338512
    assert "direct_messages_topic_id" not in first_kwargs


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
async def test_business_approval_allows_owner_prompt_after_thread_fallback():
    adapter = _make_adapter(owner_chat_id="999", owner_thread_id="338512")
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

    await adapter._handle_callback_query(SimpleNamespace(callback_query=query), None)

    adapter._bot.send_message.assert_called_once()
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 12345
    assert call_kwargs["business_connection_id"] == "bc-1"
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
async def test_private_bot_dm_topic_send_uses_message_thread_id():
    adapter = _make_adapter()

    result = await adapter.send("227049836", "Topic reply", metadata={"thread_id": "338575"})

    assert result.success is True
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 227049836
    assert call_kwargs["message_thread_id"] == 338575
    assert "direct_messages_topic_id" not in call_kwargs


@pytest.mark.asyncio
async def test_direct_messages_topic_send_uses_explicit_direct_messages_topic_id():
    adapter = _make_adapter()

    result = await adapter.send(
        "227049836",
        "Topic reply",
        metadata={"thread_id": "338575", "direct_messages_topic_id": "338575"},
    )

    assert result.success is True
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == 227049836
    assert call_kwargs["direct_messages_topic_id"] == 338575
    assert "message_thread_id" not in call_kwargs


@pytest.mark.asyncio
async def test_dm_topic_thread_not_found_does_not_retry_unthreaded():
    adapter = _make_adapter()
    adapter._bot.send_message.side_effect = BadRequest("Message thread not found")

    result = await adapter.send("227049836", "Topic reply", metadata={"thread_id": "338575"})

    assert result.success is False
    assert adapter._bot.send_message.call_count == 1
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["message_thread_id"] == 338575
    assert "direct_messages_topic_id" not in call_kwargs


@pytest.mark.asyncio
async def test_forum_topic_send_still_uses_message_thread_id():
    adapter = _make_adapter()

    result = await adapter.send("-100123", "Forum reply", metadata={"thread_id": "42"})

    assert result.success is True
    call_kwargs = adapter._bot.send_message.call_args.kwargs
    assert call_kwargs["chat_id"] == -100123
    assert call_kwargs["message_thread_id"] == 42
    assert "direct_messages_topic_id" not in call_kwargs


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


def test_business_customer_source_bypasses_gateway_user_pairing_auth():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner._is_user_authorized = MagicMock(return_value=False)

    source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="12345",
        chat_type="dm",
        user_id="67890",
        user_name="Customer User",
        thread_id="business:bc-1",
        chat_topic="Telegram Business",
    )

    assert runner._is_message_dispatch_authorized(source) is True
    runner._is_user_authorized.assert_not_called()


def test_normal_telegram_dm_still_uses_gateway_user_pairing_auth():
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner._is_user_authorized = MagicMock(return_value=False)

    source = SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="12345",
        chat_type="dm",
        user_id="67890",
        user_name="Customer User",
    )

    assert runner._is_message_dispatch_authorized(source) is False
    runner._is_user_authorized.assert_called_once_with(source)
