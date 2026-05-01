# Optimizing Token Usage in Claude

> A practical handbook for **developers and consumer users** covering Claude.ai (Free / Pro / Max / Team / Enterprise), the Claude API, Claude Code, the Claude Chrome extension, and the Claude Desktop app (Cowork).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Claude](https://img.shields.io/badge/Made%20with-Claude-D97757)](https://claude.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**All pricing, model names, and limits in this guide reflect publicly available information as of late April 2026.** Anthropic changes pricing, models, and plan limits regularly, always verify against [claude.com/pricing](https://claude.com/pricing) and the official docs before making architectural decisions.

---

## 📖 What's in this repository

```
.
├── README.md ← you are here (the full guide)
├── docs/
│ └── full-guide.md ← same guide, separated for easier deep-linking
├── examples/
│ ├── python/ ← runnable Python examples (caching, batching, …)
│ └── typescript/ ← runnable TypeScript examples
├── tables/ ← stand-alone reference tables
│ ├── model-pricing.md
│ ├── plan-comparison.md
│ └── feature-cost-impact.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

**Where to start:**

- **Just want to stop hitting the limit on Claude.ai?** Jump to [§3 Consumer guide](#3-consumer-guide).
- **Building on the API?** Read [§6 Developer guide](#6-developer-guide-the-claude-api), then [§7 Prompt caching](#7-prompt-caching-deep-dive) and [§8 Batch API](#8-batch-api), and try the code in [`examples/python`](examples/python) or [`examples/typescript`](examples/typescript).
- **Heavy Claude Code user?** Skip to [§11 Claude Code, token survival guide](#11-claude-code-token-survival-guide).

---

## TL;DR

- **Consumers:** The single biggest lever is **conversation length**: Claude re-reads the entire chat on every turn. Start new conversations often, edit (don't reply to) bad responses, use **Projects** for reusable context, turn off Extended Thinking / Web Search / Connectors when you don't need them, and match the model to the task (Haiku for trivial, Sonnet for default, Opus only when the quality lift pays off).
- **Developers:** Three mechanical levers stack into ~95% savings: **prompt caching** (cache reads cost 10% of base input, pay-back after one read on the 5-min TTL), the **Batch API** (50% off all tokens for async work), and **model routing** (Haiku $1/$5 → Sonnet $3/$15 → Opus $5/$25 per MTok). Add `count_tokens`, explicit `max_tokens`, the `effort` parameter, and tight thinking budgets to keep output under control.
- **Claude Code & Desktop (Cowork):** Tokens compound silently. Every file read, MCP tool, and CLAUDE.md re-injection lives in context for the rest of the session. Use `/clear` aggressively between unrelated tasks, prefer `/compact` with focus instructions over auto-compaction, audit MCP servers (each can add 1.5K-18K tokens of overhead per turn), keep CLAUDE.md under ~200 lines, and use **Skills** so heavy reference material loads only when needed.

---

## Table of Contents

1. [How Claude charges you (the mental model)](#1-how-claude-charges-you-the-mental-model)
2. [Current pricing & plan reference (April 2026)](#2-current-pricing--plan-reference)
3. [Consumer guide: Claude.ai, Pro, Max, Team, Enterprise](#3-consumer-guide)
4. [The Claude Desktop app (Cowork)](#4-claude-desktop-cowork)
5. [Claude in Chrome](#5-claude-in-chrome)
6. [Developer guide: the Claude API](#6-developer-guide-the-claude-api)
7. [Prompt caching deep dive](#7-prompt-caching-deep-dive)
8. [The Batch API](#8-batch-api)
9. [Extended thinking & the `effort` parameter](#9-extended-thinking--effort)
10. [Tool use, vision, and PDFs](#10-tool-use-vision-pdfs)
11. [Claude Code: token survival guide](#11-claude-code-token-survival-guide)
12. [Real cost-savings worked examples](#12-real-cost-savings-worked-examples)
13. [Code examples (Python & TypeScript)](#13-code-examples)
14. [Comparison tables](#14-comparison-tables)
15. [Caveats & known issues](#15-caveats)

---

## 1. How Claude charges you (the mental model)

Everything in Claude (chat, Code, the API, Cowork) is metered in **tokens**. A token is roughly 4 English characters or ¾ of a word. Two facts dominate every cost decision:

1. **Models are stateless.** Each turn re-sends the entire conversation as input. A 14-token follow-up question on turn 30 actually costs you turn-1-through-30 in input tokens. One developer's tracking showed the same 14-token question costing $0.0018 on turn 1 and ≈$2.41 on turn 260, a 1,339× increase driven entirely by replayed history.
2. **Output costs ≈5× input** across every current Claude model. Chatty responses, retries, and "rewrite the whole file" patterns are the most expensive thing you can do.

Consumer plans translate token usage into a "usage limit" that resets every 5 hours, plus a weekly cap. Developer/API usage is billed per million tokens (MTok). Claude Code (when authenticated against a Pro/Max subscription) draws from the same shared bucket as Claude.ai.

---

## 2. Current pricing & plan reference

### 2.1 API model pricing (per 1M tokens, USD)

| Model | Input | Output | 5-min cache write | 1-h cache write | Cache read | Context |
|---|---|---|---|---|---|---|
| **Claude Opus 4.7** (flagship, Apr 2026) | $5.00 | $25.00 | $6.25 | $10.00 | $0.50 | 1M |
| Claude Opus 4.6 | $5.00 | $25.00 | $6.25 | $10.00 | $0.50 | 1M |
| **Claude Sonnet 4.6** (recommended default) | $3.00 | $15.00 | $3.75 | $6.00 | $0.30 | 1M |
| Claude Sonnet 4.5 | $3.00 | $15.00 | $3.75 | $6.00 | $0.30 | 200K (1M beta with surcharge) |
| **Claude Haiku 4.5** (volume / latency) | $1.00 | $5.00 | $1.25 | $2.00 | $0.10 | 200K |
| Claude Opus 4 / 4.1 *(deprecated, retire path)* | $15.00 | $75.00 | - | - | - | 200K |
| Claude Haiku 3.5 *(legacy)* | $0.80 | $4.00 | - | - | - | 200K |

Multipliers that stack on these rates:

- **Batch API**: 0.5× on input *and* output (50% off).
- **Prompt caching**: cache writes 1.25× (5-min TTL) or 2.0× (1-h TTL); cache reads 0.1×.
- **`inference_geo` US-only routing** (Opus 4.6+): 1.1× on every category.
- **Fast mode** (Opus 4.6, beta research preview): 6× standard rates, can't combine with Batch.
- **Long-context surcharge** on Sonnet 4.5 over 200K input tokens: 2× input / 1.5× output. Sonnet 4.6 and Opus 4.6/4.7 carry **no** surcharge across the full 1M window.
- **Opus 4.7 tokenizer**: a new tokenizer that may produce up to ~35% more tokens for the same text. Per-token rates didn't change but effective request cost can rise 0-35%; benchmark before migrating from 4.6.

### 2.2 Subscription plans (Claude.ai)

| Plan | Price | 5-hour rolling allowance (vs Pro) | Weekly cap | Models | Notes |
|---|---|---|---|---|---|
| **Free** | $0 | ~30-100 short messages/day, varies with demand | - | Sonnet 4.5/4.6 (limited), Haiku | No Claude Code; no Projects on legacy free; basic memory |
| **Pro** | $20/mo ($17/mo annual) | 1× (~45 short msgs / 5 h) | ~40-80 h Sonnet/week | Sonnet, Haiku, limited Opus | Includes Claude Code in terminal; Projects; Memory |
| **Max 5×** | $100/mo | 5× Pro | ~140-280 h Sonnet, 15-35 h Opus | + Opus full access | Includes Claude Code, Chrome, Cowork |
| **Max 20×** | $200/mo | 20× Pro | ~240-480 h Sonnet, 24-40 h Opus | All models | Heaviest individual plan |
| **Team Standard** | $30/seat (≥5 seats) | 1.25× Pro per seat | weekly cap | All non-Opus by default | Admin controls, SSO |
| **Team Premium** | (higher seat) | 6.25× Pro per seat (peak headroom) | dual weekly caps (all-models + Sonnet-only) | + Opus, Claude Code | Better burst headroom than Max 5× |
| **Enterprise** | Custom | Custom | Usage-based or seat-based | All models, **500K context** on some models, 1M on Opus 4.6+ in Code | SCIM, audit logs, data residency |

**Important nuances:**

- **All Claude surfaces share one bucket.** claude.ai, Claude Desktop, Cowork, and Claude Code on Pro/Max all draw from the same usage limit. API usage is billed separately.
- **Sonnet and Opus have separate limits** on Max plans since Nov 2025, burning through Opus no longer blocks Sonnet (verified in Anthropic's Opus 4.5 release post; the public help-center copy still describes it as "shared," so expect ambiguity here).
- **Extra usage** can be enabled in Settings → Usage on Pro/Max/Team to keep working past a limit at standard API rates.
- **Peak/off-peak billing**: limits deplete faster on weekdays 5 a.m.-11 a.m. Pacific.
- **Context window**: 200K tokens on all paid plans by default; 500K on some Enterprise models; 1M for Opus 4.6+/Sonnet 4.6 in Claude Code on Max/Team Premium/Enterprise.

---

## 3. Consumer guide

> If you're on claude.ai, the iOS/Android app, or the Claude Desktop app and your goal is "stop hitting the limit," this section is the whole game.

### 3.1 The single most important habit: edit, don't reply

When Claude misses, your instinct is to type *"No, I meant…"*. Don't. Click the **pencil/edit icon** on your original message, fix the prompt, and regenerate. The bad exchange is replaced rather than added to history. Every "no, try again" message permanently doubles part of the conversation cost.

### 3.2 Manage conversation length aggressively

- **Start a new chat every 15-20 messages** for unrelated work. New topic = new chat, always.
- When ending a long session, ask Claude *"Summarize everything important from this chat"*, copy that, open a new chat, paste it as message 1.
- For paid plans with code execution enabled, Claude auto-summarizes when you approach 200K. This is a fallback, not a strategy. Auto-compaction quality degrades, and the summary is generated when the model is at its least intelligent.
- Long conversations that trigger automatic context management deplete your usage limit faster.

### 3.3 Batch your questions in one message

Three sequential prompts ("summarize," "list bullets," "suggest a headline") cost 3× the context replay of one prompt that asks for all three. One message, three answers.

### 3.4 Use Projects for any recurring context

- **Projects use RAG** on paid plans: when project knowledge approaches the context window, Claude retrieves only relevant chunks instead of stuffing all files into context. Capacity is roughly 10× the normal context limit.
- Upload reference docs (style guides, contracts, books, schemas) **once** into a Project; chats inside that Project don't re-pay to load them.
- Keep project **instructions** short (under a few hundred words). They prepend every message in the project.
- Clean up unused project files: they still consume tokens during retrieval.
- **Known caveat:** RAG mode in Projects activates around ~13 files regardless of total token size, and partial retrieval can produce hallucinations or instruction-adherence drops. If your project has many small files and you want full direct loading, consolidate into fewer larger files.

### 3.5 Memory, Styles, and custom instructions

- **Memory** (Settings → Capabilities → Memory) generates a synthesis from your chat history, refreshed every 24 hours, then injects it as context into every new standalone conversation. Free, Pro, Max, Team, and Enterprise users all get it. Project memories are scoped per-project.
- **Styles** (model selector → Styles): pick or build "Concise". The system prompt persists across chats without burning context every time.
- **Personal preferences** in Settings let you add a short "about me" without paying tokens to re-explain it on every new chat.
- Memory and Styles **add input tokens to every turn**: keep them tight. A 22,000-word "about me" file is a token furnace. Aim for under ~2,000 words.
- **Incognito chats** skip memory entirely: useful when you don't want a one-off session to pollute your synthesis.

### 3.6 Turn off features you don't need

Each of these adds tokens to *every* response when enabled:

| Feature | Approximate per-response cost | When to leave on |
|---|---|---|
| Extended Thinking | Tens of thousands of output tokens (billed) | Hard math, research, multi-step planning |
| Web Search | Per-search content ingestion + tokens for results | When facts must be current |
| Research / Deep Research mode | Highest per-task cost on the platform | True research projects, not Q&A |
| Connectors (Slack, GDrive, etc.) | Tool descriptions on every turn | When you actively need them in this chat |
| MCP connectors | 1.5K-18K extra tokens per turn | Active use only |
| File attachments still in chat | Re-encoded every turn | When still relevant |

Default policy: **everything off, switch on per task.**

### 3.7 Pick the right model for the task

- **Haiku 4.5**: grammar, formatting, short questions, summarization, quick lookups.
- **Sonnet 4.6**: default for writing, analysis, coding, research, anything substantive.
- **Opus 4.7**: complex reasoning, large-codebase analysis, agentic tasks, instruction-precision work (legal, brand-voice, safety-critical).

Heuristic: *if Claude takes <30 s to answer, you don't need Opus.* On Max, Opus consumes the limit fastest.

### 3.8 Attachments: the silent hogs

- A single PDF page ≈ 1,500-3,000 tokens.
- A full 1000×1000 image ≈ 1,300 tokens; high-res images on Opus 4.7 can be ~3× that (up to 4,784 tokens at 2,576 px).
- A 500 kB research PDF can be ~125,000 tokens, half your free context budget on a single upload.
- **Tip:** convert PDFs/screenshots to plain markdown before uploading when text is what you actually need; downsample images.
- Don't re-upload the same file in a chat: Claude already has it.

### 3.9 Match tool/surface to task

- **Cowork (Claude Desktop)** is the most token-intensive surface. A single "organize my downloads" can burn thousands of input/output tokens during the agent loop. Use Chat for planning, Cowork only for the execution.
- **Artifacts/file creation** uses more of your limit than regular chat. Plan in chat, generate in artifact mode.
- **Claude Code** is excellent for code, but agentic teammates can use ~7× the tokens of single-agent sessions.

### 3.10 Monitoring usage

- **claude.ai** → **Settings → Usage**: shows current 5-hour and weekly limit consumption (including Opus-specific bar on Max).
- **`/usage`** in Claude Code shows per-session token usage and (for API users) cost.
- Browser extension *Claude Usage* (third-party, GitHub: `cfranci/claude-usage-extension`) puts a colored % badge in the Chrome toolbar.
- **Anthropic Console → Usage** for API customers (admin export available for Team/Enterprise).

---

## 4. Claude Desktop (Cowork)

Cowork is Anthropic's agentic file-management surface inside the Claude Desktop app. It runs Claude Code's underlying loop in a sandboxed micro-VM with filesystem access.

**Cost reality:** Cowork is dramatically more token-intensive than chat. A "clean up my downloads" prompt can run an autonomous plan→execute→re-plan loop that produces thousands of input + output tokens in minutes. Heavy sessions also degrade after about 30 minutes of continuous work.

**Cost-saving habits specific to Cowork:**

- **Plan first in standard chat**, then move the agreed plan into Cowork for execution.
- **Maintain a `memory.txt` or `session-notes.md`** in your working folder; instruct Cowork to log progress there. New sessions read the file instead of replaying history.
- **Trim the "about me" / project context** Cowork reads at session start. Under 2,000 words is a healthy upper bound.
- **Disable connectors you don't need** in the Cowork session; they add tool definitions to every turn.
- **Schedule heavy tasks for off-peak hours**; Cowork shares the Claude.ai bucket and depletes faster on weekdays 5-11 a.m. Pacific.

---

## 5. Claude in Chrome

The Chrome extension (Pro+ only, Haiku 4.5 for Pro, full model picker for Max/Team/Enterprise) automates browser tasks. Cost notes:

- The extension takes screenshots of the active tab to "see" the page; every screenshot is a vision input (~1,300+ tokens for a typical screen).
- Workflows often involve multiple tabs and steps; one approval-then-execute run can rival a Cowork session in tokens.
- **Save your best prompts as shortcuts** (type `/` in chat) and reuse the same instructions instead of rewriting.
- **Disable the extension on sites you don't need it for** to avoid accidental screenshots/context capture.
- For Claude Code + Chrome (the developer integration via `/chrome`), the same principles apply: be specific about console-log patterns to look for, rather than "show me all errors."

---

## 6. Developer guide: the Claude API

### 6.1 Five rules that beat 90% of cost problems

1. **Cache anything that repeats** (system prompts, tool defs, big documents, conversation prefix).
2. **Batch anything that doesn't need a real-time answer** (reports, evals, content generation).
3. **Route by complexity**: Haiku → Sonnet → Opus is a portfolio, not a tier ladder.
4. **Cap output** with a tight `max_tokens`, the `effort` parameter, and stop sequences.
5. **Measure first** with `count_tokens` and the response `usage` object, never optimize in the dark.

### 6.2 Choosing a model

- **Haiku 4.5** ($1/$5): classification, routing, extraction, moderation, simple Q&A. 5× cheaper than Sonnet on both axes.
- **Sonnet 4.6** ($3/$15): production default. ~67% cheaper than Sonnet legacy, 1M context at flat pricing, near-Opus quality on most tasks.
- **Opus 4.7** ($5/$25): complex coding agents, long-horizon tasks, instruction-precision work. Only 1.67× Sonnet, but the new tokenizer can lift effective cost up to ~35%.

A common production split is 60-70% Haiku / 25-30% Sonnet / 5-10% Opus, dispatched by a router that uses input length, task type, or a quick Haiku classifier to decide.

### 6.3 Token counting before you spend

Use `messages.count_tokens` to estimate every request before sending it. It supports `system`, `tools`, images, PDFs, and thinking; it's free, has its own rate limit, and is ZDR-eligible.

```python
import anthropic
client = anthropic.Anthropic()

response = client.messages.count_tokens(
 model="claude-sonnet-4-6",
 system="You are a senior code reviewer.",
 messages=[{"role": "user", "content": "Review this PR..."}],
)
print(response.json()) # {"input_tokens": 1234}
```

See [`examples/python/04_token_counting.py`](examples/python/04_token_counting.py) and [`examples/typescript/src/04_token_counting.ts`](examples/typescript/src/04_token_counting.ts) for runnable versions.

### 6.4 Context-window management

- Opus 4.7, Opus 4.6, Sonnet 4.6 → 1M tokens at flat pricing. Sonnet 4.5 → 200K (1M beta carries 2×/1.5× surcharge above 200K).
- Haiku 4.5 → 200K. Don't try to scale Haiku into long-context workloads; pay Sonnet rates instead.
- Use `count_tokens` + the `model_context_window_exceeded` stop reason to gracefully truncate or hand off.
- On Sonnet 4.6 / Sonnet 4.5 / Haiku 4.5, **context-awareness** lets the model track its remaining budget and finish gracefully.

### 6.5 System-prompt optimization

- Put **stable** content (instructions, schemas, examples, RAG corpus) **before** dynamic content. Caching is a strict prefix cache, anything that changes invalidates everything after it.
- For RAG, put the retrieved chunks *before* the user's question, not after.
- **Compress** the system prompt: structured headers + bullets, no narrative. A "reduce verbosity" rule produced 63% output-token reduction in one independent benchmark.
- **Don't ship verbose few-shot examples to Haiku** unless you've measured the lift.
- Use the `system` parameter (not the first user message) so it benefits from caching.

### 6.6 The `max_tokens` knob

- **Always set it.** Default behavior changed across model generations; Claude 3.7+ enforces `prompt_tokens + max_tokens ≤ context_window` as a strict validation.
- Streaming is **required** when `max_tokens > 21,333`.
- For agentic loops with thinking, `max_tokens` must be greater than `thinking.budget_tokens`.
- Check `stop_reason`: `"max_tokens"` means you cut off output and may be billed for an incomplete response.

### 6.7 Stop sequences

`stop_sequences` (up to 8,191 entries) lets the model stop at custom strings, useful for structured output, JSON termination, or stopping at section headers. Saves output tokens on long responses you only need the first part of.

### 6.8 Streaming vs. non-streaming

- **Streaming** improves perceived latency (Time to First Token) and is required for max_tokens > 21,333 and large extended-thinking budgets.
- **Non-streaming** is simpler for batch-style workloads and the Batch API requires it.
- The SDK throws errors on non-streaming requests expected to exceed ~10 minutes, if you need long output, stream or use Batch.

---

## 7. Prompt caching deep dive

Prompt caching is the single highest-ROI change you can make to a Claude API integration.

### 7.1 How it works

You mark a content block with `cache_control: {"type": "ephemeral"}` (5-min TTL) or `{"type": "ephemeral", "ttl": "1h"}` (1-h TTL). The API stores an internal KV-cache representation of the *prefix up to and including that block*. Subsequent requests with the same exact prefix hit the cache.

- **Cache writes**: 1.25× base input (5-min) or 2.0× base input (1-h).
- **Cache reads**: 0.1× base input, a flat **90% discount** on the cached portion.
- **Pay-back**: caching pays for itself after one read on the 5-min TTL, two reads on the 1-h TTL.
- **Minimum cacheable size**: 1,024 tokens (Haiku 3 had 2,048; Haiku 4.5 follows the 1,024 standard). Shorter prompts silently bypass cache.
- **Cache hierarchy**: `tools → system → messages`. Up to **4 cache breakpoints** per request.
- **Verification**: response `usage` includes `cache_creation_input_tokens` and `cache_read_input_tokens`. If both are 0 on what should be a cached call, you missed the minimum or the prefix changed.
- The cache is per-organization and isolated; ZDR-eligible.

### 7.2 Automatic vs explicit caching

- **Automatic caching** (set `cache_control` once at the top level of the request): the API picks breakpoints as conversations grow. Best for getting started; only one breakpoint is chosen.
- **Explicit breakpoints**: place `cache_control` on individual content blocks. Required for agent loops where you want separate caches for tool definitions, system prompt, and message-history checkpoints.

### 7.3 The 5-min vs 1-h TTL decision

- **5-min**: high-traffic prefixes hit constantly (chatbots, classifiers). Each read resets the TTL.
- **1-h**: shared static content across users, batch processing (which can take >5 min), agentic loops with multi-minute pauses. Higher write cost but no compounding re-creation penalty.
- **Default change (March 2026):** Anthropic silently shifted the default TTL from 1 h to 5 min, including in Claude Code. If you were relying on the 1-h default, you're now paying full input price every time a session pauses past 5 minutes. Fix: explicitly set `ttl` and audit `cache_creation` vs `cache_read` token splits.

### 7.4 Cache-friendly architecture

- Static (cacheable) content **first**, dynamic content **last**.
- Working memory, runtime variables, per-user state must sit *after* the last breakpoint or you'll invalidate the prefix.
- For multi-step agents: place a breakpoint after `tools`, after the system prompt, and intermediate breakpoints every ~18 message blocks (the docs note that more than 20 content blocks before a breakpoint with edits to early blocks won't hit cache).
- **Disable extended thinking in caching-critical paths on third-party providers** (Bedrock/Vertex have inconsistent behavior); on Anthropic direct, thinking blocks cache cleanly on Opus 4.5+/Sonnet 4.6+ but are stripped on earlier models.

### 7.5 Caching for RAG

Cache the system prompt + the retrieved-document context block. Each user query only re-bills the question itself. A 50K-token knowledge base queried 1,000 times/day on Sonnet 4.6:

- **No cache**: 1,000 × 50K × $3/MTok = **$150/day** input.
- **With 5-min cache, ~80% hit rate**: ~$15/day input, a **90% reduction** on cached tokens.

### 7.6 Caching tool definitions

Tool definitions live in the cacheable region (before `system` and `messages` in the cache hierarchy). MCP tool schemas in particular are huge (1.5K-8K tokens for a typical server, up to 18K for many servers). Cache them once.

---

## 8. Batch API

### 8.1 What and when

- **Asynchronous processing** of up to 10,000 (sometimes 100,000) requests per batch, returned within **24 hours** (most finish in <1 h).
- **50% discount on both input and output tokens** for every model.
- **Stacks with prompt caching**: Anthropic's own engineers have demonstrated combined 90-95% effective discounts.
- Available beta: **300K-token output extension** (`output-300k-2026-03-24`) for book-length single-message generations (Batch-only).
- Higher rate-limit ceilings than the synchronous API.
- Mix any models, parameters, and beta flags within a single batch.

### 8.2 Use it for

- Document/data processing pipelines.
- Nightly evals, red-team runs, model comparisons.
- Bulk content generation (SEO articles, product descriptions, classification).
- Large extractions, summarization corpora, migrations.

### 8.3 Don't use it for

- Anything user-facing in real time.
- Workflows that need sub-minute SLAs.
- Fast-mode workloads (incompatible with Batch).

### 8.4 Combining with caching

Because batches can take longer than 5 minutes, use the **1-h cache TTL** with shared prefixes. Repeated cache writes inside a batch are otherwise the most common over-spend.

See [`examples/python/03_batch_api.py`](examples/python/03_batch_api.py) for an end-to-end runnable example.

---

## 9. Extended thinking & `effort`

### 9.1 Extended thinking

- Reasoning tokens are billed as **output tokens** at standard rates.
- Minimum budget is **1,024 tokens**; default budgets in some clients (notably Claude Code) can reach tens of thousands per request.
- On Opus 4.5+/Sonnet 4.6+, previous-turn thinking blocks are kept and *count toward context*. On earlier Opus/Sonnet and all Haiku, they're stripped. Plan accordingly.
- Streaming required for `max_tokens > 21,333`.
- Thinking changes invalidate cache breakpoints in messages.

### 9.2 Adaptive thinking (Opus 4.6/4.7, Sonnet 4.6)

With `thinking: {"type": "adaptive"}`, the model decides whether to think and how much, based on prompt difficulty. Replaces manual `budget_tokens`. **Recommended default**: cheaper than always-on, doesn't sacrifice quality on hard prompts.

### 9.3 The `effort` parameter

`effort: "low" | "medium" | "high" | "max"` controls the model's overall token spend (text + tool calls + thinking).

- **`low`**: for latency-sensitive chat and simple Q&A; produces fewer tool calls and shorter responses.
- **`medium`** (recommended for most prod): solid balance.
- **`high`** (default): default behavior. Equivalent to omitting the parameter.
- **`max`**: highest capability; for the work where money is no object.

`effort` works without thinking enabled. It modulates plain output too. Use `low` to cut costs on Sonnet 4.6's chat workloads where quality is already adequate.

### 9.4 Task budgets (Opus 4.7 beta)

Opus 4.7 supports `task_budget`, an advisory token budget across an entire agentic loop (thinking + tool calls + tool results + final output). The model sees a running countdown and prioritizes work.

---

## 10. Tool use, vision, PDFs

### 10.1 Tool-use overhead

When **any** tool is provided, Anthropic adds a hidden tool-use system prompt:

| Tool category | Approx. extra system-prompt tokens |
|---|---|
| Generic `tools` array (≥1 tool) | model-specific (typically 200-800) |
| `bash` tool | +245 |
| `computer_use` tool | +466-499 + per-screenshot vision tokens |
| Multi-server MCP setup | 1,500-18,000 per turn (audit your config) |

There is **no cross-turn caching of tool definitions at the API level by default**: every request pays full overhead unless you put a `cache_control` breakpoint after the `tools` block. For MCP-heavy agents, this is the single biggest correctable inefficiency.

### 10.2 Server tools with separate fees

- **Web search**: $10 per 1,000 searches (plus tokens for content).
- **Web fetch**: standard token cost only. Average page ~2,500 tokens, large doc ~25,000, big PDF ~125,000. Use `max_content_tokens` to cap.
- **Code execution**: free when used with web search/fetch; otherwise billed by container-hour.

### 10.3 Vision pricing

- Token cost ≈ `width × height / 750` per image, capped per model.
- Standard models: max 1,568 px on the long edge → up to ~1,568 tokens.
- **Opus 4.7**: max 2,576 px → up to 4,784 tokens (~3× standard); 1:1 pixel mapping for computer use.
- 600 images max per request on 1M-context models; 100 on 200K-context models.
- **Pre-resize**: downsample any image where text or layout fidelity isn't critical. A 682×318 image costs ~314 tokens; a 3456×2234 image costs 3,000+ tokens on Opus 4.7.

### 10.4 PDFs

PDFs are billed per-page as a mix of text and image tokens. A 30-page text-heavy PDF runs ~56K (Opus 4.6) to ~61K (Opus 4.7) tokens. Strategies:

- Extract text client-side and send markdown when you only need text.
- Use Files API + cached document blocks to reuse the same PDF across many queries.
- Combine with prompt caching: 100-page legal doc cached once, queried dozens of times at 10% rate.

---

## 11. Claude Code: token survival guide

### 11.1 Subscription vs API for Claude Code

| Pattern | Best fit |
|---|---|
| Daily, full-workday use | **Pro** ($20) → **Max 5×** ($100) → **Max 20×** ($200). Flat fee usually 2-3× cheaper than equivalent API spend |
| Bursty, intensive sessions | Team Premium seat (6.25× Pro per session, even more headroom than Max 5×) |
| Pay-as-you-go automation, CI/CD | API key (set workspace spend limits in console) |

**Real numbers (Anthropic + community estimates):**

- Pro user: ~10-40 prompts per 5-h window, 40-80 hours of Sonnet/week.
- Max 5×: ~50-200 prompts/window, 140-280 h Sonnet, 15-35 h Opus.
- Max 20×: ~200-800 prompts/window, 240-480 h Sonnet, 24-40 h Opus.
- One developer reported 10 billion tokens over 8 months → ~$15K API equivalent vs $800 on Max ($100 × 8), a **93% saving**.
- Enterprise average: ~$13/dev/active day, $150-250/dev/month.

### 11.2 The four habits that actually work

1. **`/clear` aggressively.** Switching tasks → clear. Old conversation lives in input on every turn until you do.
2. **`/compact <focus>` deliberately, not reactively.** Auto-compaction fires when context is at peak rot; the summary is generated by the worst version of Claude. Use `/compact Focus on the API changes and the list of modified files` at logical breakpoints.
3. **Subagents for noisy work.** "Read these 12 files and tell me X" → spin up a subagent so the raw exploration stays in *its* context and only the conclusion comes back.
4. **`/rewind` (or Esc-Esc) instead of correcting.** A failed attempt + corrections poisons the rest of the session. Roll back, re-prompt, move on.

### 11.3 CLAUDE.md best practices

- **Under 200 lines.** Longer files reduce adherence and inflate every turn's input.
- Hierarchy: global `~/.claude/CLAUDE.md` for personal preferences; project-root for shared conventions; nested per-directory for path-scoped rules.
- Project-root CLAUDE.md **survives compaction** (re-read from disk after `/compact`). Nested files reload only when Claude touches matching paths.
- Be **specific to actual failure modes**, not generic. "When a step fails, stop and report the full traceback before fixing" beats "be careful."
- Don't duplicate skill content. Skills load on demand; CLAUDE.md loads always.

### 11.4 Skills: the underused token saver

Skills are markdown files (`SKILL.md`) loaded *only* when invoked. The startup cost is just the 1-2-line description in the system prompt; full content is fetched lazily via Bash when triggered.

- Use skills for **specialized procedural knowledge** (deployment, API conventions, debug playbooks) that you'd otherwise paste into prompts repeatedly.
- Skills compose with caching: once invoked, skill content is cache-stable, so subsequent turns pay 10% rates.
- After auto-compaction, Claude Code re-attaches the most recent invocation of each skill, keeping the first 5,000 tokens (combined budget 25,000 across skills).
- Anthropic ships bundled skills (`/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`); the community library `antigravity-awesome-skills` bundles 1,200+.
- **Audit installed skills/plugins.** A 2026 community report (GitHub issue #29971) documented setups where 49 plugins were registered, only 3 actually used, and 25K tokens of skill metadata wasted per tool call.

### 11.5 Tame your MCP servers

Each MCP server injects its full tool schema into every turn: typically 1,500-4,000 tokens per server, up to 8,000 with rich documentation, totaling 18K+ tokens with several servers connected.

- Run `/context` mid-session to see live overhead.
- Disable unused servers per project (project-level `.claude/settings.json`).
- Trim tool descriptions in servers you control.
- Use **context-mode** style MCPs that index tool outputs into a sandbox knowledge base instead of dumping JSON straight into context.

### 11.6 Other Claude Code tips

- **Plan Mode** (Shift+Tab) before multi-file changes. Cheaper to plan than to recover from the wrong direction.
- **Diff output, not full files.** "Give me the changes as a diff" saves thousands of output tokens.
- **Specific line ranges**, not whole files: "Look at auth.ts lines 42-58" beats pasting the file.
- **Batch edits in one prompt**: "Add error handling to functions A, B, C, D" beats four prompts.
- **`MAX_THINKING_TOKENS=8000`** env var lowers the default extended-thinking budget for non-critical sessions.
- **`/effort low`** for chat-style coding questions on Sonnet 4.6 (which defaults to high).
- **`/usage`** at any point to see session token counts and (for API users) cost.

---

## 12. Real cost-savings worked examples

All numbers in USD, current pricing as of April 2026.

### 12.1 Caching a 10,000-token system prompt (Sonnet 4.6, 1,000 daily requests)

| Strategy | Daily input cost |
|---|---|
| No caching: 1,000 × 10,000 × $3/MTok | **$30.00** |
| 5-min cache, ~99% hit rate: 1 write at 1.25× + 999 reads at 0.1× = (10,000×$3.75 + 999×10,000×$0.30)/MTok | **≈ $3.04** |
| Same with Batch API (50% off): | **≈ $1.52** |

Savings: **~90% on caching alone, ~95% caching + Batch.**

### 12.2 Batch API on 1M tokens (Sonnet 4.6, 70/30 in/out split)

| Mode | Cost |
|---|---|
| Standard: 0.7M × $3 + 0.3M × $15 | $6.60 |
| Batch (50% off): | **$3.30** |

### 12.3 Haiku vs Opus for simple classification

10M input / 2M output tokens of routing/classification:

| Model | Cost |
|---|---|
| Opus 4.7: 10×$5 + 2×$25 | **$100.00** |
| Sonnet 4.6: 10×$3 + 2×$15 | $60.00 |
| **Haiku 4.5**: 10×$1 + 2×$5 | **$20.00** |
| Haiku 4.5 + Batch: | **$10.00** |

**80% saving** by routing to Haiku; 90% with Batch.

### 12.4 Monthly scenario costs (Sonnet 4.6 unless noted)

| Scenario | Volume | Naive cost | Optimized cost | Strategy |
|---|---|---|---|---|
| Customer-support chatbot | 50K conv/mo, 2K in / 500 out | $4,500 | **~$1,200** | 5K-token cached system prompt (1-h TTL), 70/25/5 Haiku/Sonnet/Opus routing |
| Coding assistant | 10K sessions, 50K in / 15K out | $7,500 + $3,750 = **$11,250** | **~$3,000** | Cache repo digest, Sonnet default + Opus only for hard cases |
| Document analysis | 20K docs, 10K in / 1K out | $300 (Sonnet) | **~$150** | Batch API + 1-h cache on per-doc system instructions |
| SEO content generation | 20M in / 10M out (Haiku 4.5) | $70 | **$35** | Haiku 4.5 + Batch API |
| RAG over 200K docs | 100 queries/h | $200/day | **~$30/day** | Cache the corpus, 1-h TTL, Sonnet 4.6 |
| Solo dev on Claude Code | Heavy daily | API ~$400-1,200/mo | **$100-200/mo** | Max 5× / 20× subscription instead of API |

---

## 13. Code examples

All examples in this guide are available as **runnable scripts** in:

- 🐍 [`examples/python/`](examples/python): Python with the official `anthropic` SDK
- 📘 [`examples/typescript/`](examples/typescript): TypeScript with `@anthropic-ai/sdk`

Each folder has its own README with setup instructions, an `.env.example`, and numbered files you can run individually:

| # | Topic | Python | TypeScript |
|---|---|---|---|
| 01 | Basic prompt caching with cost comparison | ✅ | ✅ |
| 02 | Multi-breakpoint caching for agents | ✅ | - |
| 03 | Batch API (with caching) | ✅ | ✅ |
| 04 | Token counting before requests | ✅ | ✅ |
| 05 | Conversation-history rolling cache | ✅ | - |
| 06 | Adaptive thinking + `effort` parameter | ✅ | - |
| 07 | Cost calculator (CLI tool) | ✅ | ✅ |

---

## 14. Comparison tables

Stand-alone reference tables also live in [`tables/`](tables) for easier copying / linking.

### 14.1 Model pricing comparison (per MTok, April 2026)

| Model | Input | Output | Cache read (90% off) | 5-min write | 1-h write | Batch in/out | Context |
|---|---|---|---|---|---|---|---|
| Opus 4.7 | $5.00 | $25.00 | $0.50 | $6.25 | $10.00 | $2.50 / $12.50 | 1M |
| Opus 4.6 | $5.00 | $25.00 | $0.50 | $6.25 | $10.00 | $2.50 / $12.50 | 1M |
| Sonnet 4.6 | $3.00 | $15.00 | $0.30 | $3.75 | $6.00 | $1.50 / $7.50 | 1M |
| Sonnet 4.5 | $3.00 | $15.00 | $0.30 | $3.75 | $6.00 | $1.50 / $7.50 | 200K |
| Haiku 4.5 | $1.00 | $5.00 | $0.10 | $1.25 | $2.00 | $0.50 / $2.50 | 200K |
| Haiku 3.5 (legacy) | $0.80 | $4.00 | $0.08 | $1.00 | $1.60 | $0.40 / $2.00 | 200K |

### 14.2 Subscription plan comparison

| Plan | Price | Multiplier (vs Pro) | Models | Claude Code | Cowork | Chrome |
|---|---|---|---|---|---|---|
| Free | $0 | - | Sonnet (limited) | ❌ | ❌ | ❌ |
| Pro | $20/mo | 1× | + limited Opus | ✅ | ✅ | ✅ Haiku-only |
| Max 5× | $100/mo | 5× | All models | ✅ | ✅ | ✅ all models |
| Max 20× | $200/mo | 20× | All models | ✅ | ✅ | ✅ all models |
| Team Standard | $30/seat | 1.25×/seat | (no Opus by default) | ❌ | ✅ | ✅ |
| Team Premium | (higher) | 6.25×/seat | + Opus | ✅ | ✅ | ✅ |
| Enterprise | Custom | Custom | All + 500K context | ✅ | ✅ | ✅ |

### 14.3 Feature cost-impact comparison

| Feature | Effect on token spend |
|---|---|
| Editing original message vs replying | Replaces history (saves) vs appends (compounds) |
| Starting a new chat | Resets ~5K+ token system overhead/turn |
| Projects (paid plans) | RAG retrieves only relevant chunks → 10× capacity |
| Memory feature | +~hundreds of input tokens per turn for the synthesis |
| Styles | +tens of input tokens per turn (cheap, useful) |
| Extended Thinking ON | +1K to 60K+ output tokens/turn |
| Adaptive Thinking | Auto-skips on simple Qs, engages on hard ones (recommended) |
| `effort: "low"` | Significantly fewer thinking + tool tokens |
| Web Search | $10/1K searches + content tokens |
| Each MCP server | +1.5K-8K tool-schema tokens/turn |
| Computer Use | +466-499 system + per-screenshot vision tokens |
| Each PDF page | ~1.5K-3K tokens |
| Each high-res image (Opus 4.7) | up to 4,784 tokens |
| Prompt caching (cache reads) | -90% on cached input tokens |
| Batch API | -50% on input + output |
| Caching + Batch combined | up to -95% |

---

## 15. Caveats

- **Pricing and limits change frequently.** Anthropic launched Opus 4.7 on April 16, 2026 and shifted the default cache TTL from 1 h to 5 min in March 2026 without announcement. Always cross-check `claude.com/pricing` and the response `usage` object before relying on a number in this guide.
- **The Opus 4.7 tokenizer change** can raise effective cost by up to ~35% on the same workload despite identical headline pricing. Run a representative traffic sample before migrating from 4.6.
- **Plan multipliers are not equivalent to absolute token counts.** Anthropic deliberately doesn't publish exact tokens-per-window figures for Pro/Max/Team. Third-party estimates (e.g. Pro ≈ 44K tokens / 5 h) come from reverse-engineering, not Anthropic. Treat them as directional only.
- **Sonnet vs Opus limits on Max**: Anthropic's November 2025 announcement implied separate caps for Sonnet and Opus, while help-center copy still calls them "shared." Behavior in the wild matches "separate," but Anthropic has not consolidated the documentation as of April 2026.
- **"Claude is getting dumber" complaints** in early 2026 are largely attributable to the cache-TTL regression rather than model regression. Independent benchmarks show stable model quality; cache misses just made identical work feel more expensive and slower.
- **Cowork is a research preview** and shares its budget with regular Claude usage. It's the most token-intensive surface; treat it as such.
- **Free-tier capacity varies with system load**, so "30-100 msgs/day" is approximate and can be lower during peak demand.
- **The community workarounds for memory/compaction** (handoff files, manual summaries, restarts) reflect real tradeoffs in Anthropic's system, not user error; expect to keep using them for now.
- **Batch API rate limits** apply both to HTTP requests and to in-flight batch requests; very large batches can be paced down during high demand.
- **Some tools and features stack non-obviously.** Fast mode is incompatible with Batch. Cache invalidation cascades: change a single token in the cached prefix and you re-pay the full write. Extended thinking changes invalidate message-level caches.
- **Third-party providers (Bedrock, Vertex, Foundry) have different caching/thinking behavior** than the Anthropic direct API. Verify on your target before committing.

---

## 🤝 Contributing

Spotted outdated pricing, a new feature, or a better strategy? PRs welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). Please cite primary Anthropic sources (`platform.claude.com`, `support.claude.com`, official Anthropic blog posts) when proposing changes.

## 📜 License

[MIT](LICENSE). Use freely; attribution appreciated.

## 🙏 Acknowledgements

Pricing and feature claims verified against Anthropic's public docs (`platform.claude.com`, `support.claude.com`, `code.claude.com`) and Anthropic blog/release posts current as of April 30, 2026.

---

*This is a community resource and is **not** affiliated with or endorsed by Anthropic.*
