# =====================================================================
#  Finance Pulse - configuration
#  Edit the values below. Secrets (API keys) are NOT stored here;
#  they live in GitHub repository secrets. See README.md.
# =====================================================================

# ---- Podcast identity (shows up in your podcast app) ----
PODCAST_TITLE = "Finance Pulse"
PODCAST_AUTHOR = "Shawn Mascia"
PODCAST_DESCRIPTION = (
    "A daily banking finance-function intelligence briefing: macro, "
    "banking, regulatory, and AI in finance, built for client conversations."
)
PODCAST_EMAIL = "you@example.com"           # used in the RSS owner tag
PODCAST_LANGUAGE = "en-us"

# ---- Your GitHub Pages base URL (NO trailing slash) ----
# Format: https://<your-github-username>.github.io/<repo-name>
# Example: https://smascia.github.io/finance-pulse-podcast
BASE_URL = "https://YOURNAME.github.io/finance-pulse-podcast"

# ---- Claude (content generation) ----
# Verify the current model id at https://docs.claude.com (Models page).
ANTHROPIC_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4000
WEB_SEARCH_MAX_USES = 10                     # how many searches Claude may run

# ---- Text to speech ----
# Provider: "openai" or "elevenlabs"
TTS_PROVIDER = "openai"

# OpenAI TTS settings (used if TTS_PROVIDER == "openai")
OPENAI_TTS_MODEL = "gpt-4o-mini-tts"         # or "tts-1-hd"
OPENAI_TTS_VOICE = "onyx"                     # default. Alternatives: alloy, echo, fable, nova, shimmer

# ElevenLabs settings (used if TTS_PROVIDER == "elevenlabs")
ELEVENLABS_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # pick a voice id from your account
ELEVENLABS_MODEL = "eleven_turbo_v2_5"

# ---- Housekeeping ----
KEEP_EPISODES = 30                            # prune older episodes to keep repo small
TIMEZONE = "America/New_York"                 # used only for episode titles/dates
