#!/usr/bin/env python3
"""Forward Codex notify events to Bark, then optionally chain another notifier."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


COMPLETE_EVENTS = {
    "agent-turn-complete",
    "agent_turn_complete",
    "turn-complete",
    "turn_complete",
    "turn-ended",
    "turn_ended",
}


def env_file_from_argv(argv: list[str]) -> str:
    for index, item in enumerate(argv):
        if item == "--env-file" and index + 1 < len(argv):
            return argv[index + 1]
        if item.startswith("--env-file="):
            return item.split("=", 1)[1]
    return os.environ.get("CODEX_BARK_ENV", "~/.codex/bark-notifier.env")


def load_env_file(path: str) -> None:
    env_path = Path(path).expanduser()
    if not env_path.is_file():
        return
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        log(f"env file read failed: {exc}")
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


def log(message: str) -> None:
    log_path = Path(os.environ.get("CODEX_BARK_LOG", "~/.codex/bark-notifier.log")).expanduser()
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except OSError:
        pass


def split_event_arg(argv: list[str]) -> tuple[list[str], str]:
    if argv and argv[-1].lstrip().startswith("{"):
        return argv[:-1], argv[-1]
    return argv, ""


def parse_args(argv: list[str]) -> tuple[argparse.Namespace, str]:
    load_env_file(env_file_from_argv(argv))
    argv, event_arg = split_event_arg(argv)
    parser = argparse.ArgumentParser(description="Send Codex completion events to Bark.")
    parser.add_argument("--env-file", default=os.environ.get("CODEX_BARK_ENV", "~/.codex/bark-notifier.env"))
    parser.add_argument("--bark-url", default=os.environ.get("BARK_URL", ""))
    parser.add_argument("--device-key", default=os.environ.get("BARK_DEVICE_KEY", os.environ.get("BARK_KEY", "")))
    parser.add_argument("--server", default=os.environ.get("BARK_SERVER", "https://api.day.app"))
    parser.add_argument("--group", default=os.environ.get("BARK_GROUP", "Codex"))
    parser.add_argument("--sound", default=os.environ.get("BARK_SOUND", ""))
    parser.add_argument("--level", default=os.environ.get("BARK_LEVEL", "active"))
    parser.add_argument("--icon", default=os.environ.get("BARK_ICON", ""))
    parser.add_argument("--url", default=os.environ.get("BARK_OPEN_URL", ""))
    parser.add_argument("--title", default=os.environ.get("CODEX_BARK_TITLE", "Codex 已完成"))
    parser.add_argument("--max-body", type=int, default=int(os.environ.get("CODEX_BARK_MAX_BODY", "120")))
    parser.add_argument("--summary-provider", default=os.environ.get("CODEX_BARK_SUMMARY_PROVIDER", "deepseek"))
    parser.add_argument("--summary-model", default=os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash"))
    parser.add_argument("--summary-base-url", default=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    parser.add_argument("--summary-timeout", type=float, default=float(os.environ.get("DEEPSEEK_TIMEOUT", "30")))
    parser.add_argument("--summary-max-input", type=int, default=int(os.environ.get("CODEX_BARK_SUMMARY_MAX_INPUT", "6000")))
    parser.add_argument("--summary-max-tokens", type=int, default=int(os.environ.get("DEEPSEEK_MAX_TOKENS", "4096")))
    parser.add_argument("--next", nargs=argparse.REMAINDER, default=[])
    return parser.parse_args(argv), event_arg


def load_event(event_arg: str) -> tuple[dict[str, Any], str]:
    candidates = [
        event_arg,
        os.environ.get("CODEX_NOTIFY_EVENT", ""),
        os.environ.get("CODEX_EVENT_JSON", ""),
    ]
    if not event_arg:
        try:
            if not sys.stdin.isatty():
                candidates.insert(0, sys.stdin.read())
        except OSError:
            pass

    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data, candidate
        except json.JSONDecodeError:
            continue
    return {}, event_arg


def first_text(event: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def event_type(event: dict[str, Any]) -> str:
    for key in ("type", "event", "name", "kind"):
        value = event.get(key)
        if isinstance(value, str):
            return value
    return ""


def build_body(event: dict[str, Any], max_body: int) -> str:
    body = first_text(
        event,
        [
            "last-assistant-message",
            "last_assistant_message",
            "assistant_message",
            "message",
            "summary",
            "body",
        ],
    )
    if not body:
        cwd = first_text(event, ["cwd", "working_directory", "workdir"])
        body = f"Codex completed a turn{f' in {cwd}' if cwd else ''}."

    body = " ".join(body.split())
    if max_body > 0 and len(body) > max_body:
        body = body[: max_body - 1].rstrip() + "..."
    return body


def completion_text(event: dict[str, Any]) -> str:
    return first_text(
        event,
        [
            "last-assistant-message",
            "last_assistant_message",
            "assistant_message",
            "message",
            "summary",
            "body",
        ],
    )


def deepseek_endpoint(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return f"{base}/chat/completions"
    return f"{base}/v1/chat/completions"


def summarize_with_deepseek(args: argparse.Namespace, text: str) -> str:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is empty")

    text = text.strip()
    if args.summary_max_input > 0 and len(text) > args.summary_max_input:
        text = text[: args.summary_max_input].rstrip()

    payload = {
        "model": args.summary_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个通知摘要器。请用中文把 Codex 刚完成的工作压缩成一句话，"
                    "只输出摘要本身，不要寒暄，不要编号，不要 Markdown，30 个汉字左右。"
                ),
            },
            {
                "role": "user",
                "content": f"Codex 最终回复全文如下：\n{text}",
            },
        ],
        "temperature": 0.2,
        "max_tokens": args.summary_max_tokens,
    }
    request = urllib.request.Request(
        deepseek_endpoint(args.summary_base_url),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=args.summary_timeout) as response:
        result = json.loads(response.read().decode("utf-8"))

    choices = result.get("choices", [])
    if not choices:
        raise ValueError("DeepSeek response has no choices")
    message = choices[0].get("message", {})
    summary = message.get("content", "") if isinstance(message, dict) else ""
    summary = " ".join(summary.strip().strip("。.!！").split())
    if not summary:
        raise ValueError("DeepSeek summary is empty")
    return summary


def build_notification_body(args: argparse.Namespace, event: dict[str, Any]) -> str:
    text = completion_text(event)
    if args.summary_provider.lower() == "deepseek" and text.strip():
        try:
            return summarize_with_deepseek(args, text)
        except Exception as exc:  # noqa: BLE001 - notification fallback should be resilient.
            log(f"deepseek summary failed: {exc}")
    return build_body(event, args.max_body)


def bark_endpoint(args: argparse.Namespace) -> tuple[str, dict[str, Any]]:
    payload: dict[str, Any] = {
        "title": args.title,
        "group": args.group,
        "level": args.level,
    }
    for key in ("sound", "icon", "url"):
        value = getattr(args, key)
        if value:
            payload[key] = value

    if args.bark_url:
        return args.bark_url.rstrip("/"), payload

    if not args.device_key:
        raise ValueError("missing Bark URL or device key")

    server = args.server.rstrip("/")
    payload["device_key"] = args.device_key
    return f"{server}/push", payload


def send_bark(args: argparse.Namespace, body: str) -> None:
    endpoint, payload = bark_endpoint(args)
    payload["body"] = body
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    timeout = float(os.environ.get("CODEX_BARK_TIMEOUT", "8"))
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.read()


def run_next(next_cmd: list[str], event_json: str) -> int:
    if not next_cmd:
        return 0
    try:
        env = dict(os.environ)
        if event_json:
            env["CODEX_NOTIFY_EVENT"] = event_json
        completed = subprocess.run(
            next_cmd,
            input=event_json.encode("utf-8") if event_json else None,
            env=env,
            timeout=float(os.environ.get("CODEX_BARK_FORWARD_TIMEOUT", "10")),
            check=False,
        )
        return completed.returncode
    except Exception as exc:  # noqa: BLE001 - notification hooks should never crash Codex.
        log(f"next notifier failed: {exc}")
        return 1


def main() -> int:
    args, event_arg = parse_args(sys.argv[1:])
    event, event_json = load_event(event_arg)
    kind = event_type(event)
    should_send = not kind or kind in COMPLETE_EVENTS or os.environ.get("CODEX_BARK_ALWAYS_SEND") == "1"

    if should_send:
        try:
            send_bark(args, build_notification_body(args, event))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            log(f"bark send failed: {exc}")
            if os.environ.get("CODEX_BARK_STRICT") == "1":
                return 1

    next_code = run_next(args.next, event_json)
    if next_code:
        log(f"next notifier exited with {next_code}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
