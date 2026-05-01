# Changelog

All notable changes to this guide will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.0.0] - 2026-04-30

### Added

- Initial release of the optimization guide covering Claude.ai (Free / Pro / Max / Team / Enterprise), Claude API, Claude Code, Claude Desktop (Cowork), and Claude in Chrome.
- Pricing tables for Opus 4.7, Opus 4.6, Sonnet 4.6, Sonnet 4.5, Haiku 4.5, and legacy models.
- Subscription plan comparison and feature cost-impact tables.
- Prompt caching deep dive (5-min vs 1-h TTL, breakpoints, RAG patterns).
- Batch API guide.
- Extended thinking and `effort` parameter coverage.
- Tool-use, vision, and PDF cost guidance.
- Claude Code survival guide (CLAUDE.md, Skills, MCP overhead).
- Real worked cost-savings examples.
- Runnable code examples in Python and TypeScript:
  - `01_basic_caching` — minimal prompt caching with cost printout.
  - `02_multi_breakpoint_caching` — agent-style 4-breakpoint cache (Python).
  - `03_batch_api` — end-to-end Batch API with caching.
  - `04_token_counting` — `count_tokens` usage.
  - `05_conversation_history_caching` — rolling cache point (Python).
  - `06_adaptive_thinking` — adaptive thinking + `effort` (Python).
  - `07_cost_calculator` — CLI tool to compute cost across all rate categories.
- Standalone reference tables in `tables/`.
- LICENSE (MIT), CONTRIBUTING.md, .gitignore.
