"""
06 - Adaptive thinking + the `effort` parameter
===============================================

Two cost knobs that the API exposes for newer models:

- `thinking={"type": "adaptive"}` (Opus 4.6/4.7, Sonnet 4.6):
    The model decides whether to think and how much, instead of you
    setting a fixed `budget_tokens`. Often cheaper than always-on
    extended thinking and matches quality on hard prompts.

- `effort` ("low" | "medium" | "high" | "max"):
    Modulates how many tool calls and how much output the model produces.
    Use "low" for chat-like Q&A; "medium" is a good default; "high" is
    the implicit default; "max" is for "money is no object" tasks.

This script asks one easy and one hard question, with three effort
settings each, and prints the usage so you can see the difference.

Run:
    python 06_adaptive_thinking.py
"""

from __future__ import annotations

import os
import sys

import anthropic

MODEL = "claude-sonnet-4-6"


PROMPTS = {
    "easy": "What is the capital of Portugal? One word.",
    "hard": (
        "A bag holds 6 red and 4 blue balls. You draw 3 without replacement. "
        "What is the probability that exactly 2 of them are red? "
        "Show your reasoning step by step."
    ),
}


def run(client: anthropic.Anthropic, question: str, effort: str) -> None:
    kwargs = {
        "model": MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": question}],
        "stop_sequences": ["</answer>"],   # cap output if we ever generate the tag
    }

    # `effort` only on supported models / API versions; if the SDK rejects
    # it, drop the kwarg. Same for `thinking`.
    try:
        resp = client.messages.create(
            **kwargs,
            thinking={"type": "adaptive"},
            extra_body={"effort": effort},   # passes through unrecognised kwargs
        )
    except anthropic.BadRequestError:
        # fall back without these knobs (older accounts / older SDKs)
        resp = client.messages.create(**kwargs)

    u = resp.usage
    out = next(
        (b.text for b in resp.content if getattr(b, "type", None) == "text"),
        "(no text)",
    )
    print(
        f"  effort={effort:<6} "
        f"input={u.input_tokens:<5} output={u.output_tokens:<5}"
        f"  text='{out[:80]}...'"
    )


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY", file=sys.stderr)
        return 1
    client = anthropic.Anthropic(api_key=api_key)

    for difficulty, question in PROMPTS.items():
        print(f"\n=== {difficulty.upper()} ===")
        print(f"Q: {question}")
        for effort in ("low", "medium", "high"):
            run(client, question, effort)

    print(
        "\nNote: with adaptive thinking, the easy question should produce "
        "few or no thinking tokens. The hard question will use them.\n"
        "Lowering effort reduces output (and thinking) tokens further.\n"
        "Tip: stop_sequences also caps output tokens cheaply."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
