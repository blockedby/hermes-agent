# TDD Plan: Telegram Business `direct_messages_topic_id` regression

Date: 2026-05-25
Repo: `/home/kcnc/.hermes/hermes-agent`

## Problem

Telegram Business draft approval send fails before calling Telegram API:

```text
ValueError: invalid literal for int() with base 10: 'business:<business_connection_id>'
```

Root cause: `GatewayRunner._thread_metadata_for_source()` treats every Telegram `dm` source with `thread_id` as a numeric Direct Messages topic. Business sessions use an internal thread marker:

```text
business:<business_connection_id>[:topic:<direct_messages_topic_id>]
```

That marker is incorrectly copied into `metadata["direct_messages_topic_id"]`, persisted into `business_approvals.json`, and later converted with `int(...)` when owner clicks **Send**.

## Desired behavior

- Business session thread marker must remain a Business marker, not a Telegram `direct_messages_topic_id`.
- Plain Business chats without a real direct topic must save:

```json
"direct_messages_topic_id": null
```

- Business chats with a real Telegram Direct Messages topic must save only the numeric topic id.
- Normal Telegram DM topic behavior must remain unchanged.
- Existing corrupted pending approvals should not crash on Send; non-numeric `direct_messages_topic_id` must be ignored or rejected safely.

## Acceptance criteria

1. A Business `SessionSource` with `thread_id="business:bc-1"` does **not** produce `metadata["direct_messages_topic_id"]`.
2. A Business `SessionSource` with `thread_id="business:bc-1:topic:338575"` produces `direct_messages_topic_id="338575"`.
3. A normal Telegram DM source with `thread_id="338575"` still produces `direct_messages_topic_id="338575"` and `telegram_dm_topic_reply_fallback=True`.
4. Business approval send with `direct_messages_topic_id="business:bc-1"` does not raise `ValueError` and does not pass that value to Telegram API.
5. Business approval send with `direct_messages_topic_id="338575"` passes `direct_messages_topic_id=338575` to Telegram API.
6. Focused Telegram Business tests pass.

## Red tests first

### Test 1: Gateway metadata does not coerce Business thread marker into DM topic

File: `tests/gateway/test_telegram_business.py` or a smaller gateway metadata test file.

Create a `GatewayRunner` or use existing helper if available. Build a source:

```python
source = SessionSource(
    platform=Platform.TELEGRAM,
    chat_id="12345",
    chat_type="dm",
    thread_id="business:bc-1",
)
```

Assert:

```python
metadata = runner._thread_metadata_for_source(source)
assert metadata["thread_id"] == "business:bc-1"
assert "direct_messages_topic_id" not in metadata
assert "telegram_dm_topic_reply_fallback" not in metadata  # or false, depending chosen API
```

### Test 2: Gateway metadata extracts real Business direct topic

```python
source.thread_id = "business:bc-1:topic:338575"
metadata = runner._thread_metadata_for_source(source)
assert metadata["thread_id"] == "business:bc-1:topic:338575"
assert metadata["direct_messages_topic_id"] == "338575"
```

Do not set `telegram_dm_topic_reply_fallback` for Business unless it is intentionally needed and covered.

### Test 3: Normal DM topic remains unchanged

```python
source.thread_id = "338575"
metadata = runner._thread_metadata_for_source(source, reply_to_message_id="55")
assert metadata["thread_id"] == "338575"
assert metadata["direct_messages_topic_id"] == "338575"
assert metadata["telegram_dm_topic_reply_fallback"] is True
assert metadata["telegram_reply_to_message_id"] == "55"
```

### Test 4: Corrupted approval is handled safely

Existing area: `tests/gateway/test_telegram_business.py` near `test_business_approval_send_uses_business_connection_id`.

Setup approval:

```python
adapter._business_approval_state["approve-1"] = {
    "customer_chat_id": "12345",
    "business_connection_id": "bc-1",
    "direct_messages_topic_id": "business:bc-1",
    "draft": "Approved text",
    ...
}
```

Click `ba:s:approve-1`.

Assert:

