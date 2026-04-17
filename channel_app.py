"""
MAIC Channel Analyzer v3.0
===========================
Maritime Agency & Identity Classifier — Full Research Pipeline

NEW IN v3.0:
  - Tab 1: Find Channels (keyword search + curated list by population)
  - Tab 2: Load Channel & Fetch Transcripts
  - Tab 3: Search & Auto-Discover Themes
  - Tab 4: Smart Video Selection (scores corpus, recommends top 3-10 for Gemini)
  - Tab 5: Gemini Video Analysis (automated API — no copy-paste required)
  - Tab 6: Synthesis (combines transcript + video findings)
  - Tab 7: MAIC Transcript Prompts (full 4-lens prompt generator)

Author: PhD Candidate | Occupational Science | UFT AI Development Course
"""

import streamlit as st
import scrapetube
import re
import io
import zipfile
import time
import collections
import json
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from typing import Optional

# Optional imports with graceful fallback
try:
    from youtubesearchpython import ChannelsSearch
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MAIC v3.0 · Maritime Agency & Identity Classifier",
    page_icon="⚓",
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
    --chalk:#f0f4f8; --coral:#e05555; --green:#1d9e75; --radius:10px;
  }
  html,body,[class*="css"]{font-family:'Source Sans 3',sans-serif;background-color:var(--navy)!important;color:var(--chalk);}
  .block-container{padding:1.5rem 2rem 3rem;max-width:1200px;}

  .maic-hero{background:linear-gradient(135deg,#0d1b2a 0%,#1b3a5c 60%,#0d2d4a 100%);border:1px solid var(--steel);border-radius:var(--radius);padding:1.4rem 2rem 1.2rem;margin-bottom:1.2rem;position:relative;overflow:hidden;}
  .maic-hero::before{content:"⚓";font-size:6rem;opacity:.05;position:absolute;right:1rem;top:-0.5rem;line-height:1;}
  .maic-hero h1{font-family:'Cinzel',serif;font-size:1.5rem;font-weight:900;color:var(--brass);letter-spacing:.05em;margin:0 0 .25rem;}
  .maic-hero p{font-size:.85rem;color:var(--foam);opacity:.85;max-width:750px;line-height:1.5;margin:0;}

  .card{background:var(--ocean);border:1px solid #2a4d6e;border-radius:var(--radius);padding:1.2rem 1.5rem;margin-bottom:1rem;}
  .card-title{font-family:'Cinzel',serif;font-size:.78rem;letter-spacing:.1em;color:var(--brass);text-transform:uppercase;margin-bottom:.75rem;}

  .stTextInput>div>div>input,.stTextArea textarea,.stNumberInput input{background-color:#0d1b2a!important;border:1px solid var(--steel)!important;color:var(--chalk)!important;border-radius:6px!important;}
  .stButton>button{background:#c9a84c!important;border:2px solid #e8c96a!important;color:#1a0f00!important;font-family:'Cinzel',serif!important;font-weight:700!important;letter-spacing:.06em!important;font-size:.83rem!important;border-radius:6px!important;}
  .stButton>button:hover{background:#e0b94a!important;transform:translateY(-1px);}
  .stProgress>div>div{background-color:var(--brass)!important;}
  .stCheckbox label{color:var(--chalk)!important;}

  [data-testid="stSidebar"]{background:#07111e!important;border-right:1px solid #1b3a5c;}
  [data-testid="stSidebar"] *{color:var(--chalk)!important;}
  [data-testid="stSidebar"] h3{font-family:'Cinzel',serif!important;color:var(--brass)!important;}

  .stat-row{display:flex;gap:.7rem;flex-wrap:wrap;margin:.4rem 0 .9rem;}
  .stat-pill{background:rgba(46,109,164,.25);border:1px solid var(--steel);border-radius:8px;padding:.4rem .85rem;text-align:center;}
  .stat-val{font-family:'Cinzel',serif;font-size:1.1rem;color:var(--brass);font-weight:700;}
  .stat-lbl{font-size:.66rem;color:var(--wake);letter-spacing:.05em;text-transform:uppercase;}

  .channel-card{background:#0d1b2a;border:1px solid #2a4d6e;border-radius:8px;padding:.8rem 1rem;margin-bottom:.5rem;cursor:pointer;transition:border-color .15s;}
  .channel-card:hover{border-color:var(--wake);}
  .channel-name{font-weight:600;color:var(--foam);font-size:.88rem;}
  .channel-meta{font-size:.75rem;color:#8fbcd4;margin-top:.2rem;}
  .channel-badge{display:inline-block;background:rgba(201,168,76,.15);border:1px solid rgba(201,168,76,.3);border-radius:10px;padding:.15rem .55rem;font-size:.7rem;color:var(--brass);margin:.15rem .1rem 0 0;}

  .score-bar-bg{background:#1b3a5c;border-radius:4px;height:8px;margin-top:.3rem;}
  .score-bar-fill{background:var(--brass);border-radius:4px;height:8px;}

  .gemini-result{background:#07111e;border:1px solid var(--steel);border-radius:8px;padding:1rem 1.2rem;font-size:.82rem;color:#d6eaf8;line-height:1.65;max-height:400px;overflow-y:auto;}
  .result-section{border-left:3px solid var(--brass);padding-left:.8rem;margin:.7rem 0;}
  .result-section-title{font-family:'Cinzel',serif;font-size:.75rem;color:var(--brass);letter-spacing:.07em;text-transform:uppercase;margin-bottom:.3rem;}

  .error-row{font-size:.8rem;color:var(--coral);}
  .success-row{font-size:.8rem;color:#5dcaa5;}
  hr{border-color:#2a4d6e!important;}
  ::-webkit-scrollbar{width:5px;}
  ::-webkit-scrollbar-track{background:#07111e;}
  ::-webkit-scrollbar-thumb{background:var(--steel);border-radius:3px;}

  .stTabs [data-baseweb="tab-list"]{background:#07111e;border-radius:8px 8px 0 0;border:1px solid #2a4d6e;border-bottom:none;}
  .stTabs [data-baseweb="tab"]{color:#8fbcd4!important;font-family:'Cinzel',serif!important;font-size:.72rem!important;letter-spacing:.05em!important;padding:.5rem .9rem!important;}
  .stTabs [aria-selected="true"]{color:var(--brass)!important;border-bottom:2px solid var(--brass)!important;}

  .pipeline-step{display:flex;align-items:center;gap:.5rem;padding:.3rem 0;font-size:.82rem;color:#8fbcd4;}
  .pipeline-step.active{color:var(--brass);}
  .pipeline-step.done{color:#5dcaa5;}
  .step-dot{width:10px;height:10px;border-radius:50%;background:#2a4d6e;flex-shrink:0;}
  .step-dot.active{background:var(--brass);}
  .step-dot.done{background:#5dcaa5;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_defaults = {
    "videos":           [],
    "channel_name":     "",
    "channel_url":      "",
    "transcripts":      {},
    "top_videos":       [],        # scored & ranked video dicts
    "gemini_results":   {},        # vid_id -> {analysis, title, score, url}
    "synthesis":        "",        # combined synthesis text
    "prompts":          {},        # MAIC 4-lens prompts
    "gemini_api_key":   "",
    "loaded":           False,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# CURATED CHANNEL LIST
# ─────────────────────────────────────────────────────────────────────────────
CURATED_CHANNELS = {
    "🦾 Adaptive & Accessible Sailing": [
        {
            "name": "Impossible Dream Catamaran",
            "url": "https://www.youtube.com/@ImpossibleDreamCatamaran",
            "description": "World's only universally accessible 60-ft catamaran. Wheelchair users at the helm. Shake-A-Leg Miami. Primary dissertation data source.",
            "tags": ["adaptive", "wheelchair", "co-occupation", "D1", "A5"]
        },
        {
            "name": "Blind Sailing International",
            "url": "https://www.youtube.com/@blindsailinginternational",
            "description": "Visually impaired sailors racing and cruising. Sensory adaptation, tactile navigation, command presence without sight.",
            "tags": ["adaptive", "blind", "sensory", "D1", "A4"]
        },
        {
            "name": "Shake-A-Leg Miami",
            "url": "https://www.youtube.com/@ShakeALegMiami",
            "description": "Community adaptive sailing & aquatics. OT connections, peer-mediated participation, occupational justice.",
            "tags": ["adaptive", "community", "OT", "D3", "occupational justice"]
        },
        {
            "name": "Disabled Sailing Association",
            "url": "https://www.youtube.com/@disabledsailingassociation",
            "description": "UK-based adaptive sailing programs. Training, racing, and access to the water for disabled sailors.",
            "tags": ["adaptive", "UK", "racing", "D1", "D2"]
        },
    ],
    "⚓ Experienced Sailors (Baseline)": [
        {
            "name": "SV Delos",
            "url": "https://www.youtube.com/@svdelos",
            "description": "14+ years bluewater cruising. Post-work identity, passage planning, Command Presence in real conditions. 529+ episodes.",
            "tags": ["baseline", "offshore", "identity", "C1", "B4", "E1"]
        },
        {
            "name": "Sailing La Vagabonde",
            "url": "https://www.youtube.com/@SailingLaVagabonde",
            "description": "Family liveaboard sailing. Co-occupation, meaning-making, child-rearing at sea. Strong Lens 1 & Lens 2 data.",
            "tags": ["baseline", "family", "identity", "A5", "C2", "E1"]
        },
        {
            "name": "Sailing Uma",
            "url": "https://www.youtube.com/@SailingUma",
            "description": "Couple sailing a steel ketch. Extensive boat work, decision-making narration, weather routing transparency.",
            "tags": ["baseline", "decision-making", "A2", "B4"]
        },
        {
            "name": "Andy & Sheryl / Far Reach Sailing",
            "url": "https://www.youtube.com/@FarReachSailing",
            "description": "Offshore passages with explicit seamanship narration. COLREGS, weather decisions, watch-keeping. Strong Lens 3 data.",
            "tags": ["baseline", "seamanship", "offshore", "B3", "B4", "B1"]
        },
    ],
    "🎓 USCG / CTE / Instruction": [
        {
            "name": "NauticEd Sailing",
            "url": "https://www.youtube.com/@NauticEd",
            "description": "Structured sailing instruction. COLREGS, anchoring, docking, rules of the road. Direct USCG OUPV curriculum alignment.",
            "tags": ["CTE", "USCG", "instruction", "B3", "B4"]
        },
        {
            "name": "Sailing World",
            "url": "https://www.youtube.com/@SailingWorld",
            "description": "Racing and cruising technique. Tactical decision-making, boat handling, crew communication.",
            "tags": ["CTE", "racing", "technique", "B2", "B1"]
        },
    ],
    "🌊 Heavy Weather / Decision-Making": [
        {
            "name": "Sailing Nahoa",
            "url": "https://www.youtube.com/@SailingNahoa",
            "description": "Pacific cruising with detailed passage narration. Weather decisions and risk assessment explicitly discussed.",
            "tags": ["heavy weather", "B4", "A2", "B5"]
        },
        {
            "name": "Gone with the Wynns",
            "url": "https://www.youtube.com/@GoneWithTheWynns",
            "description": "Catamaran liveaboard with accessible presentation style. Good for meaning-making and identity narratives.",
            "tags": ["baseline", "catamaran", "C2", "E1"]
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# COMMAND PRESENCE TERMS & SCORING
# ─────────────────────────────────────────────────────────────────────────────
COMMAND_PRESENCE_TERMS = [
    "decision","authority","responsibility","situational awareness","judgment",
    "calm","composure","navigation","bearing","helm","crew","watch","weather",
    "risk","safety","protocol","right of way","stand-on","give-way","collision",
    "COLREGS","VHF","mayday","distress","anchor","throttle","trim","capsize",
    "rescue","PFD","command","leadership","skipper","captain","communication",
    "confidence","adapt","assess","plan","execute","debrief","mistake","tack",
    "jibe","reef","passage","offshore","bearing","course","chart","waypoint",
    "visibility","squall","gust","swell","current",
]

HIGH_VALUE_TITLE_KEYWORDS = [
    "passage", "offshore", "storm", "decision", "rough", "crossing",
    "emergency", "weather", "command", "heavy", "adaptive", "disability",
    "wheelchair", "accessible", "blind", "rescue", "capsize", "survival",
    "leadership", "crew", "seamanship", "night", "watch", "helm",
]

STOP_WORDS = set("""
a about above after again against all also am an and any are aren't as at be
because been before being below between both but by can can't cannot could
couldn't did didn't do does doesn't doing don't down during each few for from
further get got had hadn't has hasn't have haven't having he he'd he'll he's
her here here's hers herself him himself his how i i'd i'll i'm i've if in
into is isn't it it's its itself just let me more most my myself no nor not
now of off on once only or other our out over own same she should so some such
than that the their them themselves then there these they this those through
to too under until up very was we were what when where which while who will
with would you your yeah okay actually really like just kind sort thing things
way one two three four five six seven eight nine ten
""".split())

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
    def normalize(entries):
        result = []
        for entry in entries:
            if isinstance(entry, dict):
                result.append(entry)
            else:
                try:
                    result.append({
                        "text":     getattr(entry, "text", str(entry)),
                        "start":    float(getattr(entry, "start", 0.0)),
                        "duration": float(getattr(entry, "duration", 0.0)),
                    })
                except Exception:
                    result.append({"text": str(entry), "start": 0.0, "duration": 0.0})
        return result

    for method in [
        lambda: normalize(YouTubeTranscriptApi.get_transcript(video_id, languages=["en","en-US","en-GB"])),
        lambda: normalize(YouTubeTranscriptApi.get_transcript(video_id)),
    ]:
        try:
            return method()
        except Exception:
            pass

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


def build_segments(raw: list) -> list:
    def secs_to_ts(s):
        s = int(s)
        h, m, sec = s//3600, (s%3600)//60, s%60
        return f"{h}:{m:02d}:{sec:02d}" if h > 0 else f"{m}:{sec:02d}"

    segments, buf_text, buf_start = [], [], 0.0
    for i, entry in enumerate(raw):
        text = re.sub(r"\[.*?\]", "", entry.get("text",""))
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        if not buf_text:
            buf_start = entry.get("start", 0.0)
        buf_text.append(text)
        joined = " ".join(buf_text)
        if len(buf_text) >= 3 or (joined and joined[-1] in ".!?"):
            segments.append({"text": joined, "start": buf_start, "timestamp": secs_to_ts(buf_start)})
            buf_text, buf_start = [], 0.0
    if buf_text:
        segments.append({"text": " ".join(buf_text), "start": buf_start, "timestamp": secs_to_ts(buf_start)})
    return segments


def duration_to_minutes(d: str) -> int:
    parts = d.strip().split(":")
    try:
        if len(parts) == 3: return int(parts[0])*60 + int(parts[1])
        if len(parts) == 2: return int(parts[0])
    except Exception:
        pass
    return 0


def score_video_for_gemini(video: dict, transcripts: dict) -> dict:
    """
    Score a video for Gemini analysis value.
    Returns dict with score breakdown and total.
    """
    vid_id = video["video_id"]
    breakdown = {}

    # 1. Duration score (sweet spot: 20-60 min)
    minutes = duration_to_minutes(video["duration"])
    dur_score = min(minutes, 60) // 3  # max 20 pts
    breakdown["duration"] = dur_score

    # 2. Transcript keyword density
    kw_score = 0
    if vid_id in transcripts:
        full_text = " ".join(s["text"].lower() for s in transcripts[vid_id]["segments"])
        matched = sum(1 for t in COMMAND_PRESENCE_TERMS if t.lower() in full_text)
        kw_score = min(matched * 2, 40)  # max 40 pts
    breakdown["keyword_density"] = kw_score

    # 3. Title keywords
    title_lower = video["title"].lower()
    title_score = sum(5 for kw in HIGH_VALUE_TITLE_KEYWORDS if kw in title_lower)
    title_score = min(title_score, 25)  # max 25 pts
    breakdown["title_relevance"] = title_score

    # 4. View count (proxy for content quality)
    views_str = video.get("views", "0")
    try:
        views = int(re.sub(r"[^\d]", "", views_str))
        if views > 500000: view_score = 15
        elif views > 100000: view_score = 10
        elif views > 50000: view_score = 7
        elif views > 10000: view_score = 4
        else: view_score = 1
    except Exception:
        view_score = 0
    breakdown["view_popularity"] = view_score

    total = sum(breakdown.values())
    breakdown["total"] = total
    return breakdown


def search_youtube_channels(query: str, limit: int = 8):
    if not SEARCH_AVAILABLE:
        return []
    try:
        results = ChannelsSearch(query, limit=limit)
        data = results.getNextPage()
        channels = []
        for item in data.get("result", []):
            custom_url = item.get("customUrl", "") or ""
            url = f"https://www.youtube.com/{custom_url}" if custom_url else f"https://www.youtube.com/channel/{item.get('id','')}"
            channels.append({
                "name":        item.get("title", "Unknown Channel"),
                "url":         url,
                "description": item.get("descriptionSnippet", {}).get("text", "") if isinstance(item.get("descriptionSnippet"), dict) else str(item.get("descriptionSnippet", "")),
                "subscribers": item.get("subscribers", ""),
                "id":          item.get("id", ""),
            })
        return channels
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI API VIDEO ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_VIDEO_PROMPT_TEMPLATE = """
You are a qualitative research assistant for a PhD dissertation in Occupational Science.
The researcher is a licensed USCG Captain and NYC occupational therapist studying how sailors
develop AGENCY and COMMAND PRESENCE — and how these can be taught to adaptive sailors
and high school CTE students.

Watch the ENTIRE video at the URL provided. Then produce ALL six sections below.

================================================================================
CODING GUIDE

Code every moment showing evidence of:

AGENCY+ (purposeful, self-directed action):
- Environmental scanning before acting
- Explicit decision narration: "I decided...", "We chose..."
- Improvised problem-solving
- Self-correction after mistakes
- Anticipatory sail trim, course changes, preparation

AGENCY- (reactive, hesitant, or absent agency):
- Surprised by foreseeable conditions
- Freezing or avoidance at decision points
- Delegating all judgment to instruments

CP+ (Command Presence — positive):
POSTURE: upright stable stance, relaxed grip, head up scanning, squared shoulders
FACE: neutral/focused expression under stress, controlled breathing, composure
VOICE: steady pitch/pace, short clear commands, intentional silence, authority without aggression
CREW: crew looks to subject for cues, smooth handoffs, crew body language relaxes

CP- (Command Presence — absent):
- Collapsed or braced posture under pressure
- White-knuckle grip suggesting fear
- Voice rising in pitch/pace, shouting, vague commands
- Crew looking at each other instead of subject

================================================================================
SECTION 1 — TIMESTAMPED CODING TABLE (minimum 20 rows)

| Timestamp | Code | Channel (V/VI/P) | What You See/Hear | Analytical Note |

V=Verbal  VI=Visual  P=Paralinguistic

================================================================================
SECTION 2 — FREQUENCY SUMMARY

| Code | Count | % of total | Peak timestamp |
AGENCY+ ratio: ____%   CP+ ratio: ____%

================================================================================
SECTION 3 — TOP 5 MOMENTS FOR CTE TEACHING
For each: Timestamp | What is happening | Why it matters for USCG OUPV students | Discussion question | Photovoice prompt for adaptive sailors

================================================================================
SECTION 4 — ABSENCE & NEGATIVE CASES
3-5 moments of AGENCY- or CP-. What is the sailor doing or failing to do?
How does crew respond? What would Command Presence look like at this moment?

================================================================================
SECTION 5 — WHAT THE TRANSCRIPT MISSES
3-5 moments where VISUAL or PARALINGUISTIC data tells a richer story than words alone.
Timestamp | Words spoken | What video shows | Why this matters methodologically

================================================================================
SECTION 6 — DISSERTATION MEMO (250-350 words)
1. Overall assessment of agency and command presence
2. Most significant finding — what surprised you
3. Relationship between verbal and nonverbal channels
4. Connection to post-work sailing identity
5. Recommended use: CTE case study / photovoice seed / longitudinal data point
6. Command Presence Composite Score (0-100) with rationale

================================================================================
VIDEO URL: {video_url}
TITLE: {title}
RESEARCHER CONTEXT: {researcher_notes}
================================================================================

Watch the full video and produce all six sections.
"""


def analyze_with_gemini_api(video_url: str, title: str, api_key: str,
                             researcher_notes: str = "") -> str:
    """
    Call Gemini API to analyze a YouTube video.
    Returns the analysis text or raises an exception.
    """
    if not GEMINI_AVAILABLE:
        raise ImportError("google-generativeai package not installed")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")

    prompt = GEMINI_VIDEO_PROMPT_TEMPLATE.format(
        video_url=video_url,
        title=title,
        researcher_notes=researcher_notes.strip() or "No additional context provided.",
    )

    # Try method 1: Pass YouTube URL as file data part
    try:
        response = model.generate_content(
            [
                {
                    "role": "user",
                    "parts": [
                        {"file_data": {"file_uri": video_url, "mime_type": "video/mp4"}},
                        {"text": prompt},
                    ],
                }
            ],
            generation_config={"max_output_tokens": 8192, "temperature": 0.3},
        )
        return response.text
    except Exception:
        pass

    # Try method 2: Inline URL in prompt text (Gemini can follow YouTube links)
    try:
        full_prompt = f"Please watch this YouTube video: {video_url}\n\n{prompt}"
        response = model.generate_content(
            full_prompt,
            generation_config={"max_output_tokens": 8192, "temperature": 0.3},
        )
        return response.text
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)[:200]}")


def auto_discover_terms(transcripts: dict, top_n: int = 60):
    word_counts = collections.Counter()
    for data in transcripts.values():
        for seg in data["segments"]:
            for word in re.findall(r"[a-zA-Z']+", seg["text"].lower()):
                word = word.strip("'")
                if len(word) >= 4 and word not in STOP_WORDS:
                    word_counts[word] += 1
    return word_counts.most_common(top_n)


def categorize_term(word: str) -> str:
    agency = {"decided","decision","chose","choice","plan","confident","confidence",
               "control","managed","adapted","solved","skill","leadership","command",
               "captain","helm","navigate","navigation","responsible","responsibility"}
    emotion = {"scared","fear","calm","panic","anxious","stressed","worried","nervous",
                "comfortable","trust","focused","determined","proud","overwhelmed","peaceful"}
    technical = {"wind","sail","tack","jibe","reef","anchor","chart","gps","compass",
                  "bearing","knots","miles","weather","storm","wave","swell","engine",
                  "autopilot","vhf","mayday","colregs","vessel","boat"}
    identity = {"life","home","family","freedom","dream","adventure","meaning","purpose",
                 "belong","community","ocean","sailing","sailor","offshore","voyage","journey"}
    w = word.lower()
    if w in agency:   return "🎯 Agency / Command"
    if w in emotion:  return "💭 Emotional / Psychological"
    if w in technical:return "⚙️ Technical / Seamanship"
    if w in identity: return "⚓ Identity / Meaning"
    return "📌 Uncategorized"


def search_transcripts(keyword: str, transcripts: dict) -> list:
    kw = keyword.strip().lower()
    if not kw:
        return []
    counts = {vid: sum(1 for s in d["segments"] if kw in s["text"].lower())
              for vid, d in transcripts.items()}
    results = []
    for vid_id, data in transcripts.items():
        for seg in data["segments"]:
            if kw in seg["text"].lower():
                excerpt = re.sub(re.escape(keyword), f"**{keyword.upper()}**", seg["text"], flags=re.IGNORECASE)
                results.append({
                    "video_id": vid_id, "title": data["title"],
                    "url": data["url"], "timestamp": seg["timestamp"],
                    "start": seg["start"], "excerpt": excerpt,
                    "count_in_video": counts[vid_id],
                })
    results.sort(key=lambda r: (-r["count_in_video"], r["start"]))
    return results


def build_maic_prompt(video: dict, segments: list, notes: str = "") -> str:
    terms = "\n".join(f"   - {t}" for t in COMMAND_PRESENCE_TERMS)
    segs  = "\n".join(f"\n--- SEGMENT {i+1} | {s['timestamp']} ---\n{s['text']}"
                      for i, s in enumerate(segments))
    wc    = sum(len(s["text"].split()) for s in segments)
    notes_block = f"\nRESEARCHER NOTES:\n{notes.strip()}\n" if notes.strip() else ""
    return f"""MARITIME AGENCY & IDENTITY CLASSIFIER (MAIC) v3.0
Qualitative Analysis Prompt — Occupational Science Dissertation

SOURCE : {video['url']}
TITLE  : {video['title']}
WORDS  : {wc:,} across {len(segments)} segments
{notes_block}
=============================================================================
LENS 1 — Post-Work Occupational Identity (Wilcock: doing-being-belonging-becoming)
  a) Language describing why they sail?
  b) WORK, LEISURE, VOCATION, or hybrid framing?
  c) Temporal structure around sailing?
  d) Community/relational belonging?
  e) Occupational becoming — growth/transformation?
  f) AI/automation tools positioned how?
  g) Post-work thesis confidence: Low/Medium/High

LENS 2 — Occupational Justice, Ableism & Co-Occupation
  a) Disability, chronic illness, neurodivergence?
  b) Adaptive technologies?
  c) Environmental modifications?
  d) Co-occupation moments?
  e) Occupational injustice or exclusion?
  f) Ableist language?
  g) 3 photovoice prompts: "Photograph a moment when ___"

LENS 3 — USCG Command Presence: CTE Case Studies
  a) 3-6 critical incidents — segment|description|USCG competency|discussion Q
  b) Rule-based navigation decisions?
  c) Weather decision-making?
  d) Crew leadership moments?
  e) Mistakes reflected upon — learning loop?
  f) CTE utility rating 1-10

LENS 4 — Command Presence Term Frequency
  Count: {terms}
  Output: | Rank | Term | Count | Timestamp | Category |
  Then: emergent terms, 10 photovoice prompts, 150-word curriculum synthesis.

FINAL SYNTHESIS — 300-word dissertation memo:
  1. Key findings | 2. Convergent themes | 3. Framework challenges
  4. 2-3 member-checking questions | 5. Analytical Richness Score 1-10

=============================================================================
TRANSCRIPT:
{segs}
=============================================================================
END — Produce full four-lens analysis.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚓ MAIC v3.0")
    st.markdown("**Research Pipeline:**")

    steps = [
        ("Find Channels",         st.session_state.channel_name != ""),
        ("Load & Fetch",          st.session_state.loaded),
        ("Search & Discover",     len(st.session_state.transcripts) > 0),
        ("Select Top Videos",     len(st.session_state.top_videos) > 0),
        ("Gemini Analysis",       len(st.session_state.gemini_results) > 0),
        ("Synthesis",             st.session_state.synthesis != ""),
        ("MAIC Prompts",          len(st.session_state.prompts) > 0),
    ]
    for label, done in steps:
        cls = "done" if done else "active" if not any(d for _, d in steps[:steps.index((label,done))]) else ""
        dot_cls = "done" if done else ""
        icon = "✅" if done else "○"
        st.markdown(
            f"<div class='pipeline-step {cls}'>{icon} {label}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Gemini API key input
    st.markdown("**🔑 Gemini API Key**")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.gemini_api_key,
        type="password",
        placeholder="AIza...",
        help="Free key from aistudio.google.com — enables automated video analysis",
        label_visibility="collapsed",
    )
    if api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input

    if st.session_state.gemini_api_key:
        st.markdown("<div class='success-row'>✅ Gemini API key set</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='error-row'>⚠️ No key — automated analysis disabled. "
            "<a href='https://aistudio.google.com' target='_blank' style='color:#5ba4d4;'>Get free key →</a></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.session_state.transcripts:
        n = len(st.session_state.transcripts)
        wc = sum(sum(len(s["text"].split()) for s in d["segments"])
                 for d in st.session_state.transcripts.values())
        st.markdown(
            f"<div style='font-size:.78rem;color:#8fbcd4;'>"
            f"<strong style='color:#c9a84c;'>Corpus:</strong><br>"
            f"{n} transcripts · {wc:,} words<br>"
            f"Channel: {st.session_state.channel_name}"
            f"</div>",
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="maic-hero">
  <h1>⚓ MAIC v3.0 · Maritime Agency & Identity Classifier</h1>
  <p>Full research pipeline: discover channels → load & analyze a corpus → auto-score videos →
  send top picks to Gemini for multimodal video coding → synthesize findings.
  Minimal copy-paste. Maximum dissertation data.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔍 Find Channels",
    "📡 Load Channel",
    "🔎 Search & Discover",
    "⭐ Select for Gemini",
    "🎬 Gemini Analysis",
    "📊 Synthesis",
    "📄 MAIC Prompts",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FIND CHANNELS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="card"><div class="card-title">🔍 Search YouTube for Channels</div>', unsafe_allow_html=True)

    col_q, col_btn = st.columns([4, 1])
    with col_q:
        search_query = st.text_input(
            "Search",
            placeholder="adaptive sailing, blind sailing, wheelchair catamaran, USCG instruction...",
            label_visibility="collapsed",
        )
    with col_btn:
        do_search = st.button("🔍 Search", use_container_width=True)

    if not SEARCH_AVAILABLE:
        st.info("Channel search requires `youtubesearchpython`. It will be installed automatically on Streamlit Cloud. If running locally: `pip install youtubesearchpython`")

    if do_search and search_query.strip():
        with st.spinner(f"Searching YouTube for '{search_query}'..."):
            results = search_youtube_channels(search_query.strip(), limit=8)
        if results:
            st.markdown(f"**{len(results)} channels found:**")
            for ch in results:
                col_info, col_load = st.columns([5, 1])
                with col_info:
                    st.markdown(
                        f"<div class='channel-card'>"
                        f"<div class='channel-name'>{ch['name']}</div>"
                        f"<div class='channel-meta'>{ch['url']}"
                        f"{' · ' + ch['subscribers'] if ch.get('subscribers') else ''}</div>"
                        f"<div class='channel-meta'>{ch.get('description','')[:120]}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with col_load:
                    if st.button("Load →", key=f"search_load_{ch['id']}"):
                        st.session_state.channel_url = ch["url"]
                        st.success(f"URL set! Go to **Load Channel** tab.")
        else:
            st.warning("No results. Try different keywords or paste a URL directly in the Load Channel tab.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Curated list ──
    st.markdown('<div class="card"><div class="card-title">📚 Curated Research Channels — by Population Group</div>', unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.82rem;color:#8fbcd4;margin-bottom:.8rem;'>"
        "Pre-vetted channels organized by your dissertation's three-group purposive sample. "
        "Click <strong>Load →</strong> to send directly to the Load Channel tab."
        "</div>",
        unsafe_allow_html=True,
    )

    for group_name, channels in CURATED_CHANNELS.items():
        st.markdown(f"**{group_name}**")
        for ch in channels:
            col_info, col_tags, col_load = st.columns([3, 2, 1])
            with col_info:
                st.markdown(
                    f"<div class='channel-name'>{ch['name']}</div>"
                    f"<div class='channel-meta'>{ch['description'][:100]}...</div>",
                    unsafe_allow_html=True,
                )
            with col_tags:
                badges = " ".join(f"<span class='channel-badge'>{t}</span>" for t in ch["tags"][:4])
                st.markdown(f"<div style='padding-top:.4rem'>{badges}</div>", unsafe_allow_html=True)
            with col_load:
                safe_key = re.sub(r"[^\w]", "_", ch["name"])
                if st.button("Load →", key=f"curated_{safe_key}"):
                    st.session_state.channel_url = ch["url"]
                    st.success(f"✅ '{ch['name']}' URL set — go to Load Channel tab.")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LOAD CHANNEL
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="card"><div class="card-title">📡 Load Channel & Fetch Transcripts</div>', unsafe_allow_html=True)

    col_url, col_limit = st.columns([3, 1])
    with col_url:
        channel_url_input = st.text_input(
            "Channel URL",
            value=st.session_state.channel_url,
            placeholder="https://www.youtube.com/@svdelos",
            label_visibility="collapsed",
            key="ch_url_input",
        )
    with col_limit:
        video_limit = st.number_input("Max videos", min_value=3, max_value=500, value=200, step=10)

    test_mode = st.checkbox("🧪 Test mode — 3 videos only (recommended for first run)", value=True)

    if st.button("📺  Load Channel Videos", use_container_width=True):
        url_to_use = channel_url_input.strip() or st.session_state.channel_url
        if not url_to_use:
            st.error("Please enter a channel URL or pick one from the Find Channels tab.")
        else:
            identifier, id_type = parse_channel_identifier(url_to_use)
            if not identifier:
                st.error("Could not parse that URL.")
            else:
                limit = 3 if test_mode else video_limit
                with st.spinner(f"Scanning {identifier} — loading up to {limit} videos..."):
                    try:
                        videos = fetch_channel_videos(identifier, id_type, limit=limit)
                        st.session_state.videos       = videos
                        st.session_state.channel_name = identifier
                        st.session_state.channel_url  = url_to_use
                        st.session_state.transcripts  = {}
                        st.session_state.loaded       = False
                        st.session_state.top_videos   = []
                        st.session_state.gemini_results = {}
                        st.session_state.synthesis    = ""
                        st.session_state.prompts      = {}
                        for v in videos:
                            key = f"chk_{v['video_id']}"
                            if key in st.session_state:
                                del st.session_state[key]
                        st.success(f"✅ Found {len(videos)} videos from **{identifier}**")
                    except Exception as e:
                        st.error(f"Could not load channel: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.videos:
        videos = st.session_state.videos

        st.markdown('<div class="card"><div class="card-title">☑️ Select Videos & Fetch Transcripts</div>', unsafe_allow_html=True)

        col_f1, col_f2, col_f3 = st.columns([2,1,1])
        with col_f1:
            search_filter = st.text_input("Filter by title", placeholder="Sailing Vessel Delos, storm...")
        with col_f2:
            min_min = st.number_input("Min duration (min)", min_value=0, max_value=120, value=0)
        with col_f3:
            sort_sel = st.selectbox("Sort", ["Newest first","Oldest first","Longest first"])

        filtered = [v for v in videos
                    if (not search_filter.strip() or search_filter.strip().lower() in v["title"].lower())
                    and duration_to_minutes(v["duration"]) >= min_min]
        if sort_sel == "Oldest first":    filtered = list(reversed(filtered))
        elif sort_sel == "Longest first": filtered = sorted(filtered, key=lambda v: duration_to_minutes(v["duration"]), reverse=True)

        all_sel = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]

        st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{len(videos)}</span><span class="stat-lbl">Loaded</span></div>
  <div class="stat-pill"><span class="stat-val">{len(filtered)}</span><span class="stat-lbl">Showing</span></div>
  <div class="stat-pill"><span class="stat-val">{len(all_sel)}</span><span class="stat-lbl">Selected</span></div>
  <div class="stat-pill"><span class="stat-val">{len(st.session_state.transcripts)}</span><span class="stat-lbl">Stored</span></div>
</div>""", unsafe_allow_html=True)

        c1, c2, _ = st.columns([1,1,4])
        with c1:
            if st.button("✅ Select all visible"):
                for v in filtered: st.session_state[f"chk_{v['video_id']}"] = True
                st.rerun()
        with c2:
            if st.button("✖️ Deselect all"):
                for v in videos: st.session_state[f"chk_{v['video_id']}"] = False
                st.rerun()

        for v in filtered:
            vid_id = v["video_id"]
            stored = " ✅" if vid_id in st.session_state.transcripts else ""
            col_chk, col_info = st.columns([0.05, 0.95])
            with col_chk:
                st.checkbox("Select", key=f"chk_{vid_id}", label_visibility="collapsed")
            with col_info:
                st.markdown(
                    f"**{v['title']}{stored}**  "
                    f"<span style='color:#8fbcd4;font-size:.76rem'>⏱ {v['duration']} | 📅 {v['date']} | 👁 {v['views']}</span>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

        all_sel = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]

        if all_sel:
            st.markdown('<div class="card"><div class="card-title">⬇️ Fetch & Store Transcripts</div>', unsafe_allow_html=True)
            st.info(f"**{len(all_sel)} videos selected.** Transcripts stored with timestamps for keyword search and scoring.")

            if st.button(f"⬇️  Fetch Transcripts for {len(all_sel)} Video{'s' if len(all_sel)!=1 else ''}", use_container_width=True):
                progress = st.progress(0)
                log = st.empty()
                lines = []

                for i, v in enumerate(all_sel):
                    vid_id = v["video_id"]
                    lines.append(f"🌊 {v['title'][:55]}...")
                    log.markdown("<br>".join(f"<div style='font-size:.78rem;color:#8fbcd4'>{l}</div>" for l in lines[-6:]), unsafe_allow_html=True)
                    try:
                        raw = fetch_transcript_raw(vid_id)
                        segs = build_segments(raw)
                        if len(segs) < 5: raise ValueError("Too few segments")
                        st.session_state.transcripts[vid_id] = {
                            "title": v["title"], "url": v["url"],
                            "duration": v["duration"], "date": v["date"],
                            "segments": segs,
                        }
                        wc = sum(len(s["text"].split()) for s in segs)
                        lines[-1] = f"✅ {v['title'][:50]} ({wc:,} words)"
                    except (TranscriptsDisabled, NoTranscriptFound):
                        lines[-1] = f"❌ No captions: {v['title'][:50]}"
                    except Exception as ex:
                        lines[-1] = f"⚠️ {v['title'][:45]}: {str(ex)[:40]}"
                    progress.progress((i+1)/len(all_sel))
                    log.markdown("<br>".join(f"<div style='font-size:.78rem;color:#8fbcd4'>{l}</div>" for l in lines[-6:]), unsafe_allow_html=True)
                    time.sleep(0.4)

                st.session_state.loaded = True
                n = len(st.session_state.transcripts)
                st.success(f"✅ {n} transcripts stored. Go to **Search & Discover** or **Select for Gemini** →")

            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SEARCH & DISCOVER
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.transcripts:
        st.info("⚓ Load transcripts first in the Load Channel tab.")
    else:
        transcripts = st.session_state.transcripts
        n_t = len(transcripts)
        total_w = sum(sum(len(s["text"].split()) for s in d["segments"]) for d in transcripts.values())
        total_s = sum(len(d["segments"]) for d in transcripts.values())

        st.markdown(f"""<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{n_t}</span><span class="stat-lbl">Transcripts</span></div>
  <div class="stat-pill"><span class="stat-val">{total_w:,}</span><span class="stat-lbl">Total Words</span></div>
  <div class="stat-pill"><span class="stat-val">{total_s:,}</span><span class="stat-lbl">Segments</span></div>
</div>""", unsafe_allow_html=True)

        search_tab, discover_tab = st.tabs(["🔍 Keyword Search", "🧠 Auto-Discover Themes"])

        with search_tab:
            st.markdown('<div class="card"><div class="card-title">🔍 Search Across All Transcripts</div>', unsafe_allow_html=True)
            col_kw, col_btn = st.columns([4,1])
            with col_kw:
                kw = st.text_input("Keyword", placeholder="confidence, command, decision, helm...", label_visibility="collapsed")
            with col_btn:
                do_s = st.button("🔍 Search", use_container_width=True, key="kw_search")

            st.markdown("**Quick search:**")
            quick_terms = ["confidence","command","decision","risk","calm","crew",
                           "leadership","weather","safety","anchor","helm","navigate"]
            cols = st.columns(6)
            for i, term in enumerate(quick_terms):
                with cols[i%6]:
                    if st.button(term, key=f"q_{term}"):
                        kw = term
                        do_s = True

            st.markdown("</div>", unsafe_allow_html=True)

            if do_s and kw.strip():
                results = search_transcripts(kw.strip(), transcripts)
                if not results:
                    st.warning(f"No results for **'{kw}'** across {n_t} transcripts.")
                else:
                    hits = len(results)
                    vids = len(set(r["video_id"] for r in results))
                    top  = results[0]["count_in_video"]
                    st.markdown(f"""<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{hits}</span><span class="stat-lbl">Matches</span></div>
  <div class="stat-pill"><span class="stat-val">{vids}</span><span class="stat-lbl">Videos</span></div>
  <div class="stat-pill"><span class="stat-val">{top}</span><span class="stat-lbl">Most in One Video</span></div>
</div>""", unsafe_allow_html=True)

                    by_video = {}
                    for r in results:
                        by_video.setdefault(r["video_id"], []).append(r)

                    for vid_id, vr in by_video.items():
                        count = vr[0]["count_in_video"]
                        with st.expander(f"📹 {vr[0]['title'][:70]}  [{count} matches]", expanded=(count == top)):
                            for r in vr:
                                st.markdown(
                                    f"<div class='result-row' style='background:#0d1b2a;border:1px solid #2a4d6e;border-radius:5px;padding:.4rem .7rem;margin-bottom:.3rem;'>"
                                    f"<span style='color:#5ba4d4;font-family:monospace;font-size:.75rem'>⏱ {r['timestamp']}</span>  "
                                    f"<span style='color:#d6eaf8;font-size:.82rem'>{r['excerpt']}</span>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )
                            st.markdown(f"<a href='{vr[0]['url']}' target='_blank' style='font-size:.75rem;color:#5ba4d4;'>▶ Watch on YouTube</a>", unsafe_allow_html=True)

                    csv = "Video Title,Timestamp,Excerpt,Count\n" + "\n".join(
                        f'"{r["title"].replace(chr(34),chr(39))}","{r["timestamp"]}","{r["excerpt"].replace(chr(34),chr(39))}",{r["count_in_video"]}'
                        for r in results
                    )
                    st.download_button(f"⬇️ Download '{kw}' results as CSV", data=csv,
                                       file_name=f"MAIC_{kw.replace(' ','_')}.csv", mime="text/csv")

        with discover_tab:
            st.markdown('<div class="card"><div class="card-title">🧠 Auto-Discover Themes — Inductive Analysis</div>', unsafe_allow_html=True)
            st.markdown("<div style='font-size:.83rem;color:#8fbcd4;margin-bottom:.7rem;'>Surfaces the most frequent meaningful words across your corpus without pre-deciding what to look for. Your inductive coding starting point.</div>", unsafe_allow_html=True)
            top_n = st.slider("Terms to surface", 20, 100, 50, 10)
            if st.button("🧠  Discover Top Terms", use_container_width=True):
                discovered = auto_discover_terms(transcripts, top_n=top_n)
                if discovered:
                    cats = {}
                    for word, count in discovered:
                        cat = categorize_term(word)
                        cats.setdefault(cat, []).append((word, count))
                    for cat, terms in sorted(cats.items()):
                        st.markdown(f"**{cat}**")
                        chips = " ".join(
                            f"<span style='display:inline-block;background:rgba(91,164,212,.12);border:1px solid #2e6da4;border-radius:12px;padding:.15rem .55rem;font-size:.75rem;color:#5ba4d4;margin:.15rem;'>"
                            f"{w} <strong style='color:#c9a84c'>{c}</strong></span>"
                            for w, c in sorted(terms, key=lambda x: -x[1])
                        )
                        st.markdown(chips, unsafe_allow_html=True)
                        st.markdown("")
                    csv_d = "Term,Frequency,Category\n" + "\n".join(
                        f'"{w}",{c},"{categorize_term(w)}"' for w,c in discovered
                    )
                    st.download_button("⬇️ Download discovery table as CSV", data=csv_d,
                                       file_name="MAIC_auto_discovery.csv", mime="text/csv")
            st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SELECT TOP VIDEOS FOR GEMINI
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    if not st.session_state.transcripts:
        st.info("⚓ Fetch transcripts first — the scoring engine needs them to rank videos.")
    else:
        st.markdown('<div class="card"><div class="card-title">⭐ Smart Video Scoring — Select Top Picks for Gemini</div>', unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:.83rem;color:#8fbcd4;margin-bottom:.8rem;'>"
            "MAIC scores every video with a stored transcript across four dimensions: "
            "keyword density, duration, title relevance, and view popularity. "
            "The top-ranked videos are your best candidates for Gemini's multimodal video analysis."
            "</div>",
            unsafe_allow_html=True,
        )

        col_n, col_btn = st.columns([2, 3])
        with col_n:
            top_n_sel = st.slider("Videos to recommend", min_value=3, max_value=10, value=5)
        with col_btn:
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            if st.button("⭐  Score & Rank All Videos", use_container_width=True):
                scored = []
                for vid_id, data in st.session_state.transcripts.items():
                    v_meta = next((v for v in st.session_state.videos if v["video_id"] == vid_id),
                                  {"video_id": vid_id, "title": data["title"], "url": data["url"],
                                   "duration": data.get("duration",""), "views": data.get("views",""), "date": data.get("date","")})
                    breakdown = score_video_for_gemini(v_meta, st.session_state.transcripts)
                    scored.append({**v_meta, "score_breakdown": breakdown, "total_score": breakdown["total"]})

                scored.sort(key=lambda x: -x["total_score"])
                st.session_state.top_videos = scored[:top_n_sel]

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.top_videos:
            st.markdown(f"### 🏆 Top {len(st.session_state.top_videos)} Videos Recommended for Gemini Analysis")
            max_score = max(v["total_score"] for v in st.session_state.top_videos) or 1

            for rank, v in enumerate(st.session_state.top_videos, 1):
                b = v["score_breakdown"]
                pct = int(v["total_score"] / max_score * 100)

                with st.expander(
                    f"#{rank}  {v['title'][:65]}  — Score: {v['total_score']}",
                    expanded=(rank <= 3),
                ):
                    col_meta, col_scores = st.columns([3, 2])
                    with col_meta:
                        st.markdown(
                            f"<div style='font-size:.82rem;color:#d6eaf8;line-height:1.8;'>"
                            f"⏱ {v.get('duration','')} &nbsp;|&nbsp; 📅 {v.get('date','')} &nbsp;|&nbsp; 👁 {v.get('views','')}<br>"
                            f"<a href='{v['url']}' target='_blank' style='color:#5ba4d4;font-size:.78rem;'>▶ Watch on YouTube</a>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    with col_scores:
                        for label, val, max_val in [
                            ("Keyword Density", b.get("keyword_density",0), 40),
                            ("Title Relevance", b.get("title_relevance",0), 25),
                            ("Duration",        b.get("duration",0), 20),
                            ("Popularity",      b.get("view_popularity",0), 15),
                        ]:
                            fill_pct = int(val / max_val * 100) if max_val else 0
                            st.markdown(
                                f"<div style='font-size:.72rem;color:#8fbcd4;margin-bottom:.1rem'>{label}: <strong style='color:#c9a84c'>{val}</strong>/{max_val}</div>"
                                f"<div class='score-bar-bg'><div class='score-bar-fill' style='width:{fill_pct}%'></div></div>",
                                unsafe_allow_html=True,
                            )

            st.markdown(
                "<div style='margin-top:.8rem;font-size:.83rem;color:#8fbcd4;'>"
                "✅ These videos are queued for Gemini analysis. Go to the <strong>Gemini Analysis</strong> tab to run them. →"
                "</div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — GEMINI ANALYSIS (AUTOMATED)
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="card"><div class="card-title">🎬 Automated Gemini Video Analysis</div>', unsafe_allow_html=True)

    if not st.session_state.top_videos:
        st.info("⭐ Score and select top videos in the **Select for Gemini** tab first.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='font-size:.83rem;color:#8fbcd4;margin-bottom:.8rem;'>"
            "MAIC sends each selected video to the Gemini API automatically. "
            "Gemini watches the full video and returns timestamped multimodal coding "
            "across verbal, visual, and paralinguistic channels. "
            "<strong>No copy-paste required.</strong>"
            "</div>",
            unsafe_allow_html=True,
        )

        if not st.session_state.gemini_api_key:
            st.warning(
                "⚠️ **Gemini API key required.** Add your free key in the sidebar. "
                "Get one at [aistudio.google.com](https://aistudio.google.com) — "
                "takes 2 minutes, no credit card needed."
            )

        researcher_notes = st.text_area(
            "Researcher context (embedded in every Gemini prompt)",
            placeholder="e.g., Focus on command presence moments. Note any co-occupation between disabled and non-disabled crew. Researcher is a licensed USCG Captain and OT studying adaptive sailing.",
            height=70,
            key="gem_notes_auto",
        )

        st.markdown(f"**{len(st.session_state.top_videos)} videos queued:**")
        for v in st.session_state.top_videos:
            done = v["video_id"] in st.session_state.gemini_results
            icon = "✅" if done else "○"
            st.markdown(
                f"<div style='font-size:.82rem;color:{'#5dcaa5' if done else '#8fbcd4'};padding:.15rem 0;'>"
                f"{icon} {v['title'][:70]}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

        col_run, col_clear = st.columns([3,1])
        with col_run:
            run_gemini = st.button(
                f"🎬  Analyze {len(st.session_state.top_videos)} Video{'s' if len(st.session_state.top_videos)!=1 else ''} with Gemini",
                use_container_width=True,
                disabled=not st.session_state.gemini_api_key,
            )
        with col_clear:
            if st.button("🗑 Clear Results", use_container_width=True):
                st.session_state.gemini_results = {}
                st.session_state.synthesis = ""
                st.rerun()

        if run_gemini and st.session_state.gemini_api_key:
            progress = st.progress(0)
            status   = st.empty()
            n_vids   = len(st.session_state.top_videos)

            for i, v in enumerate(st.session_state.top_videos):
                vid_id = v["video_id"]
                if vid_id in st.session_state.gemini_results:
                    progress.progress((i+1)/n_vids)
                    continue

                status.markdown(
                    f"<div style='font-size:.85rem;color:#c9a84c;'>"
                    f"🎬 Analyzing ({i+1}/{n_vids}): <strong>{v['title'][:60]}</strong>...</div>",
                    unsafe_allow_html=True,
                )

                try:
                    analysis = analyze_with_gemini_api(
                        video_url       = v["url"],
                        title           = v["title"],
                        api_key         = st.session_state.gemini_api_key,
                        researcher_notes= researcher_notes,
                    )
                    st.session_state.gemini_results[vid_id] = {
                        "analysis": analysis,
                        "title":    v["title"],
                        "url":      v["url"],
                        "score":    v["total_score"],
                    }
                    status.markdown(
                        f"<div style='font-size:.85rem;color:#5dcaa5;'>✅ Done: {v['title'][:60]}</div>",
                        unsafe_allow_html=True,
                    )
                except Exception as ex:
                    err_msg = str(ex)[:200]
                    st.session_state.gemini_results[vid_id] = {
                        "error":  err_msg,
                        "title":  v["title"],
                        "url":    v["url"],
                        "score":  v["total_score"],
                    }
                    status.markdown(
                        f"<div style='font-size:.83rem;color:#e05555;'>⚠️ Error on {v['title'][:50]}: {err_msg[:80]}</div>",
                        unsafe_allow_html=True,
                    )

                progress.progress((i+1)/n_vids)
                # Rate limit: 2 requests/min on free tier
                if i < n_vids - 1:
                    time.sleep(32)

            status.markdown("<div style='font-size:.9rem;color:#5dcaa5;font-weight:600;'>✅ All videos processed. Go to Synthesis tab →</div>", unsafe_allow_html=True)
            st.rerun()

        # ── Display results ──
        successful = {k:r for k,r in st.session_state.gemini_results.items() if "analysis" in r}
        failed     = {k:r for k,r in st.session_state.gemini_results.items() if "error" in r}

        if successful:
            st.markdown(f"### 📋 Gemini Analysis Results ({len(successful)} complete)")
            for vid_id, r in successful.items():
                with st.expander(f"🎬 {r['title'][:70]}", expanded=False):
                    st.markdown(f"<a href='{r['url']}' target='_blank' style='font-size:.75rem;color:#5ba4d4;'>▶ Watch on YouTube</a>", unsafe_allow_html=True)
                    st.text_area(
                        "Analysis",
                        value=r["analysis"],
                        height=300,
                        label_visibility="collapsed",
                        key=f"gem_ta_{vid_id}",
                    )
                    safe = re.sub(r"[^\w\s\-]","",r["title"])[:50].strip().replace(" ","_")
                    st.download_button(
                        "⬇️ Download this analysis",
                        data=r["analysis"],
                        file_name=f"MAIC_Gemini_{safe}_{vid_id}.txt",
                        mime="text/plain",
                        key=f"gem_dl_{vid_id}",
                    )

        if failed:
            st.markdown("**Videos that could not be analyzed:**")
            for r in failed.values():
                st.markdown(f"<div class='error-row'>❌ {r['title'][:65]} — {r.get('error','Unknown error')[:100]}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — SYNTHESIS
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    successful_gem = {k:r for k,r in st.session_state.gemini_results.items() if "analysis" in r}

    if not successful_gem and not st.session_state.transcripts:
        st.info("⚓ Complete transcript analysis and Gemini video analysis first, then return here for synthesis.")
    else:
        st.markdown('<div class="card"><div class="card-title">📊 Cross-Video Synthesis</div>', unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:.83rem;color:#8fbcd4;margin-bottom:.8rem;'>"
            "Combine findings across all analyzed videos. Generate a synthesis prompt "
            "for Claude that integrates transcript data and Gemini video coding results "
            "into a coherent dissertation-ready analysis."
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(f"""<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{len(st.session_state.transcripts)}</span><span class="stat-lbl">Transcripts</span></div>
  <div class="stat-pill"><span class="stat-val">{len(successful_gem)}</span><span class="stat-lbl">Gemini Analyses</span></div>
  <div class="stat-pill"><span class="stat-val">{len(st.session_state.channel_name and [1] or [])}</span><span class="stat-lbl">Channel</span></div>
</div>""", unsafe_allow_html=True)

        if st.button("📊  Build Synthesis Prompt for Claude", use_container_width=True):
            synth_parts = [
                "MAIC CROSS-VIDEO SYNTHESIS PROMPT",
                "=" * 60,
                f"Channel: {st.session_state.channel_name}",
                f"Transcripts analyzed: {len(st.session_state.transcripts)}",
                f"Gemini video analyses: {len(successful_gem)}",
                "",
                "You are synthesizing multimodal qualitative research data for a PhD dissertation",
                "in Occupational Science on sailor agency, command presence, and adaptive sailing.",
                "",
                "=" * 60,
                "TASK: Produce a cross-video synthesis addressing:",
                "",
                "1. CONVERGENT THEMES — What patterns appear consistently across multiple videos?",
                "   Focus on: agency expression, command presence indicators, identity language,",
                "   occupational justice moments, co-occupation dynamics.",
                "",
                "2. DIVERGENT CASES — Where do videos contradict each other or your framework?",
                "   Note: negative cases are as theoretically rich as positive ones.",
                "",
                "3. THE HAPTIC-VISUAL LOOP & OTHER EMBODIED FINDINGS",
                "   Identify any emergent concepts that transcend individual videos.",
                "   Specifically note where visual/paralinguistic data diverged from transcript data.",
                "",
                "4. COMMAND PRESENCE COMPOSITE SCORE COMPARISON",
                "   If CPCS scores are available from Gemini analyses, compare across videos.",
                "   What predicts higher CPCS? Channel type? Video context? Sailor experience?",
                "",
                "5. ADAPTIVE SAILING IMPLICATIONS",
                "   What does this corpus tell us about occupational justice in sailing?",
                "   What structural/environmental factors enable or constrain adaptive sailor agency?",
                "",
                "6. PHOTOVOICE PROMPT SYNTHESIS",
                "   Across all videos, what are the 10 most powerful photovoice prompts",
                "   that emerged? Frame each as: 'Photograph a moment when...'",
                "",
                "7. CURRICULUM IMPLICATIONS",
                "   Based on the entire corpus, draft 3 learning objectives for a USCG OUPV",
                "   CTE curriculum that would develop command presence in both able-bodied",
                "   and adaptive sailors.",
                "",
                "=" * 60,
                "DATA FROM TRANSCRIPT ANALYSIS:",
                "",
            ]

            for vid_id, data in st.session_state.transcripts.items():
                wc = sum(len(s["text"].split()) for s in data["segments"])
                synth_parts.append(f"[TRANSCRIPT] {data['title']}")
                synth_parts.append(f"  Words: {wc:,} | URL: {data['url']}")
                synth_parts.append("")

            if successful_gem:
                synth_parts += ["", "=" * 60, "DATA FROM GEMINI VIDEO ANALYSIS:", ""]
                for vid_id, r in successful_gem.items():
                    synth_parts.append(f"[GEMINI ANALYSIS] {r['title']}")
                    synth_parts.append(f"  URL: {r['url']}")
                    synth_parts.append(f"  Score: {r.get('score','N/A')}")
                    # Include first 800 chars of each analysis as context
                    preview = r["analysis"][:800].replace("\n", " ")
                    synth_parts.append(f"  Analysis preview: {preview}...")
                    synth_parts.append("")

            synth_parts += [
                "=" * 60,
                "Please produce a comprehensive cross-video synthesis addressing all 7 points above.",
                "Write in formal academic qualitative research voice appropriate for a dissertation.",
                "=" * 60,
            ]

            st.session_state.synthesis = "\n".join(synth_parts)

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.synthesis:
            st.markdown("### 📋 Synthesis Prompt — Paste into Claude.ai")
            st.text_area(
                "Synthesis Prompt",
                value=st.session_state.synthesis,
                height=320,
                label_visibility="collapsed",
                key="synth_output",
            )
            st.download_button(
                "⬇️ Download Synthesis Prompt as .txt",
                data=st.session_state.synthesis,
                file_name=f"MAIC_Synthesis_{st.session_state.channel_name}.txt",
                mime="text/plain",
            )
            st.markdown(
                "<div style='font-size:.82rem;color:#8fbcd4;margin-top:.5rem;'>"
                "Paste this into <a href='https://claude.ai' target='_blank' style='color:#5ba4d4;'>Claude.ai</a> "
                "for a dissertation-ready cross-video synthesis."
                "</div>",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — MAIC TRANSCRIPT PROMPTS
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    if not st.session_state.transcripts:
        st.info("⚓ Load transcripts first.")
    else:
        st.markdown('<div class="card"><div class="card-title">📄 Generate MAIC 4-Lens Prompts</div>', unsafe_allow_html=True)
        researcher_notes_p = st.text_area(
            "Research notes (embedded in every prompt)",
            placeholder="e.g., Analyzing SV Delos for post-work identity and command presence...",
            height=65,
        )
        if st.button("⚓  Generate All MAIC Prompts", use_container_width=True):
            st.session_state.prompts = {}
            prog = st.progress(0)
            items = list(st.session_state.transcripts.items())
            for i, (vid_id, data) in enumerate(items):
                v_dict = {"title": data["title"], "url": data["url"]}
                st.session_state.prompts[vid_id] = {
                    "prompt": build_maic_prompt(v_dict, data["segments"], researcher_notes_p),
                    "title":  data["title"],
                }
                prog.progress((i+1)/len(items))
            st.success(f"✅ {len(st.session_state.prompts)} prompts generated!")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.prompts:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for vid_id, r in st.session_state.prompts.items():
                    safe = re.sub(r"[^\w\s\-]","",r["title"])[:50].strip().replace(" ","_")
                    zf.writestr(f"MAIC_{safe}_{vid_id}.txt", r["prompt"])
            zip_buf.seek(0)
            slug = re.sub(r"[^\w\-]","_",st.session_state.channel_name)[:30]
            st.download_button(
                f"⬇️  Download All {len(st.session_state.prompts)} Prompts as ZIP",
                data=zip_buf,
                file_name=f"MAIC_{slug}_{len(st.session_state.prompts)}prompts.zip",
                mime="application/zip",
                use_container_width=True,
            )
            for vid_id, r in st.session_state.prompts.items():
                with st.expander(f"📄 {r['title'][:70]}"):
                    st.text_area("Prompt", value=r["prompt"], height=260,
                                 label_visibility="collapsed", key=f"pt_{vid_id}")
                    safe = re.sub(r"[^\w\s\-]","",r["title"])[:50].strip().replace(" ","_")
                    st.download_button("⬇️ Download", data=r["prompt"],
                                       file_name=f"MAIC_{safe}_{vid_id}.txt",
                                       mime="text/plain", key=f"pdl_{vid_id}")

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#2e6da4;font-size:.74rem;padding:.8rem 0 .4rem;border-top:1px solid #1b3a5c;">
  ⚓ MAIC v3.0 · Maritime Agency & Identity Classifier · UFT AI Development Course · Occupational Science PhD · Zero-Cost Pipeline
</div>
""", unsafe_allow_html=True)
