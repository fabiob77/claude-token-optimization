# Publishing this repo to GitHub

This file is a step-by-step guide for the maintainer (you) to get the repository onto GitHub. It is not part of the user-facing docs — once you've published, you can delete it or move it to `docs/` for posterity.

You have two options. Pick one:

- **Option A — terminal (recommended).** Faster, scriptable, the standard workflow.
- **Option B — GitHub website (zero-CLI).** Drag-and-drop upload through the browser.

---

## Option A — terminal

### 1. Create the empty repo on GitHub

1. Go to <https://github.com/new>.
2. **Repository name**: `claude-token-optimization` (or your preferred name).
3. **Description**: *A practical guide to saving money and avoiding limits on Claude — for developers and consumer users.*
4. **Public** (recommended for a community resource) or **Private**.
5. **Do NOT** tick "Add a README", "Add .gitignore", or "Choose a license" — we already have those locally.
6. Click **Create repository**. You'll land on a "Quick setup" page; copy the HTTPS URL it shows (looks like `https://github.com/<your-username>/claude-token-optimization.git`).

### 2. Initialise git locally and push

From the folder where this `PUBLISHING.md` lives:

```bash
# 1. Make sure you have git configured
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"

# 2. Initialise the repo
git init -b main
git add .
git commit -m "Initial commit: complete guide, examples, tables"

# 3. Connect to your GitHub remote and push
git remote add origin https://github.com/<your-username>/claude-token-optimization.git
git push -u origin main
```

If `git push` asks for authentication, use a [Personal Access Token](https://github.com/settings/tokens) as the password (HTTPS) — GitHub no longer accepts account passwords on the CLI.

### 3. Polish the GitHub repo page

After the push, on github.com:

- **About panel (top right):**
  - Description: copy the one above.
  - Website: leave blank for now.
  - **Topics** (super important for discoverability — click the gear, type and Enter on each): `claude`, `anthropic`, `llm`, `prompt-engineering`, `prompt-caching`, `claude-code`, `claude-api`, `cost-optimization`, `tokens`, `ai`, `genai`.
- **README preview** should now render the full guide. Check the table of contents links work.
- **License** should auto-detect as MIT (you'll see a small badge near the top right).

### 4. (Optional) Pin it to your profile

On <https://github.com/your-username>: click **Customize your pins** and pick this repo. Pinned repos show up at the top of your profile.

### 5. (Optional) Enable Discussions and Issues

- **Settings → Features → Discussions**: turn on if you want a Q&A space.
- **Issues** are on by default — keep them on so people can flag pricing changes.

---

## Option B — GitHub website (no terminal)

### 1. Create the repo

Same steps 1–6 as Option A.

### 2. Upload the files

After clicking **Create repository**, on the empty repo page:

1. Click **uploading an existing file** in the "or push an existing repository from the command line" section.
2. **Drag the entire `claude-token-optimization` folder contents** (not the folder itself — its contents) into the upload area.
   - On macOS Finder / Windows Explorer: open the folder, select all (`⌘+A` / `Ctrl+A`), drag into the browser drop zone.
   - GitHub preserves folder structure during the upload.
3. Scroll down. **Commit message**: `Initial commit: complete guide, examples, tables`. Pick **Commit directly to the main branch** and click **Commit changes**.

That's it. Steps 3–5 from Option A still apply for polish.

> **Caveat:** the website upload limits the total to ~100 files per drag. This repo has fewer than that, so you're fine.

---

## Updating after the first push

```bash
git add .
git commit -m "Update Sonnet 4.6 cache write rates"
git push
```

For changes via the website: edit any file in the browser (pencil icon → make changes → "Commit changes" at the bottom).

---

## Suggested first improvements after publishing

- **Add a screenshot or hero image** to the README (e.g., a graph of cost savings with vs without caching). The first visual block is what catches eyes on GitHub.
- **Translate the consumer guide** into Italian (since you mentioned UK/EU markets in your context). A `README.it.md` works well, with a language switcher at the top of the English README.
- **GitHub Action** to regenerate the cost calculator's expected output as a doctest (catches accidental price-table desync).
- **Open a tracking issue** "Pricing & limits — pending verification" for any number you're not 100% sure about, so contributors know where help is wanted.
- **Add a "Last verified" badge** to the top of the README (`![Last verified](https://img.shields.io/badge/Last%20verified-Apr%202026-brightgreen)`) and update on each pricing-touching commit.

Once it's up, share the link here and I can help draft a launch post for HN, X/Bluesky, LinkedIn, or a relevant subreddit if you'd like.
