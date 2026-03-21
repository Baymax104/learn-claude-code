#!/usr/bin/env python3
# Harness: tool dispatch -- expanding what the model can reach.
"""
s02_tool_use.py - Tools

The agent loop from s01 didn't change. We just added tools to the array
and a dispatch map to route calls.

    +----------+      +-------+      +------------------+
    |   User   | ---> |  LLM  | ---> | Tool Dispatch    |
    |  prompt  |      |       |      | {                |
    +----------+      +---+---+      |   bash: run_bash |
                          ^          |   read: run_read |
                          |          |   write: run_wr  |
                          +----------+   edit: run_edit |
                          tool_result| }                |
                                     +------------------+

Key insight: "The loop didn't change at all. I just added tools."
改动：将read、write、edit三个功能分离为三个独立的工具，同时实现路径安全
"""

from pathlib import Path

from rich import print
from tools import TOOL_HANDLERS, TOOLS
from utils import ask_llm

WORKDIR = Path(__file__).parent

SYSTEM = f"You are a coding agent at {WORKDIR}. Use tools to solve tasks. Act, don't explain."


def agent_loop(messages: list):
    while True:
        response = ask_llm(
            system=SYSTEM,
            messages=messages,
            tools=TOOLS,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return
        results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = TOOL_HANDLERS.get(block.name)
                print(f"[yellow]> {block.name}: {block.input}")
                output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                print(f"[green]> {block.name}: {output[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms02 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()
