---
name: codex-bark-notifier
description: Configure and test Codex completion notifications through the Bark iOS app. Use when the user asks to send Codex completion messages to Bark, update the Bark key/server, or test the Codex Bark notifier plugin.
---

# Codex Bark Notifier

This plugin provides local scripts for Codex's `notify` config entry.

## Configure

Ask the user for the Bark test URL copied from the iOS app, then run:

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
```

For a self-hosted Bark server, either pass the full URL:

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --bark-url 'https://bark.example.com/DEVICE_KEY'
```

or pass server and device key separately:

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --server 'https://bark.example.com' --device-key 'DEVICE_KEY'
```

The installer preserves any existing `notify` command by chaining it after Bark with `--next`.

## Test

Send a manual completion event:

```bash
printf '{"type":"agent-turn-complete","last-assistant-message":"Codex Bark test complete."}' | \
python3 ~/plugins/codex-bark-notifier/scripts/codex-bark-notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
```

Check failures in:

```bash
~/.codex/bark-notifier.log
```

## DeepSeek Summary

Create or edit:

```bash
~/.codex/bark-notifier.env
```

Expected contents:

```bash
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
CODEX_BARK_SUMMARY_PROVIDER=deepseek
CODEX_BARK_TITLE=Codex 已完成
```

When `DEEPSEEK_API_KEY` is filled, the notifier sends Codex's final response to DeepSeek and uses a
single Chinese sentence as the Bark body. If DeepSeek fails, it logs the error and sends the local
fallback body instead.

## Notes

- The script accepts Codex notify JSON from stdin, argv, or `CODEX_NOTIFY_EVENT`.
- Bark failures are logged but do not fail the Codex turn unless `CODEX_BARK_STRICT=1`.
- Optional environment/config values include `BARK_SOUND`, `BARK_LEVEL`, `BARK_GROUP`, `BARK_ICON`, and `BARK_OPEN_URL`.
