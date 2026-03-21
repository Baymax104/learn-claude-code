# -*- coding: UTF-8 -*-
from __future__ import annotations

import subprocess
from pathlib import Path

TOOLS = [
    {
        "name": "bash",
        "description": "Run a shell command.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    }
]

root = Path(__file__).parent


def run_bash(command: str) -> str:
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
        )
        out = (r.stdout if r.stdout else "" + r.stderr if r.stderr else "").strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
