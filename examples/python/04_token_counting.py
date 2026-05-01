"""
04 - Token counting before you spend
====================================

`messages.count_tokens` returns the input-token count the model would see
for a given request. It's free, has its own rate limit, and supports
`system`, `tools`, images, PDFs, and thinking. Use it to:

- Decide if a request fits the context window before sending it.
- Estimate cost (combine with prices from 07_cost_calculator).
- Monitor prompt sizes in tests / CI.

Run:
    python 04_token_counting.py
"""

from __future__ import annotations

import os
import sys

import anthropic

MODEL = "claude-sonnet-4-6"


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    # Case 1: simple message
    r = client.messages.count_tokens(
        model=MODEL,
        messages=[{"role": "user", "content": "Hello, world!"}],
    )
    print(f"Simple 'Hello, world!' message    -> {r.input_tokens} tokens")

    # Case 2: with a system prompt
    r = client.messages.count_tokens(
        model=MODEL,
        system="You are a senior code reviewer. Be terse.",
        messages=[{"role": "user", "content": "Review this PR (assume it's small)."}],
    )
    print(f"With short system prompt          -> {r.input_tokens} tokens")

    # Case 3: with tools
    r = client.messages.count_tokens(
        model=MODEL,
        system="You answer with tool calls when appropriate.",
        tools=[
            {
                "name": "get_weather",
                "description": "Get the current weather for a city.",
                "input_schema": {
                    "type": "object",
                    "properties": {"city": {"type": "string"}},
                    "required": ["city"],
                },
            }
        ],
        messages=[{"role": "user", "content": "What's it like in London right now?"}],
    )
    print(f"With one tool definition          -> {r.input_tokens} tokens")

    # Case 4: a long prompt - check it before sending
    long_text = "Repeat after me: tokens cost money. " * 200
    r = client.messages.count_tokens(
        model=MODEL,
        messages=[{"role": "user", "content": long_text}],
    )
    print(f"Long padded prompt                -> {r.input_tokens} tokens")

    print(
        "\ncount_tokens is free of charge for tokens but is rate-limited.\n"
        "Use it before any expensive call - especially before sending a long\n"
        "RAG context, a PDF, or many images."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
