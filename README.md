# Codex Bark Notifier

## 中文说明

Codex Bark Notifier 是一个本地 Codex 插件，用来在 Codex 完成一次任务或回复后，把完成通知推送到 iOS 上的 Bark。

它做了几件事：

- 通过 Codex 的 `notify` 配置监听完成事件。
- 将完成通知推送到 Bark。
- 支持自定义通知标题、图标、分组、铃声和打开链接。
- 可选调用 DeepSeek API，把 Codex 的最终回复全文压缩成一句中文摘要，作为 Bark 通知正文。
- 如果 DeepSeek 或 Bark 临时失败，会写入日志，并尽量不影响 Codex 自身运行。
- 安装时会保留你原来的 `notify` 命令，并通过 `--next` 继续转发。

## 安装

先从 Bark iOS app 里复制测试推送链接，然后运行：

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
codex plugin add codex-bark-notifier@personal
```

如果你使用自建 Bark 服务，可以传完整 URL：

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --bark-url 'https://bark.example.com/DEVICE_KEY'
```

也可以把服务地址和 device key 分开传：

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --server 'https://bark.example.com' --device-key 'DEVICE_KEY'
```

安装脚本会备份 `~/.codex/config.toml`，并更新其中的 `notify` 配置。完成后重启 Codex，或新开一个 Codex 任务，让配置生效。

## 测试

发送一条手动测试通知：

```bash
printf '{"type":"agent-turn-complete","last-assistant-message":"Codex Bark 测试完成。"}' | \
python3 ~/plugins/codex-bark-notifier/scripts/codex-bark-notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
```

查看失败日志：

```bash
~/.codex/bark-notifier.log
```

## DeepSeek 一句话中文摘要

创建或编辑环境变量文件：

```bash
~/.codex/bark-notifier.env
```

示例：

```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
CODEX_BARK_SUMMARY_PROVIDER=deepseek
CODEX_BARK_TITLE=Codex 已完成
```

填好 `DEEPSEEK_API_KEY` 后，插件会把 Codex 的最终回复全文发送给 DeepSeek，并把返回的一句中文摘要作为 Bark 正文。如果 API key 为空、模型名不正确或接口失败，插件会回退到本地短正文。

## 常用环境变量

- `BARK_URL`: 完整 Bark 推送 URL。
- `BARK_DEVICE_KEY`: Bark device key。
- `BARK_SERVER`: Bark 服务地址，默认 `https://api.day.app`。
- `BARK_GROUP`: Bark 通知分组，默认 `Codex`。
- `BARK_SOUND`: Bark 通知铃声。
- `BARK_ICON`: Bark 自定义图标 URL，iOS 15 及以上支持。
- `BARK_OPEN_URL`: 点击通知后打开的 URL。
- `CODEX_BARK_TITLE`: Bark 通知标题，默认 `Codex 已完成`。
- `CODEX_BARK_STRICT=1`: 发送失败时让脚本返回失败码。

## English

Codex Bark Notifier is a local Codex plugin that forwards Codex completion notifications to Bark on iOS.

It can:

- Listen to Codex completion events through the `notify` config entry.
- Push completion notifications to Bark.
- Customize the notification title, icon, group, sound, and open URL.
- Optionally call the DeepSeek API to compress Codex's final response into one Chinese sentence for the notification body.
- Log DeepSeek or Bark failures without interrupting Codex.
- Preserve an existing `notify` command by forwarding to it with `--next`.

## Install

Copy the test push URL from the Bark iOS app, then run:

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
codex plugin add codex-bark-notifier@personal
```

For a self-hosted Bark server, pass the full URL:

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --bark-url 'https://bark.example.com/DEVICE_KEY'
```

or pass the server and device key separately:

```bash
python3 ~/plugins/codex-bark-notifier/scripts/install_notify.py --server 'https://bark.example.com' --device-key 'DEVICE_KEY'
```

The installer backs up `~/.codex/config.toml` and updates the `notify` setting. Restart Codex or start a new task after installing.

## Test

```bash
printf '{"type":"agent-turn-complete","last-assistant-message":"Codex Bark test complete."}' | \
python3 ~/plugins/codex-bark-notifier/scripts/codex-bark-notify.py --bark-url 'https://api.day.app/DEVICE_KEY'
```

Logs are written to:

```bash
~/.codex/bark-notifier.log
```

## DeepSeek One-Sentence Summaries

Create or edit:

```bash
~/.codex/bark-notifier.env
```

Example:

```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
CODEX_BARK_SUMMARY_PROVIDER=deepseek
CODEX_BARK_TITLE=Codex 已完成
```

When `DEEPSEEK_API_KEY` is set, the notifier sends Codex's final response to DeepSeek and uses the returned one-sentence Chinese summary as the Bark body. If the API key is missing or the API call fails, it falls back to a local short body.
