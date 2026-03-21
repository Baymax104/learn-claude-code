# -*- coding: UTF-8 -*-
from pathlib import Path

from rich import print
from tools import CHILD_TOOLS, TOOL_HANDLERS
from utils import ask_llm

WORKDIR = Path(__file__).parent
SUBAGENT_SYSTEM = f"You are a coding subagent at {WORKDIR}. Complete the given task, then summarize your findings."


# -- Subagent: fresh context, filtered tools, summary-only return --
def run_subagent(prompt: str) -> str:
    sub_messages = [{"role": "user", "content": prompt}]  # fresh context
    summary = ""
    for _ in range(30):  # safety limit
        response = ask_llm(
            system=SUBAGENT_SYSTEM,
            messages=sub_messages,
            tools=CHILD_TOOLS
        )
        sub_messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            summary = "".join(b.text for b in response.content if hasattr(b, "text"))
            break
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[yellow]Child > {block.name}: {block.input}")
                handler = TOOL_HANDLERS.get(block.name)
                output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                print(f"[green]Child > {block.name}: {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)[:50000]})
        sub_messages.append({"role": "user", "content": results})
    # Only the final text returns to the parent -- child context is discarded
    return summary if summary else "(no summary)"
