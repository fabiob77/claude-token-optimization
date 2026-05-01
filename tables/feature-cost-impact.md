# Feature cost impact

> A quick reference for what each feature does to your token budget. See the [main guide](../README.md) for the full strategy.

## Consumer features (Claude.ai, Pro, Max, Team)

| Feature | Effect on token spend | When to use it |
|---|---|---|
| Editing your original message vs replying with "no, try again" | Edit *replaces* history (cheaper); reply *appends* and compounds | Always prefer edit |
| Starting a new chat | Resets ~5K+ tokens of system overhead per turn | Every unrelated topic |
| Projects (paid plans) | RAG retrieves only relevant chunks → ~10× capacity | Reusable reference material |
| Memory feature | +~hundreds of tokens per turn for the synthesis | Helpful, but trim |
| Styles | +tens of tokens per turn (cheap, useful) | "Concise" style for chatty users |
| Personal preferences (Settings) | +some tokens per turn | A short "about me" — keep < 2,000 words |
| Incognito chats | No memory injected | One-off sessions you don't want remembered |

## Power-user toggles

| Feature | Per-response cost | When to leave on |
|---|---|---|
| Extended Thinking (manual) | +1K to 60K+ output tokens | Hard math / planning |
| Adaptive Thinking | Auto-skips on simple Qs | Recommended default |
| Web Search | $10 / 1K searches + content tokens | When facts must be current |
| Research / Deep Research | Highest per-task cost on the platform | True research projects |
| Connectors (Slack, GDrive, …) | Tool descriptions on every turn | Active use only |
| MCP connectors | +1.5K–8K tokens/server/turn (up to 18K with several) | Active use only |
| Each PDF page in chat | ~1.5K–3K tokens | Re-encoded every turn while in context |
| Each high-res image (Opus 4.7) | up to 4,784 tokens | Pre-resize when text/layout matters |
| File still attached to the chat | Re-encoded every turn | Remove when done |

## Developer / API levers

| Lever | Effect | Notes |
|---|---|---|
| Prompt caching, cache reads | -90% on cached input tokens | 1,024-token minimum; 4 breakpoints max per request |
| Cache writes (5-min TTL) | +25% over base input | Pays back after one read |
| Cache writes (1-h TTL) | +100% over base input | Pays back after two reads |
| Batch API | -50% on input + output | 24-h SLA; non-streaming only |
| Caching + Batch combined | up to -95% | The headline cost-saving stack |
| `count_tokens` | Free; estimate before sending | Use in CI to catch ballooning prompts |
| `max_tokens` | Caps output | Required >21,333 to stream |
| `effort: "low"` | Fewer tool calls + thinking + output | Chat-style workloads |
| `thinking={"type": "adaptive"}` | Model decides when/how much to think | Cheaper than always-on |
| `stop_sequences` | Trim long responses early | Up to 8,191 entries |

## Server tools & sub-services

| Tool | Token overhead | Extra fee |
|---|---|---|
| Generic `tools` array (≥1 tool) | 200–800 system tokens | — |
| `bash` tool | +245 system tokens | — |
| `computer_use` tool | +466–499 + per-screenshot vision tokens | — |
| Web search (server tool) | +tokens for results | $10 / 1K searches |
| Web fetch | average page ~2,500 tokens | — |
| Code execution | container-hour billing when used standalone | — |

## Claude Code specifics

| Lever | Effect |
|---|---|
| `/clear` between unrelated tasks | Resets the conversation |
| `/compact <focus>` deliberately | Better summary than auto-compaction |
| Subagents | Keep noisy reads out of main context |
| `/rewind` (Esc-Esc) | Cheaper than corrections |
| CLAUDE.md under 200 lines | Inflates every turn otherwise |
| Skills (lazy-loaded) | Only the description is in the system prompt by default |
| Audit MCP servers | Each adds 1.5K–8K tokens/turn; many add 18K+ |
| `MAX_THINKING_TOKENS` env var | Lower default thinking budget |
| Plan Mode (Shift+Tab) | Plan once, not 3× recovery |
| Diff output, not full files | Cuts thousands of output tokens |
