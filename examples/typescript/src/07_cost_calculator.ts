/**
 * 07 - Cost calculator CLI
 * ========================
 *
 * Standalone, no API key required. Estimates cost from token counts.
 *
 * Examples:
 *
 *   npx tsx src/07_cost_calculator.ts --model claude-sonnet-4-6 --input 10000 --output 500
 *   npx tsx src/07_cost_calculator.ts --compare --input 10000 --output 500
 *   npx tsx src/07_cost_calculator.ts --model claude-sonnet-4-6 \
 *     --input 500 --cache-read 9500 --output 500
 */

// (input, output, cache_write_5m, cache_write_1h, cache_read) per 1M tokens, USD.
// Verified against claude.com/pricing on 30 Apr 2026.
const PRICES: Record<string, [number, number, number, number, number]> = {
  "claude-opus-4-7":   [5.0, 25.0, 6.25, 10.0, 0.5],
  "claude-opus-4-6":   [5.0, 25.0, 6.25, 10.0, 0.5],
  "claude-sonnet-4-6": [3.0, 15.0, 3.75,  6.0, 0.3],
  "claude-sonnet-4-5": [3.0, 15.0, 3.75,  6.0, 0.3],
  "claude-haiku-4-5":  [1.0,  5.0, 1.25,  2.0, 0.1],
  "claude-haiku-3-5":  [0.8,  4.0, 1.0,   1.6, 0.08],
};

interface Args {
  model: string;
  input: number;
  output: number;
  cacheRead: number;
  cacheWrite5m: number;
  cacheWrite1h: number;
  batch: boolean;
  compare: boolean;
}

function cost(model: string, a: Omit<Args, "model" | "compare">): number {
  if (!PRICES[model]) {
    throw new Error(`Unknown model: ${model}. Try: ${Object.keys(PRICES).join(", ")}`);
  }
  const [pIn, pOut, pW5, pW1, pR] = PRICES[model];
  let total =
    (a.input * pIn +
      a.output * pOut +
      a.cacheWrite5m * pW5 +
      a.cacheWrite1h * pW1 +
      a.cacheRead * pR) /
    1_000_000;
  if (a.batch) total *= 0.5;
  return Math.round(total * 1_000_000) / 1_000_000;
}

function parseArgs(argv: string[]): Args {
  const out: Args = {
    model: "claude-sonnet-4-6",
    input: 0,
    output: 0,
    cacheRead: 0,
    cacheWrite5m: 0,
    cacheWrite1h: 0,
    batch: false,
    compare: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = argv[i + 1];
    switch (a) {
      case "--model":           out.model = next!; i++; break;
      case "--input":           out.input = parseInt(next!, 10); i++; break;
      case "--output":          out.output = parseInt(next!, 10); i++; break;
      case "--cache-read":      out.cacheRead = parseInt(next!, 10); i++; break;
      case "--cache-write-5m":  out.cacheWrite5m = parseInt(next!, 10); i++; break;
      case "--cache-write-1h":  out.cacheWrite1h = parseInt(next!, 10); i++; break;
      case "--batch":           out.batch = true; break;
      case "--compare":         out.compare = true; break;
      case "--help":
      case "-h":
        console.log(`Usage: tsx 07_cost_calculator.ts [options]

  --model NAME         Model name (default: claude-sonnet-4-6)
  --input N            Fresh input tokens
  --output N           Output tokens
  --cache-read N       Cache-read tokens (90% off)
  --cache-write-5m N   5-min cache-write tokens (1.25x)
  --cache-write-1h N   1-h cache-write tokens (2.0x)
  --batch              Apply 50% Batch API discount
  --compare            Show cost across all models
  --help               This message

Models: ${Object.keys(PRICES).join(", ")}
`);
        process.exit(0);
    }
  }
  return out;
}

function main(): void {
  const args = parseArgs(process.argv.slice(2));
  const params = {
    input: args.input,
    output: args.output,
    cacheRead: args.cacheRead,
    cacheWrite5m: args.cacheWrite5m,
    cacheWrite1h: args.cacheWrite1h,
    batch: args.batch,
  };

  if (args.compare) {
    console.log(`${"Model".padEnd(22)} ${"Cost (USD)".padStart(12)}`);
    console.log("-".repeat(36));
    for (const m of Object.keys(PRICES)) {
      console.log(`${m.padEnd(22)} ${cost(m, params).toFixed(6).padStart(12)}`);
    }
  } else {
    const usd = cost(args.model, params);
    const [pIn, pOut, , , pR] = PRICES[args.model];
    console.log(`Model      : ${args.model}`);
    console.log(`Input      : ${args.input.toString().padStart(10)}  (${pIn.toFixed(2)}/MTok)`);
    console.log(`Output     : ${args.output.toString().padStart(10)}  (${pOut.toFixed(2)}/MTok)`);
    if (args.cacheRead) console.log(`Cache read : ${args.cacheRead.toString().padStart(10)}  (${pR.toFixed(2)}/MTok)`);
    if (args.cacheWrite5m) console.log(`5m write   : ${args.cacheWrite5m.toString().padStart(10)}`);
    if (args.cacheWrite1h) console.log(`1h write   : ${args.cacheWrite1h.toString().padStart(10)}`);
    if (args.batch) console.log("Batch API  : applied (50% off)");
    console.log(`\nEstimated cost: $${usd.toFixed(6)} USD`);
  }
}

main();
