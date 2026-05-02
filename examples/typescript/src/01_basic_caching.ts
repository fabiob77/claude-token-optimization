/**
 * 01 - Basic prompt caching with cost comparison
 * ==============================================
 *
 * The simplest form of prompt caching: a long, stable system prompt
 * marked with `cache_control`. The first call writes to the cache;
 * subsequent calls within the TTL hit it at 10% of base input cost.
 *
 * Run twice within 5 minutes to see the cache_read on the second run:
 *
 *     npm run example:01
 */

import "dotenv/config";
import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-sonnet-4-6";

// Sonnet 4.6 prices, USD per 1M tokens (April 2026)
const PRICE_INPUT = 3.0;
const PRICE_OUTPUT = 15.0;
const PRICE_CACHE_WRITE_5M = 3.75; // 1.25x
const PRICE_CACHE_READ = 0.3; // 0.10x

// A long, stable system prompt. Must be >=1,024 tokens to be cacheable.
const STYLE_GUIDE = `You are an expert legal-writing assistant for a UK SME.

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
`.repeat(6); // repeat to comfortably clear the 1,024-token minimum

interface CostBreakdown {
  freshInputTokens: number;
  cacheCreationTokens: number;
  cacheReadTokens: number;
  outputTokens: number;
  costUsd: number;
}

function costBreakdown(usage: Anthropic.Messages.Usage): CostBreakdown {
  const fresh = usage.input_tokens;
  const create = usage.cache_creation_input_tokens ?? 0;
  const read = usage.cache_read_input_tokens ?? 0;
  const out = usage.output_tokens;
  const cost =
    (fresh * PRICE_INPUT +
      create * PRICE_CACHE_WRITE_5M +
      read * PRICE_CACHE_READ +
      out * PRICE_OUTPUT) /
    1_000_000;
  return {
    freshInputTokens: fresh,
    cacheCreationTokens: create,
    cacheReadTokens: read,
    outputTokens: out,
    costUsd: Math.round(cost * 1_000_000) / 1_000_000,
  };
}

async function ask(client: Anthropic, question: string): Promise<void> {
  const resp = await client.messages.create({
    model: MODEL,
    max_tokens: 400,
    system: [
      {
        type: "text",
        text: STYLE_GUIDE,
        cache_control: { type: "ephemeral" }, // 5-min TTL by default
      },
    ],
    messages: [{ role: "user", content: question }],
  });

  const textBlock = resp.content.find((b) => b.type === "text");
  const text = textBlock?.type === "text" ? textBlock.text : "(no text)";
  console.log(`\nQ: ${question}`);
  console.log(`A: ${text.slice(0, 300)}...`);
  console.log(`   ${JSON.stringify(costBreakdown(resp.usage))}`);
}

async function main(): Promise<void> {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Set ANTHROPIC_API_KEY in your environment.");
    process.exit(1);
  }
  const client = new Anthropic();

  console.log("=== First call: should write to cache ===");
  await ask(client, "Summarise the indemnification clause in a typical SaaS NDA.");

  console.log("\n=== Second call: should HIT the cache (cacheReadTokens > 0) ===");
  await ask(client, "What are the most common termination triggers in SaaS contracts?");

  console.log(
    "\nIf cacheReadTokens is 0 on the second call, your STYLE_GUIDE " +
      "probably fell below the 1,024-token minimum or you waited >5 min.",
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
