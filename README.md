# Finance Pulse - your private daily audio briefing

Every weekday morning this generates a fresh banking finance-function briefing,
turns it into a natural-voice MP3, and publishes it as a private podcast.
You subscribe once in your podcast app. After that: wake up, headphones in, play.

It runs entirely in the cloud on GitHub Actions, so your computer does not need
to be on.

---

## What you need

1. A GitHub account (free).
2. An Anthropic API key, from https://console.anthropic.com
3. A text-to-speech API key. Default is OpenAI (https://platform.openai.com).
   ElevenLabs is supported too if you prefer its voices.

Cost is roughly a few cents of API usage per episode.

---

## One-time setup (about 15 minutes)

### 1. Create the repository
- Create a new GitHub repository, for example `finance-pulse-podcast`.
- Upload every file in this folder to it (keep the structure, including the
  `.github/workflows/` folder and the `episodes/` folder).

### 2. Add your API keys as secrets
In the repo: Settings, then Secrets and variables, then Actions, then
"New repository secret". Add:
- `ANTHROPIC_API_KEY`  = your Anthropic key
- `OPENAI_API_KEY`     = your OpenAI key  (if using OpenAI TTS, the default)
- `ELEVENLABS_API_KEY` = your ElevenLabs key  (only if you switch the provider)

Secrets are encrypted. They never appear in the code or the feed.

### 3. Turn on GitHub Pages
In the repo: Settings, then Pages. Under "Build and deployment", set Source to
"Deploy from a branch", branch `main`, folder `/ (root)`. Save.

Your site will be at:
`https://<your-username>.github.io/<repo-name>`

### 4. Edit config.py
Open `config.py` and set:
- `BASE_URL` to the Pages URL from step 3 (no trailing slash).
- `PODCAST_AUTHOR`, `PODCAST_EMAIL`, and the voice if you want a different one.
- Confirm `ANTHROPIC_MODEL` is a current model id (see https://docs.claude.com).

Commit the change.

### 5. Set your wake time
Open `.github/workflows/daily.yml` and adjust the `cron` line. It is in UTC.
- 6am US Eastern in summer = `0 10 * * 1-5`
- 5am US Eastern in summer = `0 9 * * 1-5`
Use https://crontab.guru to translate any time. Leave `1-5` for weekdays only,
or change to `*` for every day.

### 6. First run
Go to the Actions tab, choose "Daily Finance Pulse", and click "Run workflow".
Wait a minute, then check that `feed.xml` and a file under `episodes/` appeared.

Open `https://<your-username>.github.io/<repo-name>/feed.xml` in a browser to
confirm it loads.

### 7. Subscribe on your iPhone
- Apple Podcasts: there is no built-in "add by URL", so use Overcast or Pocket
  Casts (free), which both have "Add URL". Paste your `feed.xml` URL.
- Or in Apple Podcasts on a Mac: File, then "Add a Show by URL", paste the
  feed URL; it syncs to your iPhone.

Set the show to auto-download new episodes. Done.

---

## Daily experience
Each weekday morning a new episode is waiting. Open your podcast app, press play,
and it streams to your headphones with normal lock-screen controls. The written
briefing is in the episode notes if you want to read instead.

---

## Customizing
- Voice: change `OPENAI_TTS_VOICE` in `config.py` (alloy, echo, fable, onyx,
  nova, shimmer). For studio quality, set `TTS_PROVIDER = "elevenlabs"`.
- Content focus: edit `SYSTEM_PROMPT` in `generate.py`.
- Length: adjust the word targets in `SYSTEM_PROMPT`.
- Cover art: add a square `cover.jpg` (1400x1400 or larger) to the repo root.

## Troubleshooting
- Empty or failed run: open the failed Action, read the logs. Most issues are a
  missing secret or a stale model id in `config.py`.
- No audio in the feed: confirm Pages is enabled and `BASE_URL` matches exactly.
- Times look off: the cron is UTC; re-check the conversion for daylight saving.

## A note on privacy
With OpenAI or ElevenLabs TTS, and with Claude's web search, your briefing text
is sent to those providers to be processed. That is fine for market commentary.
Do not feed this pipeline confidential client material.
