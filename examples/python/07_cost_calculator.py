"""
07 - Cost calculator CLI
========================

Standalone script. No API key needed. Estimates cost from token counts.
Use it offline to:

- Sanity-check budgets before deploying.
- Compare scenarios (cached vs uncached, batch vs sync, model vs model).
- Confirm what a Usage object actually cost you after a run.

Examples:

    # Cost of one Sonnet 4.6 call: 10K input, 500 output
    python 07_cost_calculator.py --model claude-sonnet-4-6 --input 10000 --output 500

    # Same call, but 9.5K of the input was a cache read (90% off)
    python 07_cost_calculator.py --model claude-sonnet-4-6 \\
        --input 500 --cache-read 9500 --output 500

    # Compare across all models
    python 07_cost_calculator.py --compare --input 10000 --output 500

    # Daily total: 1,000 calls, 5K input each, 200 output, 80% cache hit
    python 07_cost_calculator.py --model claude-sonnet-4-6 \\
        --input 1000 --cache-read 4000000 --cache-write-5m 5000 \\
        --output 200000 --batch
"""

from __future__ import annotations

import argparse
import sys

# (input, output, cache_write_5m, cache_write_1h, cache_read) per 1M tokens, USD.
# Verified against claude.com/pricing on 30 Apr 2026.
PRICES = {
    "claude-opus-4-7":   (5.00, 25.00, 6.25, 10.00, 0.50),
    "claude-opus-4-6":   (5.00, 25.00, 6.25, 10.00, 0.50),
    "claude-sonnet-4-6": (3.00, 15.00, 3.75,  6.00, 0.30),
    "claude-sonnet-4-5": (3.00, 15.00, 3.75,  6.00, 0.30),
    "claude-haiku-4-5":  (1.00,  5.00, 1.25,  2.00, 0.10),
    "claude-haiku-3-5":  (0.80,  4.00, 1.00,  1.60, 0.08),
}


def cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_write_5m: int = 0,
    cache_write_1h: int = 0,
    cache_read: int = 0,
    batch: bool = False,
) -> float:
    if model not in PRICES:
        raise ValueError(f"Unknown model {model!r}. Try one of: {', '.join(PRICES)}")
    p_in, p_out, p_w5, p_w1, p_r = PRICES[model]
    total = (
        input_tokens     * p_in
        + output_tokens  * p_out
        + cache_write_5m * p_w5
        + cache_write_1h * p_w1
        + cache_read     * p_r
    ) / 1_000_000
    if batch:
        total *= 0.5
    return round(total, 6)


def main() -> int:
    parser = argparse.ArgumentParser(description="Estimate Claude API cost from token counts.")
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        choices=list(PRICES),
        help="Model name (default: claude-sonnet-4-6)",
    )
    parser.add_argument("--input", type=int, default=0, help="Fresh input tokens")
    parser.add_argument("--output", type=int, default=0, help="Output tokens")
    parser.add_argument("--cache-read", type=int, default=0, help="Cache-read tokens (90% off)")
    parser.add_argument("--cache-write-5m", type=int, default=0, help="5-min cache-write tokens (1.25x)")
    parser.add_argument("--cache-write-1h", type=int, default=0, help="1-h cache-write tokens (2.0x)")
    parser.add_argument("--batch", action="store_true", help="Apply 50% Batch API discount")
    parser.add_argument("--compare", action="store_true", help="Show cost across all models")
    args = parser.parse_args()

    kwargs = dict(
        input_tokens=args.input,
        output_tokens=args.output,
        cache_write_5m=args.cache_write_5m,
        cache_write_1h=args.cache_write_1h,
        cache_read=args.cache_read,
        batch=args.batch,
    )

    if args.compare:
        print(f"{'Model':<22} {'Cost (USD)':>12}")
        print("-" * 36)
        for model in PRICES:
            usd = cost(model, **kwargs)
            print(f"{model:<22} {usd:>12.6f}")
    else:
        usd = cost(args.model, **kwargs)
        print(f"Model      : {args.model}")
        print(f"Input      : {args.input:>10}  ({PRICES[args.model][0]:.2f}/MTok)")
        print(f"Output     : {args.output:>10}  ({PRICES[args.model][1]:.2f}/MTok)")
        if args.cache_read:
            print(f"Cache read : {args.cache_read:>10}  ({PRICES[args.model][4]:.2f}/MTok)")
        if args.cache_write_5m:
            print(f"5m write   : {args.cache_write_5m:>10}  ({PRICES[args.model][2]:.2f}/MTok)")
        if args.cache_write_1h:
            print(f"1h write   : {args.cache_write_1h:>10}  ({PRICES[args.model][3]:.2f}/MTok)")
        if args.batch:
            print("Batch API  : applied (50% off)")
        print(f"\nEstimated cost: ${usd:.6f} USD")
    return 0


if __name__ == "__main__":
    sys.exit(main())
