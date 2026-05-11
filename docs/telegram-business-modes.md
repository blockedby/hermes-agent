# Telegram Business per-chat modes

Hermes treats Telegram Business chats as opt-in per customer. Unknown Business
customer chats are gated before the agent runs, so they do not generate drafts
or send replies until the owner chooses a mode.

## Modes

- `Ignore` / `ignored`: silently ignore messages from this Business customer.
- `Watch` / `watch`: notify the owner with a safe inline card; do not run the
  agent, do not generate a draft, and do not send to the customer.
- `Draft` / `draft`: run the normal agent path. Replies are still routed to the
  owner approval card and are only sent after the owner clicks **Send**.
- `Auto` / `auto`: explicit opt-in direct Business replies. Hermes only sends
  when Telegram reports that the Business connection can reply.

Defaults:

- Human-looking unknown chats default to `watch` and get an owner mode card.
- Bot-looking chats default to `ignored`.
- Override defaults with `telegram.business_default_mode`,
  `telegram.business_bot_default_mode`, or env vars
  `TELEGRAM_BUSINESS_DEFAULT_MODE`, `TELEGRAM_BUSINESS_BOT_DEFAULT_MODE`.

## Owner UX

- New human Business chats send a card to the configured owner/home chat with
  buttons: **Ignore**, **Watch**, **Draft**, **Auto**.
- `/business` opens the owner control panel listing known Business chats by
  mode, with inline mode-switch buttons. Raw chat IDs are not part of the main
  UX; callback data uses opaque tokens.
- Mode callbacks require owner authorization.

## Watch mode and rules

Watch mode sends owner notifications with buttons for safe follow-up actions:

- **Draft once** arms the next customer message to go through the `draft` path.
- **Set Draft** changes the chat mode to `draft`.
- **Ignore** changes the chat mode to `ignored`.
- **Add rule** asks for the next owner message and stores it as a notify-only
  rule for this chat. Send any slash command instead to cancel.

The registry supports notify-only rules stored on each chat. Rule matching is
bounded and deterministic; a match only changes the owner notification text. It
never executes tools, never performs auto-actions, and never sends to the
customer.

## Storage and privacy

The registry is stored at:

`~/.hermes/gateway/platforms/telegram/business_chats.json`

The file and parent directory are written with private permissions. Entries are
keyed by Business connection + customer chat + optional direct-message topic;
display names are metadata only and are not used for routing. The registry keeps
short message previews for owner cards and watch notifications.
