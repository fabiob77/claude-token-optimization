"""
03 - Batch API end-to-end (with caching)
========================================

Demonstrates the cheapest async pattern available on Claude:
- Submit up to 10,000 requests in one batch
- 50% discount on input AND output tokens
- Use 1-hour cache TTL because batches can take >5 minutes

This script:
1. Builds a batch of 5 requests, each with a shared cached system prompt.
2. Submits them.
3. Polls until done.
4. Prints results with usage breakdown.

Run:
    python 03_batch_api.py

Note: most batches finish in under a minute, but the SLA is 24 hours.
Don't use the Batch API for anything user-facing in real time.
"""

from __future__ import annotations

import os
import sys
import time

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

MODEL = "claude-haiku-4-5"   # cheap; the discount stacks regardless of model

# Long enough to clear the 1,024-token cache minimum.
SYSTEM_PROMPT = """\
You are a content classifier. Read the input text and output a JSON object
with these fields and nothing else:
{
  "category": one of ["billing", "bug", "feature_request", "praise", "other"],
  "sentiment": one of ["positive", "neutral", "negative"],
  "urgency": integer 1-5,
  "summary": one sentence under 25 words
}

Rules:
- Always output valid JSON only - no commentary, no markdown fences.
- If the message is empty, return all fields as null.
- Choose the SINGLE best category, even if it's a stretch.
- Urgency 5 means user is blocked or business is at risk.
- Be terse in the summary; do not editorialise.
""" * 5


SAMPLE_INPUTS = [
    "I was double-charged for last month and need this refunded ASAP.",
    "Your new export feature is brilliant - saved me hours this week!",
    "Can you add CSV export to the reports page? It's the only thing missing.",
    "The dashboard hangs whenever I filter by 'last 90 days'. Tried 3 browsers.",
    "Hi, just wondering if there's a student discount.",
]


def build_requests() -> list[Request]:
    requests: list[Request] = []
    for i, text in enumerate(SAMPLE_INPUTS):
        requests.append(
            Request(
                custom_id=f"classify-{i:04d}",
                params=MessageCreateParamsNonStreaming(
                    model=MODEL,
                    max_tokens=200,
                    system=[
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral", "ttl": "1h"},
                        }
                    ],
                    messages=[{"role": "user", "content": text}],
                ),
            )
        )
    return requests


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY", file=sys.stderr)
        return 1

    client = anthropic.Anthropic(api_key=api_key)

    print("Submitting batch...")
    batch = client.messages.batches.create(requests=build_requests())
    print(f"  batch id = {batch.id}")
    print(f"  status   = {batch.processing_status}")

    print("\nPolling (most batches finish in <1 minute)...")
    while batch.processing_status != "ended":
        time.sleep(15)
        batch = client.messages.batches.retrieve(batch.id)
        counts = batch.request_counts
        print(
            f"  status={batch.processing_status} "
            f"processing={counts.processing} succeeded={counts.succeeded} "
            f"errored={counts.errored}"
        )

    print("\nResults:")
    total_input = total_output = total_cache_create = total_cache_read = 0
    for result in client.messages.batches.results(batch.id):
        if result.result.type != "succeeded":
            print(f"  [{result.custom_id}] FAILED: {result.result.type}")
            continue
        msg = result.result.message
        u = msg.usage
        total_input        += u.input_tokens
        total_output       += u.output_tokens
        total_cache_create += u.cache_creation_input_tokens or 0
        total_cache_read   += u.cache_read_input_tokens or 0
        print(f"  [{result.custom_id}] -> {msg.content[0].text}")

    print("\nAggregate usage across the batch:")
    print(f"  fresh_input          = {total_input}")
    print(f"  cache_creation_input = {total_cache_create}")
    print(f"  cache_read_input     = {total_cache_read}")
    print(f"  output               = {total_output}")
    print(
        "\nNote: Batch API rates are 50% of standard. "
        "When you compute cost, multiply each line above by the corresponding "
        "Batch rate, not the sync rate. See 07_cost_calculator.py."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
