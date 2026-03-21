#!/usr/bin/env python3
# Harness: on-demand knowledge -- domain expertise, loaded when the model asks.
"""
s05_skill_loading.py - Skills

Two-layer skill injection that avoids bloating the system prompt:

    Layer 1 (cheap): skill names in system prompt (~100 tokens/skill)
    Layer 2 (on demand): full skill body in tool_result

    skills/
      pdf/
        SKILL.md          <-- frontmatter (name, description) + body
      code-review/
        SKILL.md

    System prompt:
    +--------------------------------------+
    | You are a coding agent.              |
    | Skills available:                    |
    |   - pdf: Process PDF files...        |  <-- Layer 1: metadata only
    |   - code-review: Review code...      |
    +--------------------------------------+

    When model calls load_skill("pdf"):
    +--------------------------------------+
    | tool_result:                         |
    | <skill>                              |
    |   Full PDF processing instructions   |  <-- Layer 2: full body
    |   Step 1: ...                        |
    |   Step 2: ...                        |
    | </skill>                             |
    +--------------------------------------+

Key insight: "Don't put everything in the system prompt. Load on demand."
改动：为其他的复杂工具编写一个使用说明文档，称为Skill，每个文档包含简要概述和详细说明，将所有Skill的简要概述放在System Prompt中，
同时添加load_skill工具，agent通过该工具获取Skill的详细说明，agent可通过bash和编写代码文件实现Skill
"""

from pathlib import Path

from rich import print
from skill_loader import SKILL_LOADER
from tools import TOOL_HANDLERS, TOOLS
from utils import ask_llm

WORKDIR = Path(__file__).parent

# Layer 1: skill metadata injected into system prompt
SYSTEM = f"""
You are a coding agent at {WORKDIR}.
Use load_skill to access specialized knowledge before tackling unfamiliar topics.

Skills available:
{SKILL_LOADER.get_descriptions()}
"""


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
                try:
                    print(f"[yellow]> {block.name}: {block.input}")
                    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                except Exception as e:
                    output = f"Error: {e}"
                print(f"[green]> {block.name}: {str(output)[:200]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
        messages.append({"role": "user", "content": results})


if __name__ == "__main__":
    history = []
    while True:
        try:
            query = input("\033[36ms05 >> \033[0m")
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
