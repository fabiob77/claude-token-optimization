"""
01 - Basic prompt caching with cost comparison
=============================================

The simplest form of prompt caching: a long, stable system prompt marked
with `cache_control`. The first call writes to the cache; subsequent
calls within the TTL hit it at 10% of base input cost.

Run twice within 5 minutes to see the cache_read on the second run:

    python 01_basic_caching.py

Reads ANTHROPIC_API_KEY from the environment. See .env.example.
"""

from __future__ import annotations

import os
import sys

import anthropic

MODEL = "claude-sonnet-4-6"

# Sonnet 4.6 prices, USD per 1M tokens (April 2026)
PRICE_INPUT = 3.00
PRICE_OUTPUT = 15.00
PRICE_CACHE_WRITE_5M = 3.75       # 1.25x
PRICE_CACHE_READ = 0.30           # 0.10x


# A long, stable system prompt. Must be >=1,024 tokens to be cacheable.
# We pad with a realistic style guide repeated to make the point.
STYLE_GUIDE = """\
You are an expert legal-writing assistant for a UK SME.

Conventions:
- Always use British English (e.g. "organisation", "colour").
- Use plain language and short sentences.
- For contracts, identify and label these clauses:
  Indemnity, Limitation of Liability, Termination, Confidentiality,
  Intellectual Property, Governing Law, Force Majeure, Assignment,
  Entire Agreement, Notices, Severability, Waiver, Dispute Resolution.
- Highlight risks in plain language, not legalese.
- Cite the clause number when referencing it.
- If a clause is missing from a category that ought to have one, say so.

Risk scoring:
- LOW: standard market terms, no unusual exposure.
- MEDIUM: terms favour the counterparty but are negotiable.
- HIGH: unusual obligations, broad indemnities, no caps on liability,
  unilateral termination rights, IP assignment without payment.

Output format:
1. Executive summary (2-3 bullets).
2. Clause-by-clause analysis with risk score and recommended edit.
3. Top 3 negotiation priorities.
""" * 6  # repeat to comfortably clear the 1,024-token minimum


def cost_breakdown(usage) -> dict:
    """Compute cost in USD from a Usage object."""
    return {
        "fresh_input_tokens": usage.input_tokens,
        "cache_creation_tokens": usage.cache_creation_input_tokens or 0,
        "cache_read_tokens": usage.cache_read_input_tokens or 0,
        "output_tokens": usage.output_tokens,
        "cost_usd": round(
            usage.input_tokens             * PRICE_INPUT          / 1_000_000
            + (usage.cache_creation_input_tokens or 0) * PRICE_CACHE_WRITE_5M / 1_000_000
            + (usage.cache_read_input_tokens or 0)     * PRICE_CACHE_READ     / 1_000_000
            + usage.output_tokens          * PRICE_OUTPUT         / 1_000_000,
            6,
        ),
    }


def ask(client: anthropic.Anthropic, question: str) -> None:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=[
            {
                "type": "text",
                "text": STYLE_GUIDE,
                "cache_control": {"type": "ephemeral"},   # 5-min TTL by default
            }
        ],
        messages=[{"role": "user", "content": question}],
    )
    print(f"\nQ: {question}")
    print(f"A: {resp.content[0].text[:300]}...")
    print(f"   {cost_breakdown(resp.usage)}")


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY in your environment.", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    print("=== First call: should write to cache ===")
    ask(client, "Summarise the indemnification clause in a typical SaaS NDA.")

    print("\n=== Second call: should HIT the cache (cache_read > 0) ===")
    ask(client, "What are the most common termination triggers in SaaS contracts?")

    print(
        "\nIf cache_read_tokens is 0 on the second call, your STYLE_GUIDE "
        "probably fell below the 1,024-token minimum or you waited >5 min."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
