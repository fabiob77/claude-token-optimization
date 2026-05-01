# Model pricing reference

> Per 1 million tokens, USD. Verified against [claude.com/pricing](https://claude.com/pricing) on 30 April 2026. Confirm before relying on numbers — Anthropic ships pricing changes regularly.

| Model | Input | Output | Cache read (90% off) | 5-min cache write | 1-h cache write | Batch input | Batch output | Context |
|---|---|---|---|---|---|---|---|---|
| **Claude Opus 4.7** | $5.00 | $25.00 | $0.50 | $6.25 | $10.00 | $2.50 | $12.50 | 1M |
| Claude Opus 4.6 | $5.00 | $25.00 | $0.50 | $6.25 | $10.00 | $2.50 | $12.50 | 1M |
| **Claude Sonnet 4.6** | $3.00 | $15.00 | $0.30 | $3.75 | $6.00 | $1.50 | $7.50 | 1M |
| Claude Sonnet 4.5 | $3.00 | $15.00 | $0.30 | $3.75 | $6.00 | $1.50 | $7.50 | 200K (1M beta with surcharge) |
| **Claude Haiku 4.5** | $1.00 | $5.00 | $0.10 | $1.25 | $2.00 | $0.50 | $2.50 | 200K |
| Claude Haiku 3.5 (legacy) | $0.80 | $4.00 | $0.08 | $1.00 | $1.60 | $0.40 | $2.00 | 200K |
| Claude Opus 4 / 4.1 (deprecated) | $15.00 | $75.00 | — | — | — | $7.50 | $37.50 | 200K |

## Multipliers that stack

| Modifier | Effect |
|---|---|
| Batch API | × 0.5 on input + output (50% off) |
| Cache write, 5-min TTL | × 1.25 of base input |
| Cache write, 1-h TTL | × 2.0 of base input |
| Cache read | × 0.10 of base input (90% off) |
| `inference_geo` US-only routing (Opus 4.6+) | × 1.1 |
| Fast mode (Opus 4.6, beta) | × 6 — **incompatible with Batch** |
| Long-context surcharge (Sonnet 4.5 above 200K input) | × 2 input / × 1.5 output |
| Opus 4.7 tokenizer | up to +35% effective tokens vs Opus 4.6 (per-token rate unchanged) |

## Pay-back math for caching

- **5-min TTL (1.25× write, 0.10× read):** breaks even after **1 cache read**.
- **1-h TTL (2.0× write, 0.10× read):** breaks even after **2 cache reads**.

Stack with Batch: combined effective discount can reach **~95%** vs naive synchronous calls.
