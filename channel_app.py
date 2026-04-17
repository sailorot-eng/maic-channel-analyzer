"""
MAIC Channel Analyzer v2.0
===========================
- Stores full transcripts with timestamps in session state
- Keyword search engine across all loaded transcripts
- Auto-discovery: surfaces top frequent meaningful words inductively
- Comprehensive Gemini multimodal coding prompt generator
- Batch MAIC prompt generator with ZIP download

Author: PhD Candidate | Occupational Science | UFT AI Development Course
"""

import streamlit as st
import scrapetube
import re
import io
import zipfile
import time
import collections
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MAIC Channel Analyzer v2",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Source+Sans+3:wght@300;400;600&display=swap');
  :root {
    --navy:#0d1b2a; --ocean:#1b3a5c; --steel:#2e6da4;
    --wake:#5ba4d4; --foam:#d6eaf8; --brass:#c9a84c;
    --chalk:#f0f4f8; --coral:#e05555; --radius:10px;
  }
  html,body,[class*="css"]{font-family:'Source Sans 3',sans-serif;background-color:var(--navy)!important;color:var(--chalk);}
  .block-container{padding:2rem 2.5rem 3rem;max-width:1200px;}
  .maic-hero{background:linear-gradient(135deg,#0d1b2a 0%,#1b3a5c 60%,#0d2d4a 100%);border:1px solid var(--steel);border-radius:var(--radius);padding:1.8rem 2rem 1.4rem;margin-bottom:1.2rem;position:relative;overflow:hidden;}
  .maic-hero::before{content:"🚢";font-size:7rem;opacity:.05;position:absolute;right:1rem;top:-1rem;line-height:1;}
  .maic-hero h1{font-family:'Cinzel',serif;font-size:1.6rem;font-weight:900;color:var(--brass);letter-spacing:.05em;margin:0 0 .3rem;}
  .maic-hero p{font-size:.88rem;color:var(--foam);opacity:.85;max-width:680px;line-height:1.55;margin:0;}
  .card{background:var(--ocean);border:1px solid #2a4d6e;border-radius:var(--radius);padding:1.2rem 1.6rem;margin-bottom:1rem;}
  .card-title{font-family:'Cinzel',serif;font-size:.8rem;letter-spacing:.1em;color:var(--brass);text-transform:uppercase;margin-bottom:.8rem;}
  .stTextInput>div>div>input,.stTextArea textarea{background-color:#0d1b2a!important;border:1px solid var(--steel)!important;color:var(--chalk)!important;border-radius:6px!important;}
  .stButton>button{background:#c9a84c!important;border:2px solid #e8c96a!important;color:#1a0f00!important;font-family:'Cinzel',serif!important;font-weight:700!important;letter-spacing:.06em!important;font-size:.85rem!important;border-radius:6px!important;}
  .stProgress>div>div{background-color:var(--brass)!important;}
  [data-testid="stSidebar"]{background:#07111e!important;border-right:1px solid #1b3a5c;}
  [data-testid="stSidebar"] *{color:var(--chalk)!important;}
  .stat-row{display:flex;gap:.8rem;flex-wrap:wrap;margin:.5rem 0 1rem;}
  .stat-pill{background:rgba(46,109,164,.25);border:1px solid var(--steel);border-radius:8px;padding:.4rem .9rem;text-align:center;}
  .stat-val{font-family:'Cinzel',serif;font-size:1.2rem;color:var(--brass);font-weight:700;}
  .stat-lbl{font-size:.68rem;color:var(--wake);letter-spacing:.05em;text-transform:uppercase;}
  .result-row{background:#0d1b2a;border:1px solid #2a4d6e;border-radius:6px;padding:.6rem .9rem;margin-bottom:.35rem;font-size:.82rem;line-height:1.55;}
  .result-title{color:#c9a84c;font-weight:600;font-size:.78rem;}
  .result-ts{color:#5ba4d4;font-size:.72rem;font-family:monospace;}
  .result-excerpt{color:#d6eaf8;}
  .result-count{background:rgba(201,168,76,.15);border:1px solid rgba(201,168,76,.3);border-radius:4px;padding:.1rem .4rem;font-size:.7rem;color:#c9a84c;}
  .keyword-chip{display:inline-block;background:rgba(91,164,212,.15);border:1px solid #2e6da4;border-radius:12px;padding:.2rem .6rem;font-size:.75rem;color:#5ba4d4;margin:.15rem;}
  .error-row{font-size:.8rem;color:var(--coral);padding:.2rem 0;}
  hr{border-color:#2a4d6e!important;}
  .stDataFrame{border-radius:8px!important;}
  .stTabs [data-baseweb="tab-list"]{background:#07111e;border-radius:8px 8px 0 0;border:1px solid #2a4d6e;border-bottom:none;}
  .stTabs [data-baseweb="tab"]{color:#8fbcd4!important;font-family:'Cinzel',serif!important;font-size:.78rem!important;letter-spacing:.06em!important;}
  .stTabs [aria-selected="true"]{color:#c9a84c!important;border-bottom:2px solid #c9a84c!important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
for k, v in {
    "videos":       [],       # list of video dicts from scrapetube
    "transcripts":  {},       # vid_id -> {title, url, segments:[{text,start}]}
    "channel_name": "",
    "loaded":       False,    # True once transcripts have been fetched
    "prompts":      {},       # vid_id -> prompt string
    "analysis_done": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# STOP WORDS — for auto-discovery (common words that don't carry meaning)
# ─────────────────────────────────────────────────────────────────────────────
STOP_WORDS = set("""
a about above after again against all also am an and any are aren't as at be
because been before being below between both but by can can't cannot could
couldn't did didn't do does doesn't doing don't down during each few for from
further get got had hadn't has hasn't have haven't having he he'd he'll he's
her here here's hers herself him himself his how how's i i'd i'll i'm i've if
in into is isn't it it's its itself just know let let's like little lot make
me more most mustn't my myself no nor not now of off on once only or other
ought our ours ourselves out over own same shan't she she'd she'll she's
should shouldn't so some such than that that's the their theirs them
themselves then there there's these they they'd they'll they're they've
this those through to too under until up very was wasn't we we'd we'll we're
we've were weren't what what's when when's where where's which while who
who's whom why why's will with won't would wouldn't you you'd you'll you're
you've your yours yourself yourselves got going yeah okay actually really
just like oh yeah well um uh kind sort thing things way yeah one two three
four five six seven eight nine ten also even still back around much many
something everything nothing anything ever never always sometimes
""".split())

# ─────────────────────────────────────────────────────────────────────────────
# COMMAND PRESENCE SEED TERMS
# ─────────────────────────────────────────────────────────────────────────────
COMMAND_PRESENCE_TERMS = [
    "decision","authority","responsibility","situational awareness",
    "judgment","calm","composure","navigation","bearing","helm","crew","watch",
    "weather","risk","safety","protocol","right of way","stand-on","give-way",
    "collision","COLREGS","VHF","mayday","distress","anchor","throttle",
    "trim","capsize","rescue","PFD","command","leadership","skipper","captain",
    "communication","confidence","adapt","assess","plan","execute","debrief",
    "mistake","tack","jibe","reef","passage","offshore","watch","bearing",
    "course","chart","waypoint","visibility","squall","gust","swell","current",
]

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def parse_channel_identifier(url: str):
    url = url.strip().rstrip("/")
    for pattern, kind in [
        (r"youtube\.com/@([\w\-]+)", "channel_username"),
        (r"youtube\.com/channel/(UC[\w\-]+)", "channel_id"),
        (r"youtube\.com/(?:c|user)/([\w\-]+)", "channel_username"),
    ]:
        m = re.search(pattern, url)
        if m:
            return m.group(1), kind
    m = re.match(r"@?([\w\-]+)$", url.split("/")[-1])
    return (m.group(1), "channel_username") if m else (None, "unknown")


def fetch_channel_videos(identifier: str, id_type: str, limit: int = 300):
    gen = (
        scrapetube.get_channel(channel_id=identifier, limit=limit)
        if id_type == "channel_id"
        else scrapetube.get_channel(channel_username=identifier, limit=limit)
    )
    videos = []
    for v in gen:
        vid_id = v.get("videoId", "")
        runs   = v.get("title", {}).get("runs", [])
        title  = runs[0].get("text", "") if runs else ""
        if vid_id and title:
            videos.append({
                "video_id": vid_id,
                "title":    title,
                "duration": v.get("lengthText",       {}).get("simpleText", ""),
                "views":    v.get("viewCountText",     {}).get("simpleText", ""),
                "date":     v.get("publishedTimeText", {}).get("simpleText", ""),
                "url":      f"https://www.youtube.com/watch?v={vid_id}",
            })
    return videos


def fetch_transcript_raw(video_id: str):
    """
    Returns list of {text, start, duration} dicts.
    Handles all versions of youtube-transcript-api including
    newer versions that return FetchedTranscriptSnippet objects.
    """

    def normalize(entries):
        """
        Convert whatever the API returns into plain dicts
        with 'text' and 'start' keys. Handles:
        - Plain dicts (old API)
        - FetchedTranscriptSnippet objects (new API 0.6.x+)
        - Objects with .text / .start attributes
        """
        result = []
        for entry in entries:
            if isinstance(entry, dict):
                result.append(entry)
            else:
                # Try attribute access for new-style objects
                try:
                    text  = getattr(entry, "text",  None) or str(entry)
                    start = getattr(entry, "start", 0.0)
                    dur   = getattr(entry, "duration", 0.0)
                    result.append({"text": text, "start": float(start), "duration": float(dur)})
                except Exception:
                    result.append({"text": str(entry), "start": 0.0, "duration": 0.0})
        return result

    # Method 1: get_transcript() class method — most stable
    try:
        raw = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "en-US", "en-GB"]
        )
        return normalize(raw)
    except Exception:
        pass

    # Method 2: no language filter
    try:
        raw = YouTubeTranscriptApi.get_transcript(video_id)
        return normalize(raw)
    except Exception:
        pass

    # Method 3: instance list() — new API style
    try:
        api = YouTubeTranscriptApi()
        list_fn = getattr(api, "list", None) or getattr(api, "list_transcripts", None)
        if list_fn:
            tl = list_fn(video_id)
            for attempt in [
                lambda t: t.find_manually_created_transcript(["en","en-US","en-GB"]),
                lambda t: t.find_generated_transcript(["en","en-US","en-GB"]),
                lambda t: next(iter(t)),
            ]:
                try:
                    result = attempt(tl)
                    fetch_fn = getattr(result, "fetch", None)
                    raw = fetch_fn() if fetch_fn else list(result)
                    return normalize(raw)
                except Exception:
                    continue
    except Exception:
        pass

    raise NoTranscriptFound(video_id, ["en"], {})


def seconds_to_timestamp(seconds: float) -> str:
    """Convert float seconds to HH:MM:SS or MM:SS string."""
    s = int(seconds)
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def build_segments(raw: list) -> list:
    """
    Convert raw transcript entries into clean segments.
    Each segment: {text: str, start: float, timestamp: str}
    Groups ~3 entries together into sentence-like chunks.
    """
    segments = []
    buffer_text = []
    buffer_start = 0.0

    for i, entry in enumerate(raw):
        text = re.sub(r"\[.*?\]", "", entry.get("text", ""))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue

        if not buffer_text:
            buffer_start = entry.get("start", 0.0)

        buffer_text.append(text)

        # Group every 3 entries or on sentence-ending punctuation
        joined = " ".join(buffer_text)
        if len(buffer_text) >= 3 or (joined and joined[-1] in ".!?"):
            segments.append({
                "text":      joined,
                "start":     buffer_start,
                "timestamp": seconds_to_timestamp(buffer_start),
            })
            buffer_text  = []
            buffer_start = 0.0

    # Flush remainder
    if buffer_text:
        segments.append({
            "text":      " ".join(buffer_text),
            "start":     buffer_start,
            "timestamp": seconds_to_timestamp(buffer_start),
        })

    return segments


def duration_to_minutes(d: str) -> int:
    parts = d.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 2:
            return int(parts[0])
    except Exception:
        pass
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — SEARCH ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def search_transcripts(keyword: str, transcripts: dict) -> list:
    """
    Search all stored transcripts for a keyword.
    Returns list of match dicts sorted by video then timestamp.
    Each match: {video_id, title, url, timestamp, start, excerpt, count_in_video}
    """
    keyword_lower = keyword.strip().lower()
    if not keyword_lower:
        return []

    # First pass: count occurrences per video
    video_counts = {}
    for vid_id, data in transcripts.items():
        count = sum(
            1 for seg in data["segments"]
            if keyword_lower in seg["text"].lower()
        )
        video_counts[vid_id] = count

    # Second pass: collect matching segments
    results = []
    for vid_id, data in transcripts.items():
        for seg in data["segments"]:
            if keyword_lower in seg["text"].lower():
                # Highlight keyword in excerpt
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                excerpt = pattern.sub(f"**{keyword.upper()}**", seg["text"])
                results.append({
                    "video_id":       vid_id,
                    "title":          data["title"],
                    "url":            data["url"],
                    "timestamp":      seg["timestamp"],
                    "start":          seg["start"],
                    "excerpt":        excerpt,
                    "count_in_video": video_counts[vid_id],
                })

    # Sort by count descending (richest videos first), then timestamp
    results.sort(key=lambda r: (-r["count_in_video"], r["start"]))
    return results


def search_multiple_keywords(keywords: list, transcripts: dict) -> dict:
    """Search for multiple keywords at once. Returns {keyword: [results]}."""
    return {kw: search_transcripts(kw, transcripts) for kw in keywords if kw.strip()}


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-DISCOVERY — inductive word frequency analysis
# ─────────────────────────────────────────────────────────────────────────────

def auto_discover_terms(transcripts: dict, top_n: int = 60) -> list:
    """
    Count all meaningful word frequencies across entire corpus.
    Returns list of (word, count) tuples, sorted by frequency.
    Filters out stop words and short words.
    """
    word_counts = collections.Counter()

    for vid_id, data in transcripts.items():
        for seg in data["segments"]:
            words = re.findall(r"[a-zA-Z']+", seg["text"].lower())
            for word in words:
                # Clean possessives
                word = word.strip("'")
                if (len(word) >= 4
                        and word not in STOP_WORDS
                        and not word.isdigit()):
                    word_counts[word] += 1

    return word_counts.most_common(top_n)


def categorize_discovered_term(word: str) -> str:
    """
    Auto-categorize a discovered term into a domain.
    Returns a domain label string.
    """
    agency_words = {
        "decided","decision","chose","choice","plan","planned","assessed",
        "assessment","confident","confidence","control","controlled","managed",
        "adapted","adjust","adjusted","solved","problem","challenge","risk",
        "crew","skipper","captain","helm","steering","navigate","navigation",
        "command","lead","leadership","responsible","responsibility","skill",
        "experience","learned","lesson","mistake","correct","execute",
    }
    emotion_words = {
        "scared","fear","afraid","terrified","calm","panic","anxious","stress",
        "worried","nervous","comfortable","confident","trust","doubt","hope",
        "excited","frustrated","exhausted","tired","focused","determined",
        "proud","grateful","overwhelmed","lonely","peaceful","joy","love",
    }
    technical_words = {
        "wind","sail","tack","jibe","reef","anchor","chart","waypoint","gps",
        "compass","bearing","course","knots","miles","weather","forecast",
        "storm","squall","wave","swell","current","tide","depth","draft",
        "engine","motor","fuel","battery","solar","autopilot","vhf","radio",
        "mayday","colregs","uscg","coast","guard","vessel","boat","ship",
    }
    identity_words = {
        "life","home","family","live","living","freedom","dream","adventure",
        "meaning","purpose","identity","belong","community","world","ocean",
        "sea","sailing","sailor","offshore","passage","voyage","journey",
    }

    w = word.lower()
    if w in agency_words:
        return "🎯 Agency / Command"
    if w in emotion_words:
        return "💭 Emotional / Psychological"
    if w in technical_words:
        return "⚙️ Technical / Seamanship"
    if w in identity_words:
        return "⚓ Identity / Meaning"
    return "📌 Uncategorized"


# ─────────────────────────────────────────────────────────────────────────────
# MAIC PROMPT BUILDER (for Tab 3)
# ─────────────────────────────────────────────────────────────────────────────

def build_maic_prompt(video: dict, segments: list, researcher_notes: str = "") -> str:
    terms = "\n".join(f"   - {t}" for t in COMMAND_PRESENCE_TERMS)
    full_text = "\n".join(
        f"\n--- SEGMENT {i+1} | {seg['timestamp']} ---\n{seg['text']}"
        for i, seg in enumerate(segments)
    )
    notes_block = f"\nRESEARCHER NOTES:\n{researcher_notes.strip()}\n" if researcher_notes.strip() else ""
    wc = sum(len(seg["text"].split()) for seg in segments)

    return f"""MARITIME AGENCY & IDENTITY CLASSIFIER (MAIC) v2.0
Qualitative Analysis Prompt — Occupational Science Dissertation

SOURCE : {video['url']}
TITLE  : {video['title']}
WORDS  : {wc:,} across {len(segments)} segments
{notes_block}
=============================================================================
LENS 1 — Post-Work Occupational Identity (Wilcock: doing-being-belonging-becoming)
  a) Language used to describe why they sail?
  b) Sailing as WORK, LEISURE, VOCATION, or hybrid?
  c) Temporal structure around sailing?
  d) Community/relational belonging?
  e) Occupational becoming — growth or transformation?
  f) AI/automation tools positioned how?
  g) Post-work thesis confidence: Low/Medium/High

=============================================================================
LENS 2 — Occupational Justice, Ableism & Co-Occupation
  a) Disability, chronic illness, neurodivergence?
  b) Adaptive technologies?
  c) Environmental modifications?
  d) Co-occupation moments?
  e) Occupational injustice or exclusion?
  f) Ableist language?
  g) 3 photovoice prompts: "Photograph a moment when ___"

=============================================================================
LENS 3 — USCG Command Presence: CTE Case Studies
  a) 3-6 critical incidents — segment | description | USCG competency | discussion Q
  b) Rule-based navigation decisions?
  c) Weather decision-making?
  d) Crew leadership moments?
  e) Mistakes reflected upon — learning loop?
  f) CTE utility rating 1-10

=============================================================================
LENS 4 — Command Presence Term Frequency
  Count occurrences of:
{terms}

  Output: | Rank | Term | Count | Timestamp | Category |
  Then: emergent terms, 10 photovoice prompts, 150-word curriculum synthesis.

=============================================================================
FINAL SYNTHESIS — 300-word dissertation memo:
  1. Key findings across all lenses
  2. Convergent themes
  3. Challenges to theoretical framework
  4. 2-3 member-checking questions
  5. Analytical Richness Score 1-10

=============================================================================
TRANSCRIPT DATA:
{full_text}
=============================================================================
END. Produce full four-lens analysis.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI MULTIMODAL PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_gemini_prompt(video_url: str, researcher_notes: str = "") -> str:
    notes_block = f"\nRESEARCHER CONTEXT:\n{researcher_notes.strip()}\n" if researcher_notes.strip() else ""

    return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   MAIC — COMPREHENSIVE MULTIMODAL ETHNOGRAPHIC VIDEO ANALYSIS              ║
║   Gemini Coding Prompt — Occupational Science Dissertation                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

VIDEO URL : {video_url}
PASTE INTO: gemini.google.com (use Gemini 1.5 Pro — supports YouTube video)
{notes_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## YOUR ROLE

You are a qualitative research assistant for a PhD dissertation in Occupational
Science. The researcher is a licensed USCG Captain and NYC occupational therapist
studying how sailors develop AGENCY and COMMAND PRESENCE — and how these qualities
can be taught to adaptive sailors and high school CTE students.

Please watch the ENTIRE video at the URL above before beginning your analysis.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## WHAT TO WATCH FOR — CODING GUIDE

Code EVERY moment that shows evidence of EITHER of these:

### AGENCY — the capacity to act purposefully and self-directedly
Positive indicators (code as AGENCY+):
  - Sailor scans environment BEFORE acting (horizon, instruments, sky, crew)
  - Explicit decision narration: "I decided...", "We chose...", "The call was..."
  - Problem-solving improvisation when something breaks or changes
  - Self-correction after a mistake — learning loop visible
  - Helm behavior that shows intentionality: deliberate course changes,
    anticipatory sail trim, reading wind on water surface
  - Eye contact with crew that communicates role assignments nonverbally
  - Physical preparation before a maneuver (checking, adjusting, positioning)

Negative indicators (code as AGENCY-):
  - Surprised by conditions that were foreseeable
  - Hesitation or freezing at decision points
  - Delegating all decisions to instruments or another person
  - Reactive rather than anticipatory behavior
  - Body language of uncertainty: hunched posture, looking around for guidance,
    hands uncertain on helm

### COMMAND PRESENCE — observable constellation of competent vessel command
Positive indicators (code as CP+):
  POSTURE & BODY:
  - Upright, stable stance even in rough conditions
  - Deliberate, economical movement — no wasted motion
  - Relaxed grip on helm or lines (vs. white-knuckle tension)
  - Head up and scanning (vs. head down looking at feet or instruments only)
  - Squared shoulders during crew briefings or challenging moments
  - Calm, unhurried movement when situation demands urgency

  FACE & EXPRESSION:
  - Neutral or focused expression during high-stress moments
  - Eye contact that commands rather than seeks permission
  - Micro-expressions of assessment (narrowed eyes reading conditions)
  - Controlled breathing visible in chest/shoulders
  - Genuine composure — not performed calm, actual calm

  VOICE (paralinguistic):
  - Steady pitch and pace under pressure
  - Short, clear commands (vs. long explanations mid-maneuver)
  - Authority without aggression — confident tone not dominant tone
  - Silence used intentionally (not filling space with words)
  - Tone matches situation — quieter in danger, not louder

  CREW DYNAMICS:
  - Crew look to subject for cues — natural leadership deference
  - Subject acknowledges crew input without losing decisional authority
  - Crew body language relaxes when subject takes control
  - Smooth handoffs of tasks with clear verbal/nonverbal signals

Negative indicators (code as CP-):
  - Collapsed, hunched, or braced posture during demanding moments
  - White-knuckle grip suggesting fear rather than control
  - Scanning frantically vs. deliberately
  - Facial expressions of fear, confusion, or panic that spread to crew
  - Voice rising in pitch or pace under pressure
  - Shouting, talking over crew, or vague commands
  - Crew looking at each other instead of the subject
  - Subject looking to crew or others for reassurance

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OUTPUT FORMAT — Produce ALL six sections

### SECTION 1 — TIMESTAMPED CODING TABLE

For every coded moment, one row in this table:

| Timestamp | Code | Channel | What You See/Hear | Analytical Note |
|-----------|------|---------|-------------------|-----------------|

Channel = V (verbal) / VI (visual) / P (paralinguistic)
Code = AGENCY+ / AGENCY- / CP+ / CP-

Include AT MINIMUM 20 coded moments. More is better.
Be specific — describe exact posture, expression, words, or tone.

Example rows:
| 04:32 | CP+ | VI | Sailor maintains upright stance at helm, shoulders relaxed, eyes scanning horizon — does not grip lifelines despite 20-knot gusts | Physical composure visible in body architecture — weight centered, no bracing behavior despite conditions |
| 07:15 | AGENCY+ | V | "I looked at the sky, checked the barometer, and made the call to stay put" | Explicit environmental reading sequence narrated — three-step situational assessment before decision |
| 12:44 | CP- | P | Voice rises sharply when line tangles — pitch increases, pace doubles, one-word commands become fragments | Paralinguistic composure breaks under equipment stress — recovers within 30 seconds, notable resilience |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 2 — FREQUENCY SUMMARY

| Code | Count | % of total coded moments | Peak moment (timestamp) |
|------|-------|--------------------------|------------------------|
| AGENCY+ | | | |
| AGENCY- | | | |
| CP+ | | | |
| CP- | | | |

Overall AGENCY ratio: AGENCY+ / (AGENCY+ + AGENCY-) × 100 = ___%
Overall CP ratio: CP+ / (CP+ + CP-) × 100 = ___%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 3 — TOP 5 MOMENTS FOR CTE TEACHING

The five most powerful moments in this video for teaching Command Presence
to high school students pursuing USCG OUPV (6-Pack Captain's License):

For each moment:
  Timestamp: XX:XX
  What is happening: [verbal + visual description]
  Why it matters for CTE: [connection to USCG competency]
  Discussion question for students: [open-ended question]
  Visual description for photovoice: [what an adaptive sailor could photograph
    to capture a similar moment in their own experience]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 4 — ABSENCE & NEGATIVE CASES

Identify 3-5 moments of AGENCY- or CP- and analyze them:
  - What is the sailor doing or failing to do?
  - What does their body, face, or voice reveal?
  - How does the crew respond to this absence?
  - What would Command Presence look like at this same moment?

These negative cases are equally important for teaching — students learn
what to do AND what not to do.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 5 — WHAT THE TRANSCRIPT MISSES

Identify 3-5 moments where the VISUAL or PARALINGUISTIC data tells a
richer or different story than the spoken words alone.

Format:
  Timestamp: XX:XX
  Words spoken: "..."
  What the video shows/sounds: [describe visually and paralinguistically]
  Why this matters methodologically: [argument for multimodal analysis]

This section supports the dissertation argument that transcript-only
analysis is insufficient for studying agency and command presence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 6 — DISSERTATION MEMO (250-350 words)

Write in academic qualitative research voice. Address:
  1. Overall assessment of agency and command presence in this video
  2. Most significant finding — what surprised you most
  3. Relationship between verbal and nonverbal channels — do they align?
  4. What this video contributes to understanding post-work sailing identity
  5. Recommended use: CTE case study / photovoice seed / longitudinal data point
  6. One follow-up question you would ask this sailor in member-checking
  7. Command Presence Composite Score (0-100) with rationale

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END. Watch the full video and produce all six sections.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚢 MAIC v2.0")
    st.markdown("""
**Research Pipeline:**

1. Load channel videos
2. Fetch & store transcripts
3. Search for keywords
4. Auto-discover themes
5. Generate Gemini prompt
6. Generate MAIC prompts

---
**Three tools in one:**
- 🔍 Keyword Search Engine
- 🧠 Auto Theme Discovery
- 🎬 Gemini Video Coder

---
**Paste results into:**
- [Gemini](https://gemini.google.com) — video analysis
- [Claude.ai](https://claude.ai) — transcript analysis
""")
    st.markdown("---")
    if st.session_state.transcripts:
        n = len(st.session_state.transcripts)
        total_words = sum(
            sum(len(s["text"].split()) for s in d["segments"])
            for d in st.session_state.transcripts.values()
        )
        st.markdown(f"""
<div style='font-size:.8rem;color:#8fbcd4;'>
<strong style='color:#c9a84c;'>Corpus loaded:</strong><br>
{n} transcripts<br>
~{total_words:,} words<br>
Channel: {st.session_state.channel_name}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="maic-hero">
  <h1>🚢 MAIC Channel Analyzer v2.0</h1>
  <p>Load a YouTube channel → fetch transcripts with timestamps →
  search for keywords → auto-discover themes inductively →
  generate Gemini video coding prompts. Everything in one tool.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Load Channel",
    "🔍 Search & Discover",
    "🎬 Gemini Video Prompt",
    "📄 MAIC Transcript Prompts",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — LOAD CHANNEL
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="card"><div class="card-title">📡 Step 1 — Enter Channel URL</div>', unsafe_allow_html=True)

    col_url, col_limit = st.columns([3, 1])
    with col_url:
        channel_url = st.text_input(
            "Channel URL",
            placeholder="https://www.youtube.com/@svdelos",
            label_visibility="collapsed",
        )
    with col_limit:
        video_limit = st.number_input("Max videos", min_value=3, max_value=500, value=200, step=10)

    test_mode = st.checkbox(
        "🧪 Test mode — load 3 videos only (recommended for first run)",
        value=True,
        help="Always test with 3 videos first to confirm transcripts are loading correctly before running the full channel."
    )

    if st.button("📺  Load Channel Videos", use_container_width=True):
        if not channel_url.strip():
            st.error("Please enter a YouTube channel URL.")
        else:
            identifier, id_type = parse_channel_identifier(channel_url.strip())
            if not identifier:
                st.error("Could not parse that URL. Try: https://www.youtube.com/@channelname")
            else:
                limit = 3 if test_mode else video_limit
                with st.spinner(f"Scanning channel — loading up to {limit} videos..."):
                    try:
                        videos = fetch_channel_videos(identifier, id_type, limit=limit)
                        st.session_state.videos       = videos
                        st.session_state.channel_name = identifier
                        st.session_state.transcripts  = {}
                        st.session_state.loaded       = False
                        st.session_state.prompts      = {}
                        st.success(f"Found {len(videos)} videos from **{identifier}**")
                    except Exception as e:
                        st.error(f"Could not load channel: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Video list & transcript fetch ──
    if st.session_state.videos:
        videos = st.session_state.videos

        st.markdown('<div class="card"><div class="card-title">☑️ Step 2 — Select Videos & Fetch Transcripts</div>', unsafe_allow_html=True)

        # Filters
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        with col_f1:
            search_q = st.text_input("Filter by title", placeholder="Delos, sailing, storm...")
        with col_f2:
            min_min = st.number_input("Min duration (min)", min_value=0, max_value=120, value=0)
        with col_f3:
            sort_order = st.selectbox("Sort", ["Newest first", "Oldest first", "Longest first"])

        filtered = [v for v in videos
                    if (not search_q.strip() or search_q.strip().lower() in v["title"].lower())
                    and duration_to_minutes(v["duration"]) >= min_min]
        if sort_order == "Oldest first":
            filtered = list(reversed(filtered))
        elif sort_order == "Longest first":
            filtered = sorted(filtered, key=lambda v: duration_to_minutes(v["duration"]), reverse=True)

        all_selected = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]

        st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{len(videos)}</span><span class="stat-lbl">Loaded</span></div>
  <div class="stat-pill"><span class="stat-val">{len(filtered)}</span><span class="stat-lbl">Showing</span></div>
  <div class="stat-pill"><span class="stat-val">{len(all_selected)}</span><span class="stat-lbl">Selected</span></div>
  <div class="stat-pill"><span class="stat-val">{len(st.session_state.transcripts)}</span><span class="stat-lbl">Transcripts Stored</span></div>
</div>""", unsafe_allow_html=True)

        col_sa, col_da, _ = st.columns([1, 1, 4])
        with col_sa:
            if st.button("✅ Select all visible"):
                for v in filtered:
                    st.session_state[f"chk_{v['video_id']}"] = True
                st.rerun()
        with col_da:
            if st.button("✖️ Deselect all"):
                for v in videos:
                    st.session_state[f"chk_{v['video_id']}"] = False
                st.rerun()

        for v in filtered:
            vid_id = v["video_id"]
            stored = "✅" if vid_id in st.session_state.transcripts else ""
            col_chk, col_info = st.columns([0.05, 0.95])
            with col_chk:
                st.checkbox("", key=f"chk_{vid_id}")
            with col_info:
                st.markdown(
                    f"**{v['title']} {stored}**  "
                    f"<span style='color:#8fbcd4;font-size:.76rem'>⏱ {v['duration']} | 📅 {v['date']} | 👁 {v['views']}</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

        all_selected = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]

        if all_selected:
            st.markdown('<div class="card"><div class="card-title">⬇️ Step 3 — Fetch & Store Transcripts</div>', unsafe_allow_html=True)
            st.info(f"**{len(all_selected)} video{'s' if len(all_selected)!=1 else ''} selected.** Transcripts will be stored with timestamps so you can search them in Tab 2.")

            if st.button(f"⬇️  Fetch Transcripts for {len(all_selected)} Video{'s' if len(all_selected)!=1 else ''}", use_container_width=True):
                progress = st.progress(0)
                log      = st.empty()
                lines    = []

                for i, v in enumerate(all_selected):
                    vid_id = v["video_id"]
                    lines.append(f"🌊 Fetching: {v['title'][:55]}...")
                    log.markdown("<br>".join(
                        f"<div style='font-size:.8rem;color:#8fbcd4'>{l}</div>"
                        for l in lines[-6:]
                    ), unsafe_allow_html=True)

                    try:
                        raw      = fetch_transcript_raw(vid_id)
                        segments = build_segments(raw)
                        if len(segments) < 5:
                            raise ValueError("Too few segments — likely no speech")

                        st.session_state.transcripts[vid_id] = {
                            "title":    v["title"],
                            "url":      v["url"],
                            "duration": v["duration"],
                            "date":     v["date"],
                            "segments": segments,
                        }
                        wc = sum(len(s["text"].split()) for s in segments)
                        lines[-1] = f"✅ Stored: {v['title'][:50]} ({wc:,} words, {len(segments)} segments)"

                    except (TranscriptsDisabled, NoTranscriptFound):
                        lines[-1] = f"❌ No captions: {v['title'][:50]}"
                    except VideoUnavailable:
                        lines[-1] = f"❌ Unavailable: {v['title'][:50]}"
                    except Exception as e:
                        lines[-1] = f"⚠️ {v['title'][:45]}: {str(e)[:40]}"

                    progress.progress((i + 1) / len(all_selected))
                    log.markdown("<br>".join(
                        f"<div style='font-size:.8rem;color:#8fbcd4'>{l}</div>"
                        for l in lines[-6:]
                    ), unsafe_allow_html=True)
                    time.sleep(0.5)  # Step 5 — rate limit protection

                st.session_state.loaded = True
                n_stored = len(st.session_state.transcripts)
                st.success(f"✅ Done! {n_stored} transcripts stored and ready to search. Go to Tab 2 → Search & Discover.")

            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — SEARCH & DISCOVER
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.transcripts:
        st.info("⚓ No transcripts loaded yet. Go to Tab 1 to load a channel and fetch transcripts first.")
    else:
        transcripts = st.session_state.transcripts
        n_trans = len(transcripts)
        total_words = sum(
            sum(len(s["text"].split()) for s in d["segments"])
            for d in transcripts.values()
        )
        total_segs = sum(len(d["segments"]) for d in transcripts.values())

        st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{n_trans}</span><span class="stat-lbl">Transcripts</span></div>
  <div class="stat-pill"><span class="stat-val">{total_words:,}</span><span class="stat-lbl">Total Words</span></div>
  <div class="stat-pill"><span class="stat-val">{total_segs:,}</span><span class="stat-lbl">Segments</span></div>
</div>""", unsafe_allow_html=True)

        search_tab, discover_tab = st.tabs(["🔍 Keyword Search", "🧠 Auto-Discover Themes"])

        # ── KEYWORD SEARCH ──
        with search_tab:
            st.markdown('<div class="card"><div class="card-title">🔍 Search Across All Transcripts</div>', unsafe_allow_html=True)

            col_kw, col_btn = st.columns([4, 1])
            with col_kw:
                keyword_input = st.text_input(
                    "Keyword or phrase",
                    placeholder="confidence, command, decision, helm, risk...",
                    label_visibility="collapsed",
                )
            with col_btn:
                search_btn = st.button("🔍  Search", use_container_width=True)

            # Quick-search buttons for seed terms
            st.markdown("**Quick search — Agency & Command Presence terms:**")
            quick_terms = ["confidence","command","decision","risk","calm","crew",
                           "leadership","weather","safety","anchor","helm","navigate"]
            cols = st.columns(6)
            for i, term in enumerate(quick_terms):
                with cols[i % 6]:
                    if st.button(term, key=f"quick_{term}"):
                        keyword_input = term
                        search_btn = True

            st.markdown("</div>", unsafe_allow_html=True)

            if search_btn and keyword_input.strip():
                results = search_transcripts(keyword_input.strip(), transcripts)

                if not results:
                    st.warning(f"No results found for **'{keyword_input}'** across {n_trans} transcripts.")
                else:
                    total_hits  = len(results)
                    videos_with = len(set(r["video_id"] for r in results))
                    top_count   = results[0]["count_in_video"] if results else 0

                    st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{total_hits}</span><span class="stat-lbl">Total Matches</span></div>
  <div class="stat-pill"><span class="stat-val">{videos_with}</span><span class="stat-lbl">Videos</span></div>
  <div class="stat-pill"><span class="stat-val">{top_count}</span><span class="stat-lbl">Most in One Video</span></div>
</div>""", unsafe_allow_html=True)

                    st.markdown(f"### Results for: **{keyword_input}**")

                    # Group by video for clean display
                    from itertools import groupby
                    results_by_video = {}
                    for r in results:
                        vid = r["video_id"]
                        if vid not in results_by_video:
                            results_by_video[vid] = []
                        results_by_video[vid].append(r)

                    for vid_id, vid_results in results_by_video.items():
                        count = vid_results[0]["count_in_video"]
                        title = vid_results[0]["title"]
                        url   = vid_results[0]["url"]

                        with st.expander(f"📹 {title[:70]}  [{count} matches]", expanded=(count == top_count)):
                            for r in vid_results:
                                st.markdown(
                                    f"<div class='result-row'>"
                                    f"<span class='result-ts'>⏱ {r['timestamp']}</span> &nbsp;"
                                    f"<span class='result-excerpt'>{r['excerpt']}</span>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
                            st.markdown(f"<a href='{url}' target='_blank' style='font-size:.75rem;color:#5ba4d4;'>▶ Watch on YouTube</a>", unsafe_allow_html=True)

                    # Download results as CSV
                    csv_lines = ["Video Title,Timestamp,Excerpt,Count in Video"]
                    for r in results:
                        excerpt_clean = r["excerpt"].replace('"','""').replace("\n"," ")
                        title_clean   = r["title"].replace('"','""')
                        csv_lines.append(f'"{title_clean}","{r["timestamp"]}","{excerpt_clean}",{r["count_in_video"]}')
                    csv_data = "\n".join(csv_lines)

                    st.download_button(
                        f"⬇️ Download '{keyword_input}' results as CSV",
                        data=csv_data,
                        file_name=f"MAIC_search_{keyword_input.replace(' ','_')}.csv",
                        mime="text/csv",
                    )

        # ── AUTO-DISCOVER THEMES ──
        with discover_tab:
            st.markdown('<div class="card"><div class="card-title">🧠 Auto-Discover Themes — Inductive Analysis</div>', unsafe_allow_html=True)
            st.markdown(
                "<div style='font-size:.85rem;color:#8fbcd4;margin-bottom:.8rem;'>"
                "This surfaces the most frequent meaningful words across your entire corpus — "
                "without you pre-deciding what to look for. "
                "This is your <strong style='color:#c9a84c;'>inductive coding</strong> starting point."
                "</div>",
                unsafe_allow_html=True,
            )

            top_n = st.slider("Number of terms to surface", min_value=20, max_value=100, value=50, step=10)

            if st.button("🧠  Discover Top Terms", use_container_width=True):
                with st.spinner("Analyzing corpus..."):
                    discovered = auto_discover_terms(transcripts, top_n=top_n)

                if discovered:
                    st.markdown(f"### Top {len(discovered)} terms across your corpus")
                    st.markdown("<div style='font-size:.8rem;color:#8fbcd4;margin-bottom:.8rem;'>Click any term to search for it in the Keyword Search tab.</div>", unsafe_allow_html=True)

                    # Display as categorized chips + table
                    categories = {}
                    for word, count in discovered:
                        cat = categorize_discovered_term(word)
                        if cat not in categories:
                            categories[cat] = []
                        categories[cat].append((word, count))

                    for cat, terms in sorted(categories.items()):
                        st.markdown(f"**{cat}**")
                        chips = " ".join(
                            f"<span class='keyword-chip'>{w} <strong style='color:#c9a84c'>{c}</strong></span>"
                            for w, c in sorted(terms, key=lambda x: -x[1])
                        )
                        st.markdown(chips, unsafe_allow_html=True)
                        st.markdown("")

                    # Full table
                    with st.expander("📊 Full frequency table"):
                        table_lines = ["Term,Frequency,Category"]
                        for word, count in discovered:
                            cat = categorize_discovered_term(word)
                            table_lines.append(f'"{word}",{count},"{cat}"')
                        csv_disc = "\n".join(table_lines)
                        st.download_button(
                            "⬇️ Download discovery table as CSV",
                            data=csv_disc,
                            file_name="MAIC_auto_discovery.csv",
                            mime="text/csv",
                        )
                        for word, count in discovered:
                            cat = categorize_discovered_term(word)
                            st.markdown(
                                f"<div style='font-size:.8rem;padding:.2rem 0;border-bottom:1px solid #1b3a5c;'>"
                                f"<strong style='color:#c9a84c;'>{word}</strong> "
                                f"<span style='color:#8fbcd4;'>{count}×</span> "
                                f"<span style='color:#5ba4d4;font-size:.72rem;'>{cat}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GEMINI VIDEO PROMPT
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
<div class="maic-hero" style="margin-bottom:1rem;">
  <h1 style="font-size:1.4rem;">🎬 Gemini Multimodal Video Analysis</h1>
  <p>Gemini 1.5 Pro can <strong>watch YouTube videos directly</strong> and code for
  posture, facial expression, voice tone, helm behavior, and crew dynamics —
  everything a transcript misses. Paste the generated prompt into
  <a href="https://gemini.google.com" style="color:#c9a84c;">gemini.google.com</a>.</p>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🎬 Enter Video URL</div>', unsafe_allow_html=True)

    gem_url = st.text_input(
        "YouTube video URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
        key="gem_url",
    )

    gem_notes = st.text_area(
        "Researcher context (optional)",
        placeholder="e.g., Focus on the skipper's posture and facial expression during the storm at around 15 minutes. Note any co-occupation moments with crew.",
        height=80,
        key="gem_notes",
    )

    # If transcripts loaded, show a picker to use a loaded video
    if st.session_state.transcripts:
        st.markdown("**Or pick from your loaded transcripts:**")
        video_options = ["— select —"] + [
            f"{d['title'][:60]}" for d in st.session_state.transcripts.values()
        ]
        picked = st.selectbox("Select a loaded video", video_options, label_visibility="collapsed")
        if picked != "— select —":
            for vid_id, d in st.session_state.transcripts.items():
                if d["title"][:60] == picked:
                    gem_url = d["url"]
                    break

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🎬  Generate Gemini Coding Prompt", use_container_width=True, key="gem_btn"):
        if not gem_url.strip():
            st.error("Please enter a YouTube video URL.")
        else:
            gem_prompt = build_gemini_prompt(gem_url.strip(), gem_notes)

            st.markdown("""
<div style="background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.4);
     border-radius:8px;padding:.7rem 1rem;font-size:.85rem;color:#c9a84c;margin:.8rem 0;">
  ✅ Prompt ready. Copy it and paste into
  <a href="https://gemini.google.com" target="_blank" style="color:#e8c96a;font-weight:600;">gemini.google.com</a>
  using <strong>Gemini 1.5 Pro</strong>.
  Gemini will watch the full video and return timestamped coding for posture,
  facial expression, voice, helm behavior, and crew dynamics.
</div>
""", unsafe_allow_html=True)

            st.text_area(
                "Gemini Prompt",
                value=gem_prompt,
                height=350,
                label_visibility="collapsed",
                key="gem_output",
            )

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                vid_match = re.search(r"v=([A-Za-z0-9_\-]{11})", gem_url)
                vid_slug  = vid_match.group(1) if vid_match else "video"
                st.download_button(
                    "⬇️ Download Gemini Prompt as .txt",
                    data=gem_prompt,
                    file_name=f"MAIC_Gemini_{vid_slug}.txt",
                    mime="text/plain",
                )

            st.markdown("""
<div class="card" style="margin-top:1rem;">
<div class="card-title">🧭 How to Use Gemini</div>
<div style="font-size:.85rem;color:#d6eaf8;line-height:1.9;">
  <strong style="color:#c9a84c;">1</strong> — Go to
  <a href="https://gemini.google.com" style="color:#5ba4d4;">gemini.google.com</a>
  and sign in with a Google account<br>
  <strong style="color:#c9a84c;">2</strong> — Select <strong>Gemini 1.5 Pro</strong>
  from the model dropdown (free tier)<br>
  <strong style="color:#c9a84c;">3</strong> — Paste the entire prompt above into the chat<br>
  <strong style="color:#c9a84c;">4</strong> — Gemini watches the video and returns
  a timestamped table of coded moments<br>
  <strong style="color:#c9a84c;">5</strong> — Section 5 of Gemini's output
  ("What the Transcript Misses") is your key evidence for multimodal methodology<br><br>
  <span style="color:#8fbcd4;font-size:.78rem;">
  Use the keyword search (Tab 2) first to find which video has the richest
  transcript data — then use Gemini on that video for deep multimodal coding.
  </span>
</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MAIC TRANSCRIPT PROMPTS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    if not st.session_state.transcripts:
        st.info("⚓ No transcripts loaded yet. Go to Tab 1 first.")
    else:
        st.markdown('<div class="card"><div class="card-title">📄 Generate MAIC Prompts for Loaded Transcripts</div>', unsafe_allow_html=True)

        researcher_notes = st.text_area(
            "Research notes (embedded in every prompt)",
            placeholder="e.g., Analyzing SV Delos for post-work identity and command presence themes...",
            height=70,
        )

        if st.button("⚓  Generate All MAIC Prompts", use_container_width=True):
            st.session_state.prompts = {}
            progress = st.progress(0)
            items = list(st.session_state.transcripts.items())

            for i, (vid_id, data) in enumerate(items):
                video_dict = {"title": data["title"], "url": data["url"]}
                prompt = build_maic_prompt(video_dict, data["segments"], researcher_notes)
                st.session_state.prompts[vid_id] = {"prompt": prompt, "title": data["title"]}
                progress.progress((i + 1) / len(items))

            st.success(f"✅ {len(st.session_state.prompts)} prompts generated!")

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.prompts:
            # ZIP download
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for vid_id, r in st.session_state.prompts.items():
                    safe = re.sub(r"[^\w\s\-]", "", r["title"])[:50].strip().replace(" ", "_")
                    zf.writestr(f"MAIC_{safe}_{vid_id}.txt", r["prompt"])
            zip_buf.seek(0)
            slug = re.sub(r"[^\w\-]", "_", st.session_state.channel_name)[:30]

            st.download_button(
                f"⬇️  Download All {len(st.session_state.prompts)} Prompts as ZIP",
                data=zip_buf,
                file_name=f"MAIC_{slug}_{len(st.session_state.prompts)}prompts.zip",
                mime="application/zip",
                use_container_width=True,
            )

            st.markdown("<br>**Preview individual prompts:**")
            for vid_id, r in st.session_state.prompts.items():
                with st.expander(f"📄 {r['title'][:70]}"):
                    st.text_area(
                        "Prompt",
                        value=r["prompt"],
                        height=260,
                        label_visibility="collapsed",
                        key=f"ta_{vid_id}",
                    )
                    safe = re.sub(r"[^\w\s\-]", "", r["title"])[:50].strip().replace(" ", "_")
                    st.download_button(
                        "⬇️ Download this prompt",
                        data=r["prompt"],
                        file_name=f"MAIC_{safe}_{vid_id}.txt",
                        mime="text/plain",
                        key=f"dl_{vid_id}",
                    )

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#2e6da4;font-size:.75rem;padding:1rem 0 .5rem;border-top:1px solid #1b3a5c;">
  🚢 MAIC Channel Analyzer v2.0 · UFT AI Development Course · Occupational Science PhD · Zero API Cost
</div>
""", unsafe_allow_html=True)
