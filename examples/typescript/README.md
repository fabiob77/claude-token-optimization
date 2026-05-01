# TypeScript examples

Runnable companion code for the [main guide](../../README.md), using the official [`@anthropic-ai/sdk`](https://www.npmjs.com/package/@anthropic-ai/sdk).

## Setup

```bash
npm install
cp .env.example .env          # then edit .env and add your real key
```

Get a key at https://console.anthropic.com/. **Never commit `.env`.**

## Running

The scripts use `tsx` so you can run them straight from `.ts`:

```bash
npm run example:01      # basic caching
npm run example:03      # batch api
npm run example:04      # token counting
npm run example:07      # cost calculator (no API key needed)
```

Or directly:

```bash
npx tsx src/01_basic_caching.ts
```

## Examples

| File | What it shows |
|---|---|
| `src/01_basic_caching.ts` | Minimal prompt caching, prints usage so you can see the 90% discount on the second call. |
| `src/03_batch_api.ts` | End-to-end Batch API: build, submit, poll, fetch results. |
| `src/04_token_counting.ts` | `countTokens` for messages, system prompts, and tools. |
| `src/07_cost_calculator.ts` | Standalone CLI that estimates cost from token counts (no API key). |

The Python folder has a few additional patterns (`02_multi_breakpoint_caching`, `05_conversation_history_caching`, `06_adaptive_thinking`). Translating them to TypeScript is straightforward — PRs welcome.

## Notes

- Caching has a **1,024-token minimum** on current models. The examples use prompts long enough to qualify; if you swap in shorter content the cache will silently miss.
- The Batch API runs **non-streaming** requests only and may take up to 24 hours (most batches finish in under an hour).
- Model strings (`claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`) are valid as of April 2026. Anthropic may publish dated aliases — see https://platform.claude.com.