```python
adapter._bot.send_message.assert_called_once()
kwargs = adapter._bot.send_message.call_args.kwargs
assert kwargs["business_connection_id"] == "bc-1"
assert "direct_messages_topic_id" not in kwargs
assert kwargs["text"] == "Approved text"
query.answer.assert_awaited_with(text="Sent")
```

### Test 5: Numeric approval topic still sends correctly

Existing test already covers this:

```python
assert call_kwargs["direct_messages_topic_id"] == 338575
```

Keep it green.

## Implementation plan

### Step 1: Add a validator/helper

In `gateway/platforms/telegram.py` or shared helper:

```python
@staticmethod
 किंवा @classmethod
def _normalize_direct_messages_topic_id(value: Any) -> Optional[str]:
    if value is None or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not re.fullmatch(r"\d+", text):
        return None
    return text
```

Use it in:

- `_metadata_direct_messages_topic_id()`
- `_direct_messages_topic_id_from_message()` if useful
- Business approval callback before `int(...)`
- `_send_business_direct_text()` before `int(...)`

### Step 2: Fix `GatewayRunner._thread_metadata_for_source()`

In `gateway/run.py`:

- Detect Telegram Business thread marker before ordinary DM-topic fallback.
- If `thread_id.startswith("business:")`:
  - keep `metadata["thread_id"] = thread_id`;
  - if marker contains `:topic:<digits>`, set `metadata["direct_messages_topic_id"] = digits`;
  - do **not** set `telegram_dm_topic_reply_fallback=True` for the `business:<connection>` marker itself.

Pseudo:

```python
if platform == Platform.TELEGRAM and chat_type == "dm":
    tid = str(thread_id)
    if tid.startswith("business:"):
        topic = extract_business_topic(tid)
        if topic:
            metadata["direct_messages_topic_id"] = topic
        return metadata

    metadata["telegram_dm_topic_reply_fallback"] = True
    if tid and tid not in {"", "1"} and tid.isdigit():
        metadata["direct_messages_topic_id"] = tid
```

Avoid importing `TelegramAdapter` into `gateway/run.py` if that creates coupling/cycles; a tiny local parse helper is fine.

### Step 3: Defensive send path

In `gateway/platforms/telegram.py` around Business approval send:

```python
direct_topic_id = self._normalize_direct_messages_topic_id(entry.get("direct_messages_topic_id"))
if direct_topic_id:
    kwargs["direct_messages_topic_id"] = int(direct_topic_id)
```

Same defensive normalization in `_send_business_direct_text()`.

### Step 4: Existing corrupted state cleanup

After code fix, either:

- manually remove the bad field from VPS pending approval:

```json
"direct_messages_topic_id": null
```

or

- leave it; defensive send path should ignore it and allow retry.

If status remains `failed_retryable`, confirm callback path permits retry. If not, reset status to `pending` after backup.

## Verification commands

Focused tests:

```bash
cd /home/kcnc/.hermes/hermes-agent
python -m pytest tests/gateway/test_telegram_business.py -q --tb=short
```

If gateway metadata tests are in another file, include it:

```bash
python -m pytest tests/gateway/test_telegram_business.py tests/gateway/test_telegram_thread_fallback.py -q --tb=short
```

Optional broader Telegram regression:

```bash
python -m pytest tests/gateway -q --tb=short
```

VPS smoke after deploy:

```bash
ssh everyday-white 'journalctl --user -u hermes-gateway.service --since "10 minutes ago" --no-pager | grep -Ei "business|ValueError|failed" | tail -80'
```

## Rollout notes

1. Commit locally on `blockedby-main`.
2. Push to `alex/main` only after focused tests pass.
3. Pull on VPS and restart gateway.
4. Retry the existing Business approval Send button or clean/reset the pending approval first.

## Risk notes

- Do not regress normal Telegram private DM topics; they depend on numeric `direct_messages_topic_id` fallback.
- Do not send Business drafts directly unless mode is `auto` or owner clicked **Send**.
- Do not expose `business_connection_id` in final user-facing report unless explicitly requested.
