# Local verification — Telegram Business media ingestion

Date: 2026-05-26
Branch: `epic/telegram-business-media`

## Environment note

The canonical wrapper was used with `HERMES_TEST_VENV=$PWD/venv` because the checkout's `.venv` exists but does not have `pytest` installed. This preserves `scripts/run_tests.sh` behavior while selecting the working repo venv.

## Commands

```bash
python -m py_compile \
  gateway/platforms/telegram.py \
  gateway/platforms/telegram_business_history.py \
  gateway/run.py \
  tests/gateway/test_telegram_business.py \
  tests/gateway/test_stt_config.py
```

Result: passed.

```bash
HERMES_TEST_VENV=$PWD/venv scripts/run_tests.sh \
  tests/gateway/test_telegram_business.py \
  tests/gateway/test_stt_config.py \
  tests/gateway/test_telegram_documents.py \
  tests/gateway/test_telegram_audio_vs_voice.py \
  tests/gateway/test_native_image_buffer_isolation.py \
  tests/gateway/test_vision_memory_leak.py \
  -- -q
```

Result: `134 passed, 0 failed`.

## Evidence mapping

- Business photo with caption in draft mode enqueues a cached `MessageType.PHOTO` event with Business thread id.
- Business image documents route as photo media.
- Business voice in draft mode enqueues cached `MessageType.VOICE` media and records `media_received` history.
- Business watch/new-chat voice schedules background media+STT history persistence without enqueueing an agent turn.
- Business STT write-back from the gateway runner records structured `voice_transcribed` history for Business voice events that enter the agent path.
- Existing Telegram document/media, voice-vs-audio, native image buffer, and vision memory-leak regressions remain green.

## Rollout checklist for EverydayWiteVPS

Local tests do not prove live Telegram behavior. On `EverydayWiteVPS` after deploying/restarting the gateway:

1. Send a Telegram Business photo with caption to a draft/auto chat; confirm agent sees the image/caption.
2. Send a Telegram Business image-as-document; confirm it routes as image media.
3. Send a Telegram Business voice message in draft/auto; confirm Business history has `media_received` and `voice_transcribed`, and the agent sees the transcript.
4. Send a Telegram Business voice message in watch/new-chat mode; confirm owner notification is prompt and history later receives voice media + transcript.
