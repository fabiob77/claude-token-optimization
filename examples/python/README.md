# Python examples

Runnable companion code for the [main guide](../../README.md). Every script:

- uses the official [`anthropic`](https://pypi.org/project/anthropic/) SDK,
- prints the `usage` object so you can verify cache hits and Batch discounts yourself,
- assumes the **Anthropic direct API** (not Bedrock / Vertex), and
- targets current pricing as of April 2026.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env # then edit .env and add your real key
```

Get an API key at https://console.anthropic.com/. **Never commit `.env`.**

You can load the env file with `python-dotenv`:

```bash
pip install python-dotenv
```

…and then add `from dotenv import load_dotenv; load_dotenv()` to the top of any script, or just `export ANTHROPIC_API_KEY=sk-ant-…` for the session.

## Examples

| File | What it shows |
|---|---|
| `01_basic_caching.py` | Minimal prompt caching, prints `cache_creation_*` vs `cache_read_*` usage so you can see the 90% discount kick in on the second call. |
| `02_multi_breakpoint_caching.py` | Agent-style request with cache breakpoints on `tools`, `system`, and the message history (the 4-breakpoint pattern). |
| `03_batch_api.py` | End-to-end Batch API: build → submit → poll → fetch results, with 1-hour caching enabled. |
| `04_token_counting.py` | Estimating cost before sending, `count_tokens` for text, system prompts, and tools. |
| `05_conversation_history_caching.py` | Rolling cache point that walks forward as the conversation grows. |
| `06_adaptive_thinking.py` | `thinking={"type":"adaptive"}` + `effort="medium"` + tight `max_tokens` and `stop_sequences`. |
| `07_cost_calculator.py` | Standalone CLI: `python 07_cost_calculator.py --help` |

## Running

```bash
python 01_basic_caching.py
python 04_token_counting.py
python 07_cost_calculator.py --model claude-sonnet-4-6 --input 10000 --output 500
```

## Notes & caveats

- Caching has a **1,024-token minimum** on current models. The examples use prompts long enough to qualify; if you swap in shorter content the cache will silently miss.
- `cache_creation_input_tokens` is billed at 1.25× (5-min) or 2× (1-h) of base input rate. `cache_read_input_tokens` is billed at 0.10×, the 90% discount.
- The Batch API runs **non-streaming** requests only and may take up to 24 hours (most batches finish in under an hour).
- Model strings used in these scripts (`claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`) are valid as of April 2026. Anthropic may publish dated aliases (e.g. `claude-haiku-4-5-20251001`); see https://platform.claude.com for the latest.
