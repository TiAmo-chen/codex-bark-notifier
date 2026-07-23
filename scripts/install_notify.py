#!/usr/bin/env python3
"""Install the Codex Bark notify wrapper into ~/.codex/config.toml."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import tomllib
from pathlib import Path


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in values) + "]"


def find_notify_span(text: str) -> tuple[int, int] | None:
    lines = text.splitlines(keepends=True)
    offset = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            return None
        if stripped.startswith("notify") and "=" in stripped:
            depth = 0
            end_offset = offset
            for inner in lines[index:]:
                end_offset += len(inner)
                depth += inner.count("[") - inner.count("]")
                if depth <= 0:
                    return offset, end_offset
        offset += len(line)
    return None


def load_existing_notify(config_path: Path) -> list[str]:
    if not config_path.exists():
        return []
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    notify = data.get("notify", [])
    if isinstance(notify, list) and all(isinstance(item, str) for item in notify):
        return notify
    return []


def install(config_path: Path, script_path: Path, bark_args: list[str]) -> Path:
    existing = load_existing_notify(config_path)
    wrapper_prefix = [sys.executable, str(script_path)]

    if existing[:2] == wrapper_prefix:
        next_index = existing.index("--next") if "--next" in existing else len(existing)
        next_cmd = existing[next_index + 1 :] if next_index < len(existing) else []
    else:
        next_cmd = existing

    new_notify = wrapper_prefix + bark_args
    if next_cmd:
        new_notify += ["--next", *next_cmd]

    config_path.parent.mkdir(parents=True, exist_ok=True)
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    backup = config_path.with_suffix(config_path.suffix + f".bark-backup-{time.strftime('%Y%m%d%H%M%S')}")
    if config_path.exists():
        shutil.copy2(config_path, backup)

    replacement = f"notify = {toml_array(new_notify)}\n"
    span = find_notify_span(original)
    if span:
        start, end = span
        updated = original[:start] + replacement + original[end:]
    else:
        updated = replacement + ("\n" if original and not original.startswith("\n") else "") + original
    config_path.write_text(updated, encoding="utf-8")
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Configure Codex to push completion notifications to Bark.")
    parser.add_argument("--bark-url", help="Full Bark push URL, for example https://api.day.app/your_key")
    parser.add_argument("--device-key", help="Bark device key. Uses https://api.day.app/push by default.")
    parser.add_argument("--server", default="", help="Custom Bark server, for example https://bark.example.com")
    parser.add_argument("--sound", default="")
    parser.add_argument("--level", default="")
    parser.add_argument("--group", default="")
    parser.add_argument("--config", default=str(Path("~/.codex/config.toml").expanduser()))
    parser.add_argument("--script", default=str(Path(__file__).with_name("codex-bark-notify.py")))
    args = parser.parse_args()

    if not args.bark_url and not args.device_key:
        parser.error("pass --bark-url copied from Bark, or pass --device-key")

    bark_args: list[str] = []
    for flag in ("bark_url", "device_key", "server", "sound", "level", "group"):
        value = getattr(args, flag)
        if value:
            bark_args.extend([f"--{flag.replace('_', '-')}", value])

    backup = install(Path(args.config).expanduser(), Path(args.script).expanduser(), bark_args)
    print(f"Updated {Path(args.config).expanduser()}")
    if backup.exists():
        print(f"Backup: {backup}")
    print("Restart Codex, or start a new Codex session, for the notify setting to take effect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
