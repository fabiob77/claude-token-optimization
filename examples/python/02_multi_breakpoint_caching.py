"""
02 - Multi-breakpoint caching for agents
========================================

Real production agents usually have several stable layers:
    tools           (large schemas, rarely change)
    system          (instructions, sometimes versioned)
    long doc / RAG  (per-session, reused across many turns)
    user input      (always fresh)

The Claude API allows up to 4 cache breakpoints per request, evaluated
in order: tools -> system -> messages. This example shows how to mark
each layer so they cache independently and don't invalidate each other.

Run:
    python 02_multi_breakpoint_caching.py
"""

from __future__ import annotations

import os
import sys

import anthropic

MODEL = "claude-sonnet-4-6"


# --- Layer 1: tool definitions (cacheable, change rarely) -------------------
TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": (
            "Searches the internal knowledge base for documents matching the query. "
            "Returns up to 10 documents with title, snippet, and URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "top_k": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_document",
        "description": "Fetches the full text of a document by its URL.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "format": "uri"}},
            "required": ["url"],
        },
    },
    # Pad with realistic extra tool defs so we cross the 1,024-token min.
    {
        "name": "create_ticket",
        "description": (
            "Creates a support ticket with the given title, description, priority, "
            "and assignee. Returns the ticket ID and URL."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "assignee_email": {"type": "string", "format": "email"},
                "labels": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "description", "priority"],
        },
    },
] * 3  # repeat to comfortably exceed the 1,024-token cache minimum


# --- Layer 2: system prompt (cacheable, versioned weekly) -------------------
SYSTEM_PROMPT = """\
You are a senior support agent for Acme SaaS.

You answer in three steps:
1. Identify the user's underlying problem (don't take the literal request).
2. Use search_knowledge_base before claiming any factual answer.
3. If the resolution requires a human, create_ticket and return the URL.

Tone: warm, concise, no hedging. Cite sources by URL when you use the KB.
Never invent product features. If unsure, say so and create a ticket.
""" * 4   # padded for cache minimum


# --- Layer 3: a "session document" (cacheable per session) ------------------
# Imagine a per-user RAG result, an account dossier, or a contract excerpt.
SESSION_DOCUMENT = """\
Customer dossier:
- Account: Acme Co, plan: Team Premium, MRR: GBP 1,250
- Open tickets (3): #4421 'SSO failures Tuesday', #4503 'API 429s', #4510 'Billing'
- CSAT trend: 4.6 -> 4.2 (last 90 days)
- Last QBR: action 'enable Okta SCIM by Q2'.
Notes:
- Champion: Maria Diaz (eng manager). DM responsive.
- Blocker on SCIM: depends on shared idP migration we have not scheduled.
""" * 8


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    user_question = "Why is the Acme Co SSO still failing on Tuesdays?"

    # Three breakpoints: end-of-tools, end-of-system, end-of-session-doc.
    # The 4th breakpoint slot is left free for future conversation growth.
    tools_with_cache = list(TOOLS)
    tools_with_cache[-1] = {
        **tools_with_cache[-1],
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }

    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        tools=tools_with_cache,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": SESSION_DOCUMENT,
                        "cache_control": {"type": "ephemeral"},  # 5 min - per session
                    },
                    {"type": "text", "text": user_question},     # uncached, dynamic
                ],
            }
        ],
    )

    u = resp.usage
    print("Model output (truncated):")
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            print(" ", block.text[:300], "...")

    print("\nUsage breakdown:")
    print(f"  fresh input tokens   = {u.input_tokens}")
    print(f"  cache_creation tokens = {u.cache_creation_input_tokens or 0}")
    print(f"  cache_read tokens     = {u.cache_read_input_tokens or 0}")
    print(f"  output tokens         = {u.output_tokens}")
    print(
        "\nFirst run: cache_creation_tokens will be large.\n"
        "Run again within 5 minutes (1 hour for the tools/system) to see "
        "cache_read tokens dominate and fresh input drop to just the question."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
