#!/usr/bin/env python3
"""
Finance Pulse - daily pipeline.

1. Ask Claude (with live web search) to produce today's briefing:
   a written version (show notes) and a spoken script (for audio).
2. Convert the spoken script to an MP3 with a natural TTS voice.
3. Save the episode and rebuild the podcast RSS feed.

Run by the GitHub Action each morning. Can also be run locally.
"""

import os
import io
import re
import json
import html
import datetime as dt
from email.utils import format_datetime
from zoneinfo import ZoneInfo

import config

# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
EPISODES_DIR = os.path.join(ROOT, "episodes")
MANIFEST = os.path.join(ROOT, "episodes.json")
FEED = os.path.join(ROOT, "feed.xml")
os.makedirs(EPISODES_DIR, exist_ok=True)

DELIM = "===AUDIO_SCRIPT==="

# ---------------------------------------------------------------------
# 1. Generate the briefing with Claude + web search
# ---------------------------------------------------------------------
SYSTEM_PROMPT = """You are a banking finance-function intelligence analyst. \
Your reader is a finance transformation consultant who works primarily \
with banks and uses this briefing in client conversations. The test for every \
item: does it affect a bank CFO, controller, treasurer, or the finance \
transformation agenda?

Use the web_search tool to retrieve the most recent (last 24 to 48 hours) \
developments. Cover the latest from major financial podcasts (Bloomberg Daybreak, \
WSJ What's News, Bloomberg Surveillance, Bloomberg Odd Lots, FT News Briefing, \
Morning Brew) for macro, plus targeted banking, regulatory, and AI-in-finance news.

Anchor competitive positioning on the super-regional cohort: PNC, U.S. Bancorp, \
Truist, Fifth Third, KeyCorp, Regions, M&T, Citizens. Treat megabanks as context.

Required coverage: macro and rates; banking finance-function metrics (NIM, deposit \
beta and mix, funding costs, credit and provisioning, efficiency, capital); a \
regulatory radar (Basel III endgame, CCAR/DFAST, Fed/OCC/FDIC, accounting); AI in \
finance (adoption in FP&A, close, controllership, treasury, regulatory reporting; \
agentic AI; vendor moves across OneStream, SAP, Oracle, Workday, BlackLine; \
workforce implications; governance and ROI versus hype); and FP&A and transformation \
signals. Distinguish real deployments from vendor marketing. Anchor claims in \
specific facts, numbers, and named sources. No em dashes anywhere.

You must produce TWO outputs separated by a line containing only the delimiter \
%s

PART 1 (before the delimiter) - WRITTEN BRIEFING in clean Markdown, about 600 \
words, with sections: a one-line bold Bottom line; Top Takeaways; three Key Themes \
(each tagged New, Recurring, or Evolving); Banking Finance-Function; Regulatory \
Radar; AI in Finance; CFO Agenda, FP&A, and Transformation Signals; one Contrarian \
Insight; and three Client Conversation Hooks. This is the episode's show notes.

PART 2 (after the delimiter) - SPOKEN SCRIPT written for the ear, about 550 to 650 \
words, roughly a 4 minute listen. Plain prose only: no markdown, no bullets, no \
symbols, no headers. Spell numbers and percentages as words (for example "three \
point seven five percent", "June eighteenth"). Conversational and flowing, like a \
host reading a morning briefing. Open with a greeting and today's date. Close with \
the day's three conversation hooks and a brief sign-off.""" % DELIM


def generate_briefing(today_str):
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_msg = (
        f"Today is {today_str}. Produce today's Finance Pulse briefing now, "
        f"using live web search for the latest developments. Remember the two "
        f"parts separated by the delimiter."
    )

    resp = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=config.MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": config.WEB_SEARCH_MAX_USES,
        }],
        messages=[{"role": "user", "content": user_msg}],
    )

    text = "".join(
        block.text for block in resp.content if getattr(block, "type", "") == "text"
    ).strip()

    if DELIM in text:
        written, spoken = text.split(DELIM, 1)
    else:
        # Fallback: use the whole thing for both
        written, spoken = text, text

    return written.strip(), spoken.strip()


