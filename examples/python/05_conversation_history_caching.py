"""
05 - Conversation history caching (rolling cache point)
=======================================================

Long conversations get expensive because every turn re-sends the entire
history as input. The trick: mark the LAST user message as cacheable.
That turns everything before it into a cached prefix on the next turn.

Pattern:
- System prompt cached with 1-hour TTL (stable across turns).
- Each new user turn marked with 5-minute cache_control. The previous
  turn's mark stops counting; on the next turn, the previous user
  message is now part of the cached prefix.

This keeps you within the 4-breakpoint per-request limit while letting
the conversation grow indefinitely with mostly-cached input.

Run:
    python 05_conversation_history_caching.py
"""

from __future__ import annotations

import os
import sys

import anthropic

MODEL = "claude-sonnet-4-6"


SYSTEM_PROMPT = """\
You are a friendly tutor for a UK GCSE student.
- Use British English.
- Explain in short, simple sentences first; offer to go deeper.
- Refuse to do the student's homework verbatim - guide them instead.
- Use UK examples (pounds sterling, English/Welsh history, etc.).
- After each answer, ask one short check-for-understanding question.
""" * 4


def make_message(role: str, text: str, cache: bool) -> dict:
    """Build a message dict, optionally with a 5-min cache breakpoint."""
    block: dict = {"type": "text", "text": text}
    if cache:
        block["cache_control"] = {"type": "ephemeral"}
    return {"role": role, "content": [block]}


def chat_turn(client: anthropic.Anthropic, history: list, user_text: str) -> tuple[str, list]:
    """Send a turn and return (assistant_reply, new_history)."""
    # Strip cache_control off any prior message (only the most recent user
    # message should carry the rolling breakpoint).
    cleaned = []
    for m in history:
        new_m = {"role": m["role"]}
        if isinstance(m["content"], list):
            new_m["content"] = [
                {k: v for k, v in block.items() if k != "cache_control"}
                for block in m["content"]
            ]
        else:
            new_m["content"] = m["content"]
        cleaned.append(new_m)

    cleaned.append(make_message("user", user_text, cache=True))

    resp = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }
        ],
        messages=cleaned,
    )

    reply = resp.content[0].text
    u = resp.usage
    print(
        f"  [usage] fresh={u.input_tokens} "
        f"cache_create={u.cache_creation_input_tokens or 0} "
        f"cache_read={u.cache_read_input_tokens or 0} "
        f"output={u.output_tokens}"
    )

    cleaned.append({"role": "assistant", "content": reply})
    return reply, cleaned


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY", file=sys.stderr)
        return 1
    client = anthropic.Anthropic(api_key=api_key)

    questions = [
        "Why did the Industrial Revolution start in Britain and not France?",
        "Which invention had the biggest impact?",
        "How did this change daily life for ordinary workers?",
        "Was anyone better off because of it?",
    ]

    history: list = []
    for q in questions:
        print(f"\nUser: {q}")
        reply, history = chat_turn(client, history, q)
        print(f"Tutor: {reply[:250]}...")

    print(
        "\nNotice how cache_read grows each turn while fresh input "
        "stays small: that's the rolling cache point earning its keep."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
