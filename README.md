# Codex Bark Notifier

Local Codex plugin that forwards Codex completion notifications to Bark on iOS.

## Install

Copy the test URL from Bark on iOS, then run:

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
codex plugin add codex-bark-notifier@personal
```

Restart Codex or start a new session after installing.

The installer backs up `~/.codex/config.toml` and preserves any existing `notify` command by chaining it after the Bark notification.

## Test

```bash
printf '{"type":"agent-turn-complete","last-assistant-message":"Codex Bark test complete."}' | \
python3 ~/plugins/codex-bark-notifier/scripts/codex-bark-notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
```

Logs are written to `~/.codex/bark-notifier.log`.

## One-Sentence Chinese Summaries

Fill in the API key file:

```bash
~/.codex/bark-notifier.env
```

Required value:

```bash
DEEPSEEK_API_KEY=your_api_key_here
```

By default, completion notifications use the Chinese title `Codex 已完成` and ask DeepSeek to
compress Codex's final response into one Chinese sentence. If the API key is empty or the API call
fails, the notifier falls back to a local short body and logs the failure.