# ---------------------------------------------------------------------
# 2. Text to speech
# ---------------------------------------------------------------------
def chunk_text(text, limit=3500):
    """Split on sentence boundaries so each TTS request stays under the limit."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 > limit and cur:
            chunks.append(cur.strip())
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur.strip())
    return chunks


def tts_openai(text):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    parts = []
    for chunk in chunk_text(text, 3500):
        with client.audio.speech.with_streaming_response.create(
            model=config.OPENAI_TTS_MODEL,
            voice=config.OPENAI_TTS_VOICE,
            input=chunk,
            response_format="mp3",
        ) as response:
            buf = io.BytesIO()
            for data in response.iter_bytes():
                buf.write(data)
            parts.append(buf.getvalue())
    return parts


def tts_elevenlabs(text):
    import requests
    key = os.environ["ELEVENLABS_API_KEY"]
    url = (
        f"https://api.elevenlabs.io/v1/text-to-speech/"
        f"{config.ELEVENLABS_VOICE_ID}?output_format=mp3_44100_128"
    )
    parts = []
    for chunk in chunk_text(text, 2500):
        r = requests.post(
            url,
            headers={"xi-api-key": key, "Content-Type": "application/json"},
            json={"text": chunk, "model_id": config.ELEVENLABS_MODEL},
            timeout=120,
        )
        r.raise_for_status()
        parts.append(r.content)
    return parts


def synthesize(text, out_path):
    """Create the MP3 and return (duration_seconds, byte_size)."""
    from pydub import AudioSegment
    parts = tts_openai(text) if config.TTS_PROVIDER == "openai" else tts_elevenlabs(text)
    combined = AudioSegment.empty()
    for p in parts:
        combined += AudioSegment.from_file(io.BytesIO(p), format="mp3")
    combined.export(out_path, format="mp3", bitrate="128k")
    return int(len(combined) / 1000), os.path.getsize(out_path)


# ---------------------------------------------------------------------
# 3. Episode manifest + RSS feed
# ---------------------------------------------------------------------
def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            return json.load(f)
    return []


def save_manifest(items):
    with open(MANIFEST, "w") as f:
        json.dump(items, f, indent=2)


def hms(seconds):
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def prune(items):
    """Keep the newest KEEP_EPISODES; delete older MP3s."""
    items = sorted(items, key=lambda x: x["date"], reverse=True)
    keep, drop = items[: config.KEEP_EPISODES], items[config.KEEP_EPISODES:]
    for old in drop:
        path = os.path.join(EPISODES_DIR, old["file"])
        if os.path.exists(path):
            os.remove(path)
    return keep


def build_feed(items):
    items = sorted(items, key=lambda x: x["date"], reverse=True)
    now = format_datetime(dt.datetime.now(dt.timezone.utc))

    entries = []
    for it in items:
        mp3_url = f"{config.BASE_URL}/episodes/{it['file']}"
        pub = format_datetime(dt.datetime.fromisoformat(it["pubdate"]))
        desc = html.escape(it["notes"])
        entries.append(f"""    <item>
      <title>{html.escape(it['title'])}</title>
      <description><![CDATA[{it['notes']}]]></description>
      <itunes:summary>{desc}</itunes:summary>
      <pubDate>{pub}</pubDate>
      <enclosure url="{mp3_url}" length="{it['bytes']}" type="audio/mpeg"/>
      <guid isPermaLink="false">{it['file']}</guid>
      <itunes:duration>{it['duration']}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{html.escape(config.PODCAST_TITLE)}</title>
    <link>{config.BASE_URL}</link>
    <language>{config.PODCAST_LANGUAGE}</language>
    <description>{html.escape(config.PODCAST_DESCRIPTION)}</description>
    <itunes:author>{html.escape(config.PODCAST_AUTHOR)}</itunes:author>
    <itunes:summary>{html.escape(config.PODCAST_DESCRIPTION)}</itunes:summary>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Business"/>
    <itunes:owner>
      <itunes:name>{html.escape(config.PODCAST_AUTHOR)}</itunes:name>
      <itunes:email>{html.escape(config.PODCAST_EMAIL)}</itunes:email>
    </itunes:owner>
    <itunes:image href="{config.BASE_URL}/cover.jpg"/>
    <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(entries)}
  </channel>
</rss>
"""
    with open(FEED, "w") as f:
        f.write(feed)


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    tz = ZoneInfo(config.TIMEZONE)
    now = dt.datetime.now(tz)
    date_iso = now.date().isoformat()
    pretty = now.strftime("%A, %B %-d, %Y")
    print(f"Generating Finance Pulse for {pretty}")

    written, spoken = generate_briefing(pretty)
    print(f"Briefing generated. Written {len(written)} chars, spoken {len(spoken)} chars.")

    fname = f"{date_iso}.mp3"
    out_path = os.path.join(EPISODES_DIR, fname)
    duration_s, byte_size = synthesize(spoken, out_path)
    print(f"Audio written: {fname} ({hms(duration_s)}, {byte_size//1024} KB)")

    items = [x for x in load_manifest() if x["date"] != date_iso]  # replace same-day reruns
    items.append({
        "date": date_iso,
        "pubdate": now.isoformat(),
        "title": f"Finance Pulse - {now.strftime('%b %-d, %Y')}",
        "file": fname,
        "bytes": byte_size,
        "duration": hms(duration_s),
        "notes": written,
    })

    items = prune(items)
    save_manifest(items)
    build_feed(items)
    print(f"Feed rebuilt with {len(items)} episode(s). Done.")


if __name__ == "__main__":
    main()
