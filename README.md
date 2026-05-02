# Optimizing Token Usage in Claude

> A practical handbook for both developers and consumer users, covering Claude.ai (Free / Pro / Max / Team / Enterprise), the Claude API, Claude Code, the Claude Chrome extension, and the Claude Desktop app (Cowork).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Made with Claude](https://img.shields.io/badge/Made%20with-Claude-D97757)](https://claude.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A few words of warning before you read on: **all the prices, model names and limits in this guide are accurate as of late April 2026.** Anthropic changes these things often, so please check [claude.com/pricing](https://claude.com/pricing) and the official docs before you make any architectural decision based on the numbers here.

---

## What's in this repository

```
.
├── README.md                  ← you're reading it (the main guide)
├── docs/
│   └── full-guide.md          ← same guide, kept separate for deep linking
├── examples/
│   ├── python/                ← runnable Python examples
│   └── typescript/            ← runnable TypeScript examples
├── tables/                    ← reference tables you can link to directly
│   ├── model-pricing.md
│   ├── plan-comparison.md
│   └── feature-cost-impact.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

**Where to start, depending on who you are:**

- **You just want to stop hitting the limit on Claude.ai?** Jump to [§3 Consumer guide](#3-consumer-guide). The rest is for developers.
- **You're building on the API?** Read [§6 Developer guide](#6-developer-guide-the-claude-api), then [§7 Prompt caching](#7-prompt-caching-deep-dive) and [§8 Batch API](#8-batch-api). The runnable code lives in [`examples/python`](examples/python) and [`examples/typescript`](examples/typescript).
- **You spend half your day in Claude Code?** Skip to [§11 Claude Code: token survival guide](#11-claude-code-token-survival-guide). It's where I lost the most money before I worked out what I was doing.

---

## TL;DR

If you read nothing else, read this:

**For consumer users:** the single thing that matters most is conversation length. Claude re-reads the entire chat on every turn, so a long conversation makes every reply progressively more expensive. Start new chats often, edit your messages instead of replying with corrections, use **Projects** to avoid re-uploading reference material, and turn off Extended Thinking, Web Search and Connectors when you're not actually using them. Pick Haiku for trivial tasks, Sonnet by default, Opus only when the task really benefits from it.

**For developers:** there are three big levers, and stacked together they get you to roughly 95% savings. **Prompt caching** (cache reads cost 10% of base input, pays for itself after a single read on the 5-minute TTL). **Batch API** (50% off everything, when the work isn't real-time). **Model routing** (Haiku $1/$5, Sonnet $3/$15, Opus $5/$25 per million tokens). On top of that, use `count_tokens` before you spend, set `max_tokens` explicitly, use the `effort` parameter and keep your thinking budgets tight.

**For Claude Code and Cowork users:** tokens build up in ways you don't notice. Every file read, every MCP tool, every CLAUDE.md re-injection sits in context for the rest of the session. Use `/clear` between unrelated tasks. Use `/compact` deliberately, with focus instructions, instead of letting auto-compaction kick in when the model is already drowning. Audit your MCP servers (each can add 1.5K to 18K tokens of overhead per turn). Keep CLAUDE.md under 200 lines. Use **Skills** so heavy reference material loads only when needed.

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
9. [Extended thinking and the `effort` parameter](#9-extended-thinking-and-effort)
10. [Tool use, vision, and PDFs](#10-tool-use-vision-pdfs)
11. [Claude Code: token survival guide](#11-claude-code-token-survival-guide)
12. [Real cost-savings worked examples](#12-real-cost-savings-worked-examples)
13. [Code examples (Python and TypeScript)](#13-code-examples)
14. [Comparison tables](#14-comparison-tables)
15. [Caveats and known issues](#15-caveats)

---

## 1. How Claude charges you (the mental model)

Everything in Claude (chat, Code, the API, Cowork) is priced in **tokens**. A token is roughly four English characters, or three quarters of a word. Two facts dominate every cost decision you'll ever make:

1. **The model has no memory.** Every turn re-sends the entire conversation as input. So a 14-token follow-up question on turn 30 actually costs you turns 1 through 30 in input tokens. I read a developer's writeup where the same 14-token question went from $0.0018 on turn 1 to about $2.41 on turn 260. That's a 1,339× increase, and all of it came from replayed history.
2. **Output costs roughly 5× input** on every current Claude model. Long responses, retries, and "rewrite the whole file please" are the most expensive things you can do.

Consumer plans turn this into a "usage limit" that resets every five hours, plus a weekly cap. API usage is billed per million tokens (MTok). When you use Claude Code while authenticated against a Pro or Max subscription, it draws from the same shared bucket as Claude.ai.

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
| Claude Opus 4 / 4.1 *(deprecated)* | $15.00 | $75.00 | - | - | - | 200K |
| Claude Haiku 3.5 *(legacy)* | $0.80 | $4.00 | - | - | - | 200K |

A few multipliers stack on top of these rates:

- **Batch API**: 0.5× on input *and* output. Half price.
- **Prompt caching**: writes cost 1.25× (5-min TTL) or 2.0× (1-h TTL); reads cost 0.1×.
- **`inference_geo` US-only routing** (Opus 4.6+): 1.1× across the board.
- **Fast mode** (Opus 4.6, beta research preview): 6× standard rates, and you can't combine it with Batch.
- **Long-context surcharge** on Sonnet 4.5 above 200K input tokens: 2× input and 1.5× output. Sonnet 4.6 and Opus 4.6/4.7 don't have this surcharge across the full 1M window.
- **Opus 4.7 tokenizer**: a new tokenizer that can produce up to about 35% more tokens for the same text. The per-token rate hasn't changed, but the effective cost of a request can go up by 0-35% versus 4.6. Benchmark on your own workload before you migrate.

### 2.2 Subscription plans (Claude.ai)

| Plan | Price | 5-hour rolling allowance (vs Pro) | Weekly cap | Models | Notes |
|---|---|---|---|---|---|
| **Free** | $0 | ~30-100 short messages/day, depending on demand | - | Sonnet 4.5/4.6 (limited), Haiku | No Claude Code; no Projects on legacy free; basic memory |
| **Pro** | $20/mo ($17/mo annual) | 1× (~45 short msgs / 5 h) | ~40-80 h Sonnet/week | Sonnet, Haiku, limited Opus | Includes Claude Code in terminal; Projects; Memory |
| **Max 5×** | $100/mo | 5× Pro | ~140-280 h Sonnet, 15-35 h Opus | + full Opus access | Includes Claude Code, Chrome, Cowork |
| **Max 20×** | $200/mo | 20× Pro | ~240-480 h Sonnet, 24-40 h Opus | All models | The heaviest individual plan |
| **Team Standard** | $30/seat (≥5 seats) | 1.25× Pro per seat | weekly cap | All except Opus by default | Admin controls, SSO |
| **Team Premium** | (higher per seat) | 6.25× Pro per seat at peak | dual weekly caps (all-models + Sonnet-only) | + Opus, Claude Code | Better burst headroom than Max 5× |
| **Enterprise** | Custom | Custom | Usage-based or seat-based | All, **500K context** on some, 1M on Opus 4.6+ in Code | SCIM, audit logs, data residency |

A few things worth knowing that aren't always obvious from the marketing pages:

- **All Claude products share one bucket.** claude.ai, Claude Desktop, Cowork, and Claude Code on Pro/Max all draw from the same usage limit. API usage is billed separately through the Console.
- **Sonnet and Opus have separate limits** on Max plans since November 2025. Burning through your Opus quota no longer blocks Sonnet (verified in Anthropic's Opus 4.5 release post; the help-center copy still describes them as "shared," so expect some documentation lag).
- **Extra usage** can be enabled in *Settings → Usage* on Pro/Max/Team. You keep working past the limit and pay standard API rates for the overage.
- **Peak vs off-peak**: limits drain faster on weekday mornings, roughly 5 a.m. to 11 a.m. Pacific.
- **Context window**: 200K tokens by default on all paid plans; 500K on some Enterprise models; 1M for Opus 4.6+ and Sonnet 4.6 inside Claude Code, on Max, Team Premium, and Enterprise.

---

## 3. Consumer guide

> If you're on claude.ai, the mobile app, or the desktop app and you just want to stop hitting that "you've reached your limit" wall, this section is the whole game. Skip the rest.

### 3.1 The most important habit, by far: edit, don't reply

When Claude gets it wrong, your first instinct is to type *"no, I meant..."* and explain. Don't. Hit the pencil icon on your original message instead, fix the prompt, and let it regenerate.

Why this matters: a chat is not a memory. Every time you send a new turn, Claude re-reads the entire conversation from the top. So when you reply with "no, try again," you've just made every future turn in that chat 30% more expensive, and you've kept the bad answer in context where it can poison the next one. Editing replaces. Replying accumulates.

I cannot stress this enough. If I had to pick one habit to teach a new Claude user, this would be it.

### 3.2 Your conversations are longer than you think

Some real numbers from a working session:

- Turn 1: a question costs you maybe 200 input tokens.
- Turn 30 of the same chat: that "yes, exactly" reply you just sent? It now costs 30 turns' worth of replayed history. Maybe 15,000 tokens. For a two-word reply.
- By turn 60 or 70, you're spending tens of thousands of tokens on every nothing-burger message.

What to do about it:

- **New topic, new chat. Always.** This is the cheapest fix in the entire guide. If you're switching from "help me draft an email" to "explain Kubernetes networking," that's two chats, not one.
- **Don't let chats run past 15-20 turns** if you can help it. The quality also degrades, Claude stops noticing things from earlier in the conversation, even though they're technically still in context.
- **The wrap-up trick:** at the end of a long session, ask Claude to summarise the important conclusions. Copy that summary, open a new chat, paste it as your first message. You've kept the useful state and dropped the dead weight.

Yes, the platform will eventually auto-summarise long chats for you. Don't rely on it. Auto-compaction kicks in when the model is already struggling, and the summary it generates is mediocre because it's being generated by a context-stuffed version of Claude. Take the wheel yourself.

### 3.3 One message, three questions

Three back-to-back prompts ("summarise this", "now bullet it", "now suggest a headline") cost you three full context replays. The same three questions in one prompt cost you one replay. Sounds obvious. Most people still don't do it.

### 3.4 Projects: use them properly

Projects are the most underused feature on the consumer side. Two reasons they save you money:

- Files you upload to a Project don't get re-paid every time you open a new chat inside it. They're loaded once, then reused.
- On paid plans, Projects use RAG when the knowledge base gets large. Claude pulls only the chunks relevant to your question instead of stuffing all your files into context. The effective capacity is about 10× a normal chat.

A few things I learned the hard way:

- Keep project **instructions** short. They get prepended to every message in the project. Whatever you write there, you pay for many times over.
- Clean up old files. Even if you don't reference them, they take up retrieval budget.
- One gotcha: RAG mode in Projects activates around 13 files, regardless of how big the files are. If you've got a project with 30 tiny files, RAG can produce weird hallucinations because it's only seeing a slice. Consolidate small files into fewer big ones if you want full direct loading.

### 3.5 Memory and Styles

**Memory** (Settings → Capabilities → Memory) builds a synthesis of who you are and what you're working on, refreshes it daily, and injects it into every new chat. Available on every plan, including Free.

**Styles** is the underrated cousin. Pick "Concise" or build your own, and it persists across chats without you having to retype "be brief" every time.

The catch with both: they add tokens to every single turn. Useful, but keep them tight. I've seen people with 22,000-word personal preferences files. That's not a memory, that's a small novel you're paying to re-read on every message. Aim for under 2,000 words.

If you want a one-off chat that doesn't pollute your synthesis, use **Incognito**. It skips memory entirely.

### 3.6 Things to switch off when you don't need them

Every feature in this table adds tokens to every response, every turn, until you turn it off:

| Feature | Roughly how much it costs you | Worth keeping on for |
|---|---|---|
| Extended Thinking | Tens of thousands of output tokens, billed | Hard maths, real research, multi-step planning |
| Web Search | Search content + result tokens | When the answer needs to be current |
| Research / Deep Research | The most expensive thing on the platform | Actual research projects, not Q&A |
| Connectors (Slack, Drive, etc.) | Tool descriptions on every turn | When you're actively using them right now |
| MCP connectors | Anywhere from 1.5K to 18K tokens per turn | Active use only |
| Files still attached to the chat | Re-encoded every turn | While they're still relevant |

My rule: everything off by default, switched on only for the specific task that needs it. Don't leave Web Search on "just in case."

### 3.7 Pick the right model

There's no prize for using the smartest model on every task. There's only a financial penalty.

- **Haiku 4.5** is fine for grammar, formatting, short questions, summarising, looking things up. Roughly five times cheaper than Sonnet.
- **Sonnet 4.6** is your default for most things: writing, analysis, coding, research. Near-Opus quality on most tasks.
- **Opus 4.7** is for complex reasoning, large codebases, agentic work, anything where instruction-following needs to be exact (legal, brand voice, safety).

A rule of thumb: if Claude takes less than 30 seconds to reply, you don't need Opus. On Max plans, Opus eats your usage limit fastest, so save it for when it actually matters.

### 3.8 Attachments: the silent budget killers

A few numbers worth keeping in your head:

- One PDF page: roughly 1,500 to 3,000 tokens.
- A normal-sized image (1000×1000): around 1,300 tokens. On Opus 4.7, a high-res image can be three times that.
- A 500 KB research PDF: around 125,000 tokens. Half your free context budget on a single upload.

Two simple habits:

- If you only need the text from a PDF or screenshot, convert it to plain markdown before uploading. Saves thousands of tokens.
- Don't re-upload the same file in the same chat. Claude already has it.

### 3.9 Different surfaces, very different costs

Not all Claude products cost the same per task:

- **Cowork (the desktop app)** is by far the most token-intensive. A single "clean up my Downloads folder" can spin up an autonomous loop that burns thousands of tokens per minute. My pattern: plan in regular chat, switch to Cowork only for the actual execution.
- **Artifacts and file creation** cost more than plain chat. Plan in chat, generate the artifact at the end.
- **Claude Code** is great for code, but agentic teammates (multiple subagents working in parallel) can use seven times the tokens of a single-agent session. Worth knowing before you turn them all on.

### 3.10 How to actually see what you've used

- **claude.ai → Settings → Usage** shows your current 5-hour and weekly usage, with a separate bar for Opus on Max.
- In Claude Code, type `/usage` to see per-session token counts (and cost, if you're on the API).
- For something always-visible, there's a third-party Chrome extension called *Claude Usage* (`cfranci/claude-usage-extension` on GitHub) that puts a coloured percentage badge in your toolbar. Useful for reality-checking.
- API users: **Anthropic Console → Usage**, plus admin export on Team and Enterprise plans.

---

## 4. Claude Desktop (Cowork)

Cowork is Anthropic's agentic file-management thing inside the Claude Desktop app. Under the hood it's the same loop as Claude Code, running in a sandboxed micro-VM with filesystem access.

The truth nobody tells you upfront: Cowork is dramatically more token-intensive than chat. A single "clean up my downloads" prompt can run an autonomous plan/execute/re-plan loop that produces thousands of input and output tokens in a couple of minutes. Heavy sessions also start to degrade after about 30 minutes of continuous work.

Some habits that make a real difference:

- **Plan first in regular chat**, then move the agreed plan into Cowork for execution. This alone saves you a lot.
- **Keep a `memory.txt` or `session-notes.md`** in your working folder, and tell Cowork to log progress to it. New sessions read the file instead of replaying history.
- **Trim the "about me" / project context** Cowork reads at session start. Under 2,000 words is a healthy upper bound.
- **Disable connectors you don't need** in the Cowork session. They add tool definitions to every turn.
- **Schedule heavy tasks for off-peak hours.** Cowork shares the Claude.ai bucket and drains faster on weekday mornings.

---

## 5. Claude in Chrome

The Chrome extension (Pro and up; Pro gets Haiku 4.5 only, Max/Team/Enterprise get the full model picker) automates browser tasks. Some cost notes:

- The extension takes screenshots of the active tab to "see" the page. Every screenshot is a vision input, around 1,300+ tokens for a typical screen.
- Workflows usually involve multiple tabs and multiple steps. One approval-then-execute run can rival a Cowork session in tokens.
- **Save your best prompts as shortcuts** (type `/` in chat) and reuse them instead of rewriting.
- **Disable the extension on sites where you don't need it** so it's not capturing screenshots in the background.
- For Claude Code + Chrome (the developer integration via `/chrome`), the same principles apply: be specific about which console-log patterns to look at, rather than asking for "show me all errors."

---

## 6. Developer guide: the Claude API

### 6.1 Five rules that solve 90% of cost problems

1. **Cache anything that repeats.** System prompts, tool definitions, big documents, conversation prefix.
2. **Batch anything that doesn't need a real-time answer.** Reports, evals, content generation.
3. **Route by complexity.** Haiku → Sonnet → Opus is a portfolio, not a tier ladder.
4. **Cap output.** Tight `max_tokens`, the `effort` parameter, stop sequences. All three.
5. **Measure first.** `count_tokens` and the response `usage` object. Don't optimise blind.

### 6.2 Choosing a model

- **Haiku 4.5** ($1/$5): classification, routing, extraction, moderation, simple Q&A. Five times cheaper than Sonnet on both axes.
- **Sonnet 4.6** ($3/$15): the production default. About 67% cheaper than legacy Sonnet, full 1M context at flat pricing, near-Opus quality on most tasks.
- **Opus 4.7** ($5/$25): complex coding agents, long-horizon tasks, instruction-precision work. Only 1.67× Sonnet, but the new tokenizer can push the effective cost up by as much as 35%.

A common production split is something like 60-70% Haiku, 25-30% Sonnet, 5-10% Opus, with a small router that decides based on input length, task type, or a quick Haiku classifier. It's worth building.

### 6.3 Counting tokens before you spend

Use `messages.count_tokens` to estimate every request before sending it. It supports `system`, `tools`, images, PDFs, and thinking. It's free, it has its own rate limit, and it's ZDR-eligible.

```python
import anthropic
client = anthropic.Anthropic()

response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="You are a senior code reviewer.",
    messages=[{"role": "user", "content": "Review this PR..."}],
)
print(response.json())  # {"input_tokens": 1234}
```

Runnable versions are in [`examples/python/04_token_counting.py`](examples/python/04_token_counting.py) and [`examples/typescript/src/04_token_counting.ts`](examples/typescript/src/04_token_counting.ts).

### 6.4 Context-window management

- Opus 4.7, Opus 4.6, and Sonnet 4.6 give you 1M tokens at flat pricing. Sonnet 4.5 is 200K (with a 1M beta that adds 2× input / 1.5× output above 200K).
- Haiku 4.5 is 200K. Don't try to scale Haiku into long-context workloads; you'll end up paying Sonnet rates anyway.
- Use `count_tokens` plus the `model_context_window_exceeded` stop reason to truncate or hand off cleanly.
- On Sonnet 4.6, Sonnet 4.5, and Haiku 4.5, **context-awareness** lets the model see how much budget it has left and finish gracefully.

### 6.5 System-prompt optimisation

- Put **stable** content (instructions, schemas, examples, RAG corpus) **before** dynamic content. Caching is a strict prefix cache: anything that changes invalidates everything after it.
- For RAG, put the retrieved chunks *before* the user's question, not after.
- **Compress** the system prompt: structured headers and bullets, no narrative. One independent benchmark showed a 63% output-token reduction just from adding a "reduce verbosity" rule.
- **Don't waste verbose few-shot examples on Haiku** unless you've measured that they help.
- Use the `system` parameter rather than the first user message, so it benefits from caching properly.

### 6.6 The `max_tokens` knob

- **Always set it.** The default behaviour has changed across model generations, and Claude 3.7+ enforces `prompt_tokens + max_tokens ≤ context_window` as a hard validation.
- Streaming is **required** when `max_tokens > 21,333`.
- For agentic loops with thinking, `max_tokens` has to be larger than `thinking.budget_tokens`.
- Always check `stop_reason`. If it's `"max_tokens"`, you cut off the output and you may have paid for an incomplete response.

### 6.7 Stop sequences

`stop_sequences` (up to 8,191 of them) lets the model stop at custom strings. Useful for structured output, terminating JSON, or stopping at section headers. Saves output tokens when you only need the first part of a long response.

### 6.8 Streaming vs non-streaming

- **Streaming** improves perceived latency (Time to First Token) and is required when `max_tokens > 21,333` or when extended thinking budgets are large.
- **Non-streaming** is simpler for batch-style work, and the Batch API requires it.
- The SDK throws errors on non-streaming requests that are expected to take more than about 10 minutes. If you need long output, either stream or use Batch.

---

## 7. Prompt caching deep dive

If you take only one technical change away from this guide, make it prompt caching. It's the single highest-ROI thing you can do to a Claude API integration.

### 7.1 How it actually works

You mark a content block with `cache_control: {"type": "ephemeral"}` (5-minute TTL) or `{"type": "ephemeral", "ttl": "1h"}` (1-hour TTL). The API stores an internal KV-cache representation of the *prefix up to and including that block*. Any subsequent request with the exact same prefix hits the cache.

A few things to know:

- **Cache writes** cost 1.25× base input on the 5-minute TTL, 2.0× on the 1-hour TTL.
- **Cache reads** cost 0.1× base input. A flat 90% discount on whatever portion was cached.
- **Pay-back**: caching pays for itself after one read on the 5-minute TTL, two reads on the 1-hour TTL. That's the bar.
- **Minimum cacheable size**: 1,024 tokens (Haiku 3 had 2,048; Haiku 4.5 follows the 1,024 standard). Anything shorter silently bypasses the cache and you won't be told.
- **Cache hierarchy**: `tools → system → messages`. Up to **4 cache breakpoints** per request.
- **How to verify**: the response `usage` object includes `cache_creation_input_tokens` and `cache_read_input_tokens`. If both are zero on what should be a cached call, you missed the minimum or the prefix changed.
- The cache is per-organisation and isolated. ZDR-eligible.

### 7.2 Automatic vs explicit caching

- **Automatic caching** (set `cache_control` once at the top level): the API picks breakpoints as conversations grow. Good for getting started, but only one breakpoint is chosen.
- **Explicit breakpoints**: place `cache_control` on individual content blocks. Required for agent loops where you want separate caches for tool definitions, system prompt, and message history checkpoints.

### 7.3 5-minute vs 1-hour TTL

- **5-minute TTL**: high-traffic prefixes that get hit constantly (chatbots, classifiers). Each read resets the TTL, so as long as traffic continues, the cache stays warm.
- **1-hour TTL**: shared static content across users, batch processing (which can take more than 5 minutes), agentic loops with multi-minute pauses. Higher write cost, but no compounding re-creation penalty.
- **A regression to be aware of (March 2026):** Anthropic silently changed the default TTL from 1 hour to 5 minutes, including in Claude Code. If you were relying on the old default, you're now paying full input price every time a session pauses past 5 minutes. The fix is to set `ttl` explicitly and audit your `cache_creation` vs `cache_read` ratio.

### 7.4 Cache-friendly architecture

- Static (cacheable) content first. Dynamic content last. This is the whole game.
- Working memory, runtime variables, per-user state must sit *after* the last breakpoint, otherwise you'll invalidate the prefix.
- For multi-step agents: place a breakpoint after `tools`, after the system prompt, and intermediate breakpoints every ~18 message blocks. The docs note that with more than 20 content blocks before a breakpoint, edits to early blocks won't hit the cache.
- **Disable extended thinking on caching-critical paths if you're on third-party providers.** Bedrock/Vertex behaviour is inconsistent. On Anthropic direct, thinking blocks cache cleanly on Opus 4.5+ and Sonnet 4.6+ but get stripped on earlier models.

### 7.5 Caching for RAG

Cache the system prompt plus the retrieved-document context block. Each user query then only re-bills the question itself. A 50K-token knowledge base queried 1,000 times per day on Sonnet 4.6:

- **No cache**: 1,000 × 50K × $3/MTok = **$150/day** in input.
- **With 5-minute cache, ~80% hit rate**: about $15/day. A 90% reduction on the cached portion.

### 7.6 Caching tool definitions

Tool definitions live in the cacheable region (before `system` and `messages`). MCP tool schemas in particular are huge, 1.5K to 8K tokens for a typical server, up to 18K with several. Cache them once and forget about them.

---

## 8. Batch API

### 8.1 What it is and when to use it

- **Asynchronous processing** of up to 10,000 (sometimes 100,000) requests per batch, returned within 24 hours. Most batches actually finish in under an hour.
- **50% off both input and output tokens.** Every model.
- **Stacks with prompt caching.** Anthropic's own engineers have shown combined effective discounts of 90-95%.
- A beta worth knowing about: **300K-token output extension** (`output-300k-2026-03-24`) for book-length single-message generations. Batch-only.
- Higher rate-limit ceilings than the synchronous API.
- You can mix any models, parameters and beta flags in a single batch.

### 8.2 Use it for

- Document and data processing pipelines.
- Nightly evals, red-team runs, model comparisons.
- Bulk content generation (SEO articles, product descriptions, classification).
- Large extractions, summarisation corpora, migrations.

### 8.3 Don't use it for

- Anything user-facing in real time.
- Workflows with sub-minute SLAs.
- Fast-mode workloads (incompatible with Batch).

### 8.4 Combining it with caching

Because batches can take longer than 5 minutes, use the **1-hour cache TTL** on shared prefixes. Repeated cache writes inside a batch are otherwise the most common over-spend I see.

End-to-end runnable example: [`examples/python/03_batch_api.py`](examples/python/03_batch_api.py).

---

## 9. Extended thinking and `effort`

### 9.1 Extended thinking

- Reasoning tokens are billed as **output tokens** at standard rates.
- The minimum budget is **1,024 tokens**. The default budgets in some clients (notably Claude Code) can reach tens of thousands per request.
- On Opus 4.5+ and Sonnet 4.6+, previous-turn thinking blocks are kept and *count toward context*. On earlier Opus/Sonnet and on all Haiku, they're stripped. Plan accordingly.
- Streaming is required for `max_tokens > 21,333`.
- Thinking changes invalidate cache breakpoints in messages.

### 9.2 Adaptive thinking (Opus 4.6/4.7, Sonnet 4.6)

`thinking: {"type": "adaptive"}` lets the model decide whether to think and how much, based on prompt difficulty. Replaces manual `budget_tokens`. **My recommended default**: cheaper than always-on, and it doesn't sacrifice quality on hard prompts.

### 9.3 The `effort` parameter

`effort: "low" | "medium" | "high" | "max"` controls overall token spend (text + tool calls + thinking).

- **`low`**: latency-sensitive chat, simple Q&A. Fewer tool calls, shorter responses.
- **`medium`** (recommended for most production): a solid balance.
- **`high`** (the default): default behaviour, equivalent to omitting the parameter.
- **`max`**: highest capability. For tasks where quality is more important than money.

`effort` works without thinking enabled, by the way. It modulates plain output too. Use `low` to cut costs on Sonnet 4.6 chat workloads where the quality is already plenty.

### 9.4 Task budgets (Opus 4.7 beta)

Opus 4.7 supports `task_budget`, an advisory token budget across an entire agentic loop (thinking, tool calls, tool results, final output). The model sees a running countdown and prioritises its work accordingly.

---

## 10. Tool use, vision, PDFs

### 10.1 Tool-use overhead

Whenever you provide **any** tool, Anthropic adds a hidden tool-use system prompt:

| Tool category | Approx. extra system-prompt tokens |
|---|---|
| Generic `tools` array (≥1 tool) | model-specific (typically 200-800) |
| `bash` tool | +245 |
| `computer_use` tool | +466-499 + per-screenshot vision tokens |
| Multi-server MCP setup | 1,500-18,000 per turn (audit your config) |

There is **no cross-turn caching of tool definitions at the API level by default.** Every request pays the full overhead unless you put a `cache_control` breakpoint after the `tools` block. For MCP-heavy agents, this is the single most common correctable inefficiency.

### 10.2 Server tools with separate fees

- **Web search**: $10 per 1,000 searches, plus tokens for the content.
- **Web fetch**: standard token cost only. An average page is around 2,500 tokens, a large doc 25,000, a big PDF 125,000. Use `max_content_tokens` to cap.
- **Code execution**: free when used together with web search/fetch; otherwise billed by container-hour.

### 10.3 Vision pricing

- Token cost is roughly `width × height / 750` per image, capped per model.
- Standard models: max 1,568 px on the long edge, so up to about 1,568 tokens.
- **Opus 4.7**: max 2,576 px, up to 4,784 tokens. About 3× the standard. 1:1 pixel mapping for computer use.
- 600 images per request on 1M-context models, 100 on 200K-context models.
- **Pre-resize.** Downsample any image where text or layout fidelity isn't critical. A 682×318 image costs about 314 tokens; a 3456×2234 image costs over 3,000 tokens on Opus 4.7. The ratio matters.

### 10.4 PDFs

PDFs are billed per page as a mix of text and image tokens. A 30-page text-heavy PDF runs about 56K tokens on Opus 4.6 and 61K on Opus 4.7. A few strategies:

- Extract text client-side and send markdown when you only need the text.
- Use the Files API plus cached document blocks to reuse the same PDF across many queries.
- Combine with prompt caching: cache a 100-page legal doc once, query it dozens of times at 10% rate.

---

## 11. Claude Code: token survival guide

### 11.1 Subscription vs API for Claude Code

| Pattern | Best fit |
|---|---|
| Daily, full-workday use | **Pro** ($20) → **Max 5×** ($100) → **Max 20×** ($200). A flat fee is usually 2-3× cheaper than the equivalent API spend |
| Bursty, intensive sessions | Team Premium seat (6.25× Pro per session, even more headroom than Max 5×) |
| Pay-as-you-go automation, CI/CD | API key (set workspace spend limits in the console) |

Some real numbers (Anthropic plus community estimates):

- Pro user: ~10-40 prompts per 5-hour window, 40-80 hours of Sonnet/week.
- Max 5×: ~50-200 prompts/window, 140-280 h Sonnet, 15-35 h Opus.
- Max 20×: ~200-800 prompts/window, 240-480 h Sonnet, 24-40 h Opus.
- One developer reported 10 billion tokens over 8 months. That's about $15K of API usage versus $800 on Max ($100 × 8). A 93% saving.
- Enterprise average: about $13/dev per active day, $150-250/dev/month.

### 11.2 The four habits that actually work

1. **`/clear` aggressively.** Switching tasks? Clear. The old conversation lives in input on every turn until you do.
2. **`/compact <focus>` deliberately, not reactively.** Auto-compaction fires when the context is at peak rot, and the summary it generates is poor because it's being made by the worst version of Claude. Use `/compact Focus on the API changes and the list of modified files` at logical breakpoints. You'll see the difference.
3. **Subagents for noisy work.** "Read these 12 files and tell me X", spin up a subagent, so the raw exploration stays in *its* context and only the conclusion comes back to you.
4. **`/rewind` (or Esc-Esc) instead of correcting.** A failed attempt plus corrections poisons the rest of the session. Roll back, re-prompt, move on.

### 11.3 CLAUDE.md best practices

- **Keep it under 200 lines.** Longer files reduce adherence and inflate every turn's input.
- The hierarchy: global `~/.claude/CLAUDE.md` for personal preferences; project-root for shared conventions; nested per-directory for path-scoped rules.
- Project-root CLAUDE.md **survives compaction** (re-read from disk after `/compact`). Nested files reload only when Claude touches matching paths.
- Be **specific to actual failure modes**, not generic. "When a step fails, stop and report the full traceback before fixing" is much more useful than "be careful."
- Don't duplicate skill content. Skills load on demand; CLAUDE.md loads always.

### 11.4 Skills: the underused token saver

Skills are markdown files (`SKILL.md`) loaded *only* when invoked. The startup cost is just the 1-2 line description in the system prompt; the full content is fetched lazily via Bash when triggered.

- Use skills for **specialised procedural knowledge** (deployment runbooks, API conventions, debug playbooks) that you'd otherwise paste into prompts repeatedly.
- Skills compose with caching. Once invoked, skill content is cache-stable, so subsequent turns pay 10% rates.
- After auto-compaction, Claude Code re-attaches the most recent invocation of each skill, keeping the first 5,000 tokens (combined budget 25,000 across skills).
- Anthropic ships bundled skills (`/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`); the community library `antigravity-awesome-skills` bundles 1,200+.
- **Audit installed skills and plugins.** A 2026 community report (GitHub issue #29971) documented setups where 49 plugins were registered, only 3 were actually being used, and 25K tokens of skill metadata was wasted per tool call.

### 11.5 Tame your MCP servers

Each MCP server injects its full tool schema into every turn. Typical numbers: 1,500-4,000 tokens per server, up to 8,000 with rich documentation, totalling 18K+ tokens with several servers connected.

- Run `/context` mid-session to see the live overhead.
- Disable unused servers per project (project-level `.claude/settings.json`).
- Trim tool descriptions in servers you control.
- Use **context-mode** style MCPs that index tool outputs into a sandbox knowledge base, instead of dumping JSON straight into context.

### 11.6 Other Claude Code tips

- **Plan Mode** (Shift+Tab) before multi-file changes. Cheaper to plan than to recover from going the wrong way.
- **Diff output, not full files.** "Give me the changes as a diff" saves thousands of output tokens.
- **Specific line ranges**, not whole files. "Look at auth.ts lines 42-58" beats pasting the whole file.
- **Batch edits in one prompt.** "Add error handling to functions A, B, C, D" beats four prompts.
- **`MAX_THINKING_TOKENS=8000`** as an environment variable lowers the default extended-thinking budget for non-critical sessions.
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

Savings: about 90% on caching alone, about 95% with caching plus Batch.

### 12.2 Batch API on 1M tokens (Sonnet 4.6, 70/30 input/output split)

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

Routing to Haiku saves you 80%. 90% with Batch on top.

### 12.4 Monthly scenario costs (Sonnet 4.6 unless noted)

| Scenario | Volume | Naive cost | Optimised cost | Strategy |
|---|---|---|---|---|
| Customer-support chatbot | 50K conv/mo, 2K in / 500 out | $4,500 | **~$1,200** | 5K-token cached system prompt (1-h TTL), 70/25/5 Haiku/Sonnet/Opus routing |
| Coding assistant | 10K sessions, 50K in / 15K out | $7,500 + $3,750 = **$11,250** | **~$3,000** | Cache repo digest, Sonnet by default + Opus only for hard cases |
| Document analysis | 20K docs, 10K in / 1K out | $300 (Sonnet) | **~$150** | Batch API + 1-h cache on per-doc system instructions |
| SEO content generation | 20M in / 10M out (Haiku 4.5) | $70 | **$35** | Haiku 4.5 + Batch API |
| RAG over 200K docs | 100 queries/h | $200/day | **~$30/day** | Cache the corpus, 1-h TTL, Sonnet 4.6 |
| Solo dev on Claude Code | Heavy daily use | API ~$400-1,200/mo | **$100-200/mo** | Max 5× / 20× subscription instead of API |

---

## 13. Code examples

All examples in this guide are available as **runnable scripts**:

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

Standalone reference tables also live in [`tables/`](tables) for easier copying or linking.

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
| Adaptive Thinking | Auto-skips on simple questions, engages on hard ones (recommended) |
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

A few things worth being honest about:

- **Pricing and limits change often.** Anthropic launched Opus 4.7 on 16 April 2026, and shifted the default cache TTL from 1 hour to 5 minutes in March 2026 with no announcement. Always cross-check `claude.com/pricing` and the response `usage` object before relying on a specific number from this guide.
- **The Opus 4.7 tokenizer change** can raise the effective cost by up to about 35% on the same workload, even though the headline pricing is identical. Run a representative traffic sample before you migrate from 4.6.
- **Plan multipliers are not the same as absolute token counts.** Anthropic deliberately doesn't publish exact tokens-per-window figures for Pro/Max/Team. Third-party estimates (e.g. "Pro ≈ 44K tokens / 5 h") come from reverse-engineering, not from Anthropic. Treat them as directional only.
- **Sonnet vs Opus limits on Max**: Anthropic's November 2025 announcement implied separate caps for Sonnet and Opus, while help-center copy still says "shared." In practice it behaves like separate limits, but Anthropic hasn't consolidated the documentation as of April 2026.
- **The "Claude is getting dumber" complaints** in early 2026 are largely down to the cache-TTL regression, not model regression. Independent benchmarks show stable model quality; cache misses just made the same work feel more expensive and slower.
- **Cowork is a research preview** and shares its budget with regular Claude usage. It's the most token-intensive surface; treat it as such.
- **Free-tier capacity varies with system load.** "30-100 messages/day" is approximate and can be lower during peak demand.
- **The community workarounds for memory and compaction** (handoff files, manual summaries, restarts) reflect real tradeoffs in Anthropic's system, not user error. Expect to keep using them for now.
- **Batch API rate limits** apply to both HTTP requests and in-flight batch requests. Very large batches can be paced down during high-demand periods.
- **Some tools and features stack in non-obvious ways.** Fast mode is incompatible with Batch. Cache invalidation cascades: change a single token in the cached prefix and you re-pay the full write. Extended thinking changes invalidate message-level caches.
- **Third-party providers (Bedrock, Vertex, Foundry) behave differently from the Anthropic direct API** when it comes to caching and thinking. Verify on your target before you commit.

---

## 🤝 Contributing

Spotted outdated pricing, a new feature, or a better strategy? PRs are welcome. Have a look at [CONTRIBUTING.md](CONTRIBUTING.md) first. Please cite primary Anthropic sources (`platform.claude.com`, `support.claude.com`, official Anthropic blog posts) when you propose changes.

## 📜 License

[MIT](LICENSE). Use it freely; attribution is appreciated but not required.

## 🙏 Acknowledgements

Pricing and feature claims verified against Anthropic's public docs (`platform.claude.com`, `support.claude.com`, `code.claude.com`) and Anthropic blog/release posts current as of 30 April 2026.

---

*This is a community resource and is **not** affiliated with or endorsed by Anthropic.*
