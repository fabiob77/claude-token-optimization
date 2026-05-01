/**
 * 03 - Batch API end-to-end (with caching)
 * ========================================
 *
 * - Submit up to 10,000 requests in one batch
 * - 50% discount on input AND output tokens
 * - Use 1-hour cache TTL because batches can take >5 minutes
 *
 * Run:
 *     npm run example:03
 *
 * Most batches finish in <1 minute; SLA is 24 hours.
 */

import "dotenv/config";
import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-haiku-4-5";

const SYSTEM_PROMPT =
  `You are a content classifier. Read the input text and output a JSON object
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
`.repeat(5);

const SAMPLE_INPUTS = [
  "I was double-charged for last month and need this refunded ASAP.",
  "Your new export feature is brilliant - saved me hours this week!",
  "Can you add CSV export to the reports page? It's the only thing missing.",
  "The dashboard hangs whenever I filter by 'last 90 days'. Tried 3 browsers.",
  "Hi, just wondering if there's a student discount.",
];

async function main(): Promise<void> {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Set ANTHROPIC_API_KEY");
    process.exit(1);
  }
  const client = new Anthropic();

  const requests = SAMPLE_INPUTS.map((text, i) => ({
    custom_id: `classify-${String(i).padStart(4, "0")}`,
    params: {
      model: MODEL,
      max_tokens: 200,
      system: [
        {
          type: "text" as const,
          text: SYSTEM_PROMPT,
          cache_control: { type: "ephemeral" as const, ttl: "1h" as const },
        },
      ],
      messages: [{ role: "user" as const, content: text }],
    },
  }));

  console.log("Submitting batch...");
  let batch = await client.messages.batches.create({ requests });
  console.log(`  batch id = ${batch.id}`);
  console.log(`  status   = ${batch.processing_status}`);

  console.log("\nPolling (most batches finish in <1 minute)...");
  while (batch.processing_status !== "ended") {
    await new Promise((r) => setTimeout(r, 15_000));
    batch = await client.messages.batches.retrieve(batch.id);
    const c = batch.request_counts;
    console.log(
      `  status=${batch.processing_status} processing=${c.processing} succeeded=${c.succeeded} errored=${c.errored}`,
    );
  }

  console.log("\nResults:");
  let totalInput = 0,
    totalOutput = 0,
    totalCacheCreate = 0,
    totalCacheRead = 0;

  for await (const result of client.messages.batches.results(batch.id)) {
    if (result.result.type !== "succeeded") {
      console.log(`  [${result.custom_id}] FAILED: ${result.result.type}`);
      continue;
    }
    const msg = result.result.message;
    const u = msg.usage;
    totalInput += u.input_tokens;
    totalOutput += u.output_tokens;
    totalCacheCreate += u.cache_creation_input_tokens ?? 0;
    totalCacheRead += u.cache_read_input_tokens ?? 0;
    const t = msg.content.find((b) => b.type === "text");
    const text = t?.type === "text" ? t.text : "(no text)";
    console.log(`  [${result.custom_id}] -> ${text}`);
  }

  console.log("\nAggregate usage across the batch:");
  console.log(`  fresh_input          = ${totalInput}`);
  console.log(`  cache_creation_input = ${totalCacheCreate}`);
  console.log(`  cache_read_input     = ${totalCacheRead}`);
  console.log(`  output               = ${totalOutput}`);
  console.log(
    "\nNote: Batch API rates are 50% of standard. " +
      "Multiply each line above by the corresponding Batch rate. " +
      "See 07_cost_calculator.",
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
