# Subscription plan comparison

> Verified against [claude.com/pricing](https://claude.com/pricing) and [Claude Help Center](https://support.claude.com) on 30 April 2026. Anthropic deliberately doesn't publish exact tokens-per-window figures for Pro/Max/Team — third-party estimates are directional only.

## Quick comparison

| Plan | Price | Multiplier vs Pro | Models | Claude Code | Cowork | Chrome ext. | Notes |
|---|---|---|---|---|---|---|---|
| **Free** | $0 | — | Sonnet (limited), Haiku | ❌ | ❌ | ❌ | ~30–100 short msgs/day, varies with demand |
| **Pro** | $20/mo ($17/mo annual) | 1× (~45 short msgs / 5 h) | Sonnet, Haiku, limited Opus | ✅ terminal | ✅ | ✅ Haiku-only | Includes Projects + Memory |
| **Max 5×** | $100/mo | 5× Pro | All models, full Opus | ✅ | ✅ | ✅ all models | ~140–280 h Sonnet, 15–35 h Opus per week |
| **Max 20×** | $200/mo | 20× Pro | All models | ✅ | ✅ | ✅ all models | Heaviest individual plan |
| **Team Standard** | $30/seat (≥5 seats) | 1.25× Pro/seat | All non-Opus by default | ❌ | ✅ | ✅ | SSO, admin controls |
| **Team Premium** | (higher seat) | 6.25× Pro/seat at peak | + Opus, + Claude Code | ✅ | ✅ | ✅ | Dual weekly caps (all-models + Sonnet-only) |
| **Enterprise** | Custom | Custom | All + 500K context (some), 1M (Opus 4.6+) | ✅ | ✅ | ✅ | SCIM, audit logs, data residency |

## How limits actually work

- **Rolling 5-hour window** + **weekly cap.** When you send a message, the 5-hour timer starts; subsequent messages count against that window until it resets.
- **All Claude surfaces share one bucket.** claude.ai, the iOS/Android app, Claude Desktop, Cowork, and Claude Code on Pro/Max all draw from the same usage limit. **API usage is billed separately** through the Console.
- **Sonnet vs Opus on Max** have separate limits since Anthropic's November 2025 update — burning through Opus no longer blocks Sonnet (the public help-center copy still describes them as "shared," so expect documentation lag).
- **Extra usage** is available in *Settings → Usage* on Pro / Max / Team — keep working past the limit and pay standard API rates for the overage.
- **Peak/off-peak**: limits deplete faster on weekdays 5 a.m.–11 a.m. Pacific.

## Context windows

| Plan | Default | Long-context |
|---|---|---|
| Free / Pro / Team Standard | 200K | — |
| Max / Team Premium | 200K | 1M for Opus 4.6+/Sonnet 4.6 in Claude Code |
| Enterprise | 500K (some models) | 1M for Opus 4.6+/Sonnet 4.6 in Claude Code |

## Choosing between Pro, Max, Team Premium

| If you… | Pick |
|---|---|
| Use Claude casually a few times a day | **Pro** |
| Use Claude Code most days for ≤ ~3–4 hours | **Pro** |
| Run intensive Claude Code sessions daily, occasional 200K-context work | **Max 5×** |
| Are a heavy individual user, multi-hour Code sessions, frequent Opus usage | **Max 20×** |
| Have 5+ devs and want SSO and centralised billing | **Team Standard** or **Team Premium** |
| Need org-wide audit, SCIM, residency | **Enterprise** |

> **Rough rule of thumb:** if you'd otherwise spend more than ~3× the plan price on the API, the plan wins. One developer reported $15K of API-equivalent Claude Code usage costing $800 on Max over 8 months — a 93% saving.
