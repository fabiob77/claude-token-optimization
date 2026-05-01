/**
 * 04 - Token counting before you spend
 * ====================================
 *
 * `messages.countTokens` returns the input-token count the model would see
 * for a given request. Free, rate-limited, supports system, tools, images,
 * PDFs, and thinking. Use it to:
 *
 * - Decide if a request fits the context window before sending it.
 * - Estimate cost (combine with prices from 07_cost_calculator).
 * - Monitor prompt sizes in tests / CI.
 *
 * Run:
 *     npm run example:04
 */

import "dotenv/config";
import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-sonnet-4-6";

async function main(): Promise<void> {
  if (!process.env.ANTHROPIC_API_KEY) {
    console.error("Set ANTHROPIC_API_KEY");
    process.exit(1);
  }
  const client = new Anthropic();

  // Case 1: simple message
  let r = await client.messages.countTokens({
    model: MODEL,
    messages: [{ role: "user", content: "Hello, world!" }],
  });
  console.log(`Simple 'Hello, world!' message    -> ${r.input_tokens} tokens`);

  // Case 2: with a system prompt
  r = await client.messages.countTokens({
    model: MODEL,
    system: "You are a senior code reviewer. Be terse.",
    messages: [{ role: "user", content: "Review this PR (assume it's small)." }],
  });
  console.log(`With short system prompt          -> ${r.input_tokens} tokens`);

  // Case 3: with tools
  r = await client.messages.countTokens({
    model: MODEL,
    system: "You answer with tool calls when appropriate.",
    tools: [
      {
        name: "get_weather",
        description: "Get the current weather for a city.",
        input_schema: {
          type: "object",
          properties: { city: { type: "string" } },
          required: ["city"],
        },
      },
    ],
    messages: [{ role: "user", content: "What's it like in London right now?" }],
  });
  console.log(`With one tool definition          -> ${r.input_tokens} tokens`);

  // Case 4: a long prompt - check it before sending
  const longText = "Repeat after me: tokens cost money. ".repeat(200);
  r = await client.messages.countTokens({
    model: MODEL,
    messages: [{ role: "user", content: longText }],
  });
  console.log(`Long padded prompt                -> ${r.input_tokens} tokens`);

  console.log(
    "\ncountTokens is free of charge for tokens but is rate-limited.\n" +
      "Use it before any expensive call - especially before sending a long\n" +
      "RAG context, a PDF, or many images.",
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
