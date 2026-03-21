#!/usr/bin/env python3
# Harness: context isolation -- protecting the model's clarity of thought.
"""
s04_subagent.py - Subagents

Spawn a child agent with fresh messages=[]. The child works in its own
context, sharing the filesystem, then returns only a summary to the parent.

    Parent agent                     Subagent
    +------------------+             +------------------+
    | messages=[...]   |             | messages=[]      |  <-- fresh
    |                  |  dispatch   |                  |
    | tool: task       | ---------->| while tool_use:  |
    |   prompt="..."   |            |   call tools     |
    |   description="" |            |   append results |
    |                  |  summary   |                  |
    |   result = "..." | <--------- | return last text |
    +------------------+             +------------------+
              |
    Parent context stays clean.
    Subagent context is discarded.

Key insight: "Process isolation gives context isolation for free."
改动：将子agent作为工具处理子任务，由父agent调用
"""

from pathlib import Path

from rich import print
from subagent import run_subagent
from tools import PARENT_TOOLS, TOOL_HANDLERS
from utils import ask_llm

WORKDIR = Path(__file__).parent

SYSTEM = f"You are a coding agent at {WORKDIR}. Split task and use the task tool to delegate exploration or subtasks."


def agent_loop(messages: list):
    while True:
        response = ask_llm(
            system=SYSTEM,
            messages=messages,
            tools=PARENT_TOOLS,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return
        results = []
        for block in response.content:
            if block.type == "tool_use":
                if block.name == "task":
                    desc = block.input.get("description", "subtask")
                    print(f"[yellow]> task ({desc}): {block.input['prompt']}")
                    output = run_subagent(block.input["prompt"])
                else:
                    print(f"[yellow]> {block.name}: {block.input}")
                    handler = TOOL_HANDLERS.get(block.name)
                    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                print(f"[green]> {block.name}: {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms04 >> \033[0m")
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
