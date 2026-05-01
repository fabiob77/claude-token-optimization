# Contributing

Thanks for considering a contribution! This guide is a community resource and stays useful only if it stays accurate.

## What we welcome

- **Pricing or limit corrections** when Anthropic ships a change.
- **New model entries** when Anthropic releases one.
- **Better worked examples** with measured numbers (please include the workload assumptions).
- **New code examples** for the API, especially for edge cases not yet covered.
- **Translations** of the README into other languages (please open an issue to coordinate first).
- **Typo fixes, broken-link fixes, formatting cleanups.**

## What we're more careful about

- **Strong opinions about workflow** — we try to keep recommendations grounded in published docs or measured behavior, not vibes.
- **Sweeping rewrites** without a clear scope. Please open an issue first so we can agree on direction before you spend hours.
- **Unsourced numbers.** Every cost claim in the guide cites a primary source or shows the calculation. Please do the same.

## How to propose a change

1. **Open an issue** describing what's wrong / what you'd add. For trivial fixes (typos, broken links) you can skip straight to a PR.
2. **Fork** the repo and create a branch: `git checkout -b fix/cache-ttl-numbers`.
3. **Cite primary Anthropic sources** for any factual change. Acceptable sources:
   - `platform.claude.com/docs/...`
   - `support.claude.com/...`
   - `code.claude.com/docs/...`
   - The Anthropic engineering blog
   - Official Anthropic release announcements / model cards
   - Anthropic's pricing page
   - Cite community / third-party numbers as such (e.g., "community estimate, GitHub issue #...").
4. **Keep code examples runnable.** If you change a snippet in `examples/`, run it locally and confirm it works.
5. **Update the [CHANGELOG.md](CHANGELOG.md)** under the `## [Unreleased]` section.
6. **Open the PR.** Reference the issue, describe what changed, and paste a link to the source you cited.

## Style

- Markdown linted to match the existing tables and headings.
- Money values use `$N.NN` and "per MTok" / "/MTok" — not "per million tokens" mid-table.
- Code blocks declare a language so GitHub renders them correctly.
- Keep the **TL;DR** section to three bullets.
- Prefer concrete numbers over hedges ("≈$3.04/day" beats "much cheaper").

## Code-of-conduct

Be civil, be specific, assume good faith. Disagreements about strategy are fine and welcome — disagreements about people are not.

## License

By contributing you agree your contribution is licensed under [MIT](LICENSE).
