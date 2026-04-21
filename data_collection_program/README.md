# Data Collection Program

This folder contains the local tooling used to prepare new entries in the `experiments/` archive.

The current checked-in version supports both replication styles:
- no hardcoded API keys
- no automatic `git add` / `git commit` / `git push`
- API-backed helper mode when configured
- local fallback mode when no API key is configured

## What It Does

The Flask app helps with the repetitive parts of a new experiment:
- clone the latest experiment folder
- reset HTML and README sections for a fresh run
- paste or ingest the four raw HTML outputs
- count reasoning words and HTML lines
- save manual scores and observations
- generate the post template and README summary table

The optional browser automation uses Playwright against public model interfaces through Chrome's remote debugging port. Those flows are experimental and may need selector updates when the sites change.

## Replication Modes

There are two valid ways to think about this folder:

### Path 1: Exact historical-style replication

This is the closest to the original workflow used during data collection.
If you want to mirror that setup, keep a `.env` file with an OpenAI key available.
Use [`.env.example`](./.env.example) as the template:

```env
DATA_COLLECTION_TEXT_MODE=auto
OPENAI_API_KEY=your_key_here
OPENAI_TEXT_MODEL=gpt-4.1-mini
```

The main LLM-backed helper steps are:
- `Step 2: Update README prompt + TLDR`
- `Step 13a: Format observations`

Those steps now support API mode again in the current codebase.

### Path 2: Current public no-key mode

This repo currently ships the publish-safe version:
- `Step 2` uses local prompt keyword extraction to build the TLDR
- `Step 13a` formats observations locally from `model_scores.json`
- browser automation still uses public web UIs for ChatGPT, Gemini, and Grok, but not hosted API requests

So the current code can run fully without an OpenAI key, but it can also switch into API-backed text-helper mode automatically when a key is present.

## Access Requirements

The app does not require an `OPENAI_API_KEY` just to start.
The GPT-related browser automation still drives the public ChatGPT web interface through the browser; it does not call the OpenAI API directly.

The dependency split is:
- Core local workflow: no hosted API key required
- Optional text-helper API workflow: uses OpenAI for `Step 2` and `Step 13a` when `OPENAI_API_KEY` is present
- Optional browser automation: requires Google Chrome, Playwright, and active logged-in access to the public ChatGPT, Gemini, and Grok web apps you want to automate

So for an external user:
- if they only want the local experiment-management steps, they can run the app without any API key
- if they want the old text-helper behavior back, they can add an OpenAI key and the app will use it for the supported steps
- if they want to use the automated prompt-submission steps, they need their own browser sessions and whatever paid or account access those public model interfaces require
- those automated steps are browser-driven UI automation, not hosted API requests

## Workflow Map

The website exposes these steps:
- `Step 1`: Clone latest folder
- `Step 2`: Update README prompt + TLDR
- `Step 3`: Clear HTML + README sections
- `Step 5`: Time tracker UI
- `Step 5a`: Browser automation
- `Step 6`: Reasoning word count UI
- `Step 7`: Count HTML lines
- `Step 8`: Scoring UI
- `Step 9`: Record the videos
- `Step 10`: Gemini scoring prompt
- `Step 11`: Song prompt
- `Step 13`: Post template + README table
- `Step 13a`: Format observations

How to read that list:
- dual-mode text-helper steps: `Step 2`, `Step 13a` (`OpenAI API` when configured, otherwise local fallback)
- browser/UI automation steps: `Step 5a`
- local/manual repo steps: `Step 1`, `Step 3`, `Step 5`, `Step 6`, `Step 7`, `Step 8`, `Step 9`, `Step 10`, `Step 11`, `Step 13`

## Folder Layout

- `app.py`: main Flask app
- `templates/`: UI templates used by the Flask app
- `scripts/`: local helper scripts used by individual steps
- `automation/`: Playwright browser automation helpers
- `html_ai_battle.command`: macOS launcher

## Run It

From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

If you plan to use the optional browser automation, install Playwright's browser tooling too:

```bash
playwright install
```

You will also need Chrome running with remote debugging enabled. The app can launch it for you on macOS, or you can start it manually:

```bash
/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
```

## Important Behavior

- The app works against the repo's `experiments/` folder.
- Most steps target the newest experiment folder by creation or modification time.
- `build_post_template.py` expects a `downloaded_data.csv` file inside the newest experiment folder and renames it to match the experiment directory.
- `Step 2` and `Step 13a` automatically choose API mode or local mode based on your env configuration.
