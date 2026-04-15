"""
MAIC Channel Analyzer
=====================
Batch qualitative research pre-processor for entire YouTube channels.
Lists all videos, lets researcher select targets, and generates
MAIC analysis prompts in bulk — zero API cost.

Author: Built for PhD Candidate | Occupational Science | UFT AI Development Course
"""

import streamlit as st
import scrapetube
import re
import io
import zipfile
import time
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
    page_title="MAIC Channel Analyzer",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
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

  .maic-hero{background:linear-gradient(135deg,#0d1b2a 0%,#1b3a5c 60%,#0d2d4a 100%);border:1px solid var(--steel);border-radius:var(--radius);padding:2rem 2.5rem 1.6rem;margin-bottom:1.5rem;position:relative;overflow:hidden;}
  .maic-hero::before{content:"🚢";font-size:8rem;opacity:.05;position:absolute;right:1.5rem;top:-1rem;line-height:1;}
  .maic-hero h1{font-family:'Cinzel',serif;font-size:1.8rem;font-weight:900;color:var(--brass);letter-spacing:.05em;margin:0 0 .3rem;}
  .maic-hero .subtitle{font-size:.92rem;color:var(--foam);opacity:.85;max-width:700px;line-height:1.55;}
  .badge-row{margin-top:.8rem;display:flex;gap:.5rem;flex-wrap:wrap;}
  .badge{background:rgba(91,164,212,.18);border:1px solid var(--wake);border-radius:20px;padding:.25rem .75rem;font-size:.72rem;color:var(--wake);}

  .card{background:var(--ocean);border:1px solid #2a4d6e;border-radius:var(--radius);padding:1.4rem 1.8rem;margin-bottom:1.2rem;}
  .card-title{font-family:'Cinzel',serif;font-size:.82rem;letter-spacing:.1em;color:var(--brass);text-transform:uppercase;margin-bottom:.9rem;}

  .stTextInput>div>div>input,.stTextArea textarea{background-color:#0d1b2a!important;border:1px solid var(--steel)!important;color:var(--chalk)!important;border-radius:6px!important;}
  .stButton>button{background:linear-gradient(135deg,var(--steel),var(--ocean))!important;border:1px solid var(--wake)!important;color:white!important;border-radius:6px!important;font-family:'Cinzel',serif!important;letter-spacing:.06em!important;font-size:.82rem!important;}

  /* PRIMARY brass button */
  .stButton>button[kind="primary"],div[data-testid="stButton"]>button:first-child{background:linear-gradient(135deg,#c9a84c,#a07830)!important;border:2px solid #e8c96a!important;color:#1a0f00!important;font-weight:700!important;}

  .stDataFrame{border-radius:8px!important;}
  .stProgress>div>div{background-color:var(--brass)!important;}
  .stCheckbox label{color:var(--chalk)!important;}

  [data-testid="stSidebar"]{background:#07111e!important;border-right:1px solid #1b3a5c;}
  [data-testid="stSidebar"] *{color:var(--chalk)!important;}
  [data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{font-family:'Cinzel',serif!important;color:var(--brass)!important;}

  .stat-row{display:flex;gap:.8rem;flex-wrap:wrap;margin:.5rem 0 1rem;}
  .stat-pill{background:rgba(46,109,164,.25);border:1px solid var(--steel);border-radius:8px;padding:.4rem .9rem;text-align:center;}
  .stat-val{font-family:'Cinzel',serif;font-size:1.2rem;color:var(--brass);font-weight:700;}
  .stat-lbl{font-size:.68rem;color:var(--wake);letter-spacing:.05em;text-transform:uppercase;}

  .video-row{background:#0d1b2a;border:1px solid #2a4d6e;border-radius:6px;padding:.6rem 1rem;margin-bottom:.4rem;display:flex;align-items:center;gap:.8rem;cursor:pointer;transition:border-color .15s;}
  .video-row:hover{border-color:var(--wake);}
  .video-row.selected{border-color:var(--brass);background:rgba(201,168,76,.08);}
  .vr-thumb{width:80px;height:45px;border-radius:4px;object-fit:cover;flex-shrink:0;background:#1b3a5c;}
  .vr-title{font-size:.85rem;color:var(--chalk);font-weight:600;flex:1;line-height:1.35;}
  .vr-meta{font-size:.72rem;color:#8fbcd4;white-space:nowrap;}
  .vr-badge{font-size:.68rem;background:rgba(91,164,212,.15);border:1px solid #2e6da4;border-radius:10px;padding:.15rem .5rem;color:var(--wake);}

  .phase-header{font-family:'Cinzel',serif;font-size:.95rem;color:var(--brass);letter-spacing:.08em;text-transform:uppercase;border-bottom:1px solid #2a4d6e;padding-bottom:.5rem;margin-bottom:1rem;}
  .progress-item{font-size:.82rem;color:var(--foam);padding:.25rem 0;display:flex;align-items:center;gap:.5rem;}
  .progress-item .pi-icon{width:18px;text-align:center;}
  .result-prompt{background:#07111e;border:1px solid var(--steel);border-radius:8px;padding:1rem 1.2rem;font-family:'Courier New',monospace;font-size:.75rem;color:#a8d8f0;white-space:pre-wrap;max-height:300px;overflow-y:auto;line-height:1.55;}
  .error-row{font-size:.8rem;color:var(--coral);padding:.2rem 0;}

  hr{border-color:#2a4d6e!important;}
  ::-webkit-scrollbar{width:6px;height:6px;}
  ::-webkit-scrollbar-track{background:#07111e;}
  ::-webkit-scrollbar-thumb{background:var(--steel);border-radius:3px;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COMMAND PRESENCE TERMS (shared with MAIC)
# ─────────────────────────────────────────────────────────────────────────────
COMMAND_PRESENCE_TERMS = [
    "decision","authority","responsibility","situation awareness","situational awareness",
    "judgment","calm","composure","navigation","chart","bearing","helm","crew","watch",
    "weather","risk","safe","safety","protocol","rule","right of way","stand-on",
    "give-way","collision","COLREGS","VHF","mayday","pan-pan","distress","anchor",
    "dock","moor","throttle","trim","heel","capsize","rescue","PFD","life jacket",
    "command","lead","leadership","skipper","captain","mate","communication","confidence",
    "adapt","assess","plan","execute","debrief","lesson","mistake","correct",
    "tack","jibe","reef",
]

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def parse_channel_identifier(url: str) -> tuple[Optional[str], str]:
    """
    Return (identifier_value, identifier_type) from a channel URL.
    Types: 'channel' (@handle or /channel/ID), 'url'
    """
    url = url.strip().rstrip("/")

    # @handle  e.g. youtube.com/@svdelos
    m = re.search(r"youtube\.com/@([\w\-]+)", url)
    if m:
        return m.group(1), "channel_username"

    # /channel/UC...
    m = re.search(r"youtube\.com/channel/(UC[\w\-]+)", url)
    if m:
        return m.group(1), "channel_id"

    # /c/name or /user/name
    m = re.search(r"youtube\.com/(?:c|user)/([\w\-]+)", url)
    if m:
        return m.group(1), "channel_username"

    # bare @handle
    m = re.match(r"@?([\w\-]+)$", url)
    if m:
        return m.group(1), "channel_username"

    return None, "unknown"


def fetch_channel_videos(identifier: str, id_type: str, limit: int = 300) -> list[dict]:
    """Use scrapetube to pull video list from a channel."""
    videos = []
    if id_type == "channel_id":
        gen = scrapetube.get_channel(channel_id=identifier, limit=limit)
    else:
        gen = scrapetube.get_channel(channel_username=identifier, limit=limit)

    for v in gen:
        vid_id   = v.get("videoId", "")
        title    = ""
        duration = ""
        views    = ""
        date_str = ""

        # title
        runs = v.get("title", {}).get("runs", [])
        if runs:
            title = runs[0].get("text", "")

        # duration
        dl = v.get("lengthText", {}).get("simpleText", "")
        if dl:
            duration = dl

        # views
        vl = v.get("viewCountText", {}).get("simpleText", "")
        if vl:
            views = vl

        # published date
        pt = v.get("publishedTimeText", {}).get("simpleText", "")
        if pt:
            date_str = pt

        if vid_id and title:
            videos.append({
                "video_id": vid_id,
                "title":    title,
                "duration": duration,
                "views":    views,
                "date":     date_str,
                "url":      f"https://www.youtube.com/watch?v={vid_id}",
            })
    return videos


def fetch_transcript(video_id: str) -> list[dict]:
    tl = YouTubeTranscriptApi.list_transcripts(video_id)
    for attempt in [
        lambda t: t.find_manually_created_transcript(["en","en-US","en-GB"]),
        lambda t: t.find_generated_transcript(["en","en-US","en-GB"]),
        lambda t: next(iter(t)),
    ]:
        try:
            return attempt(tl).fetch()
        except Exception:
            continue
    raise NoTranscriptFound(video_id, ["en"], {})


def clean_transcript(raw: list[dict]) -> str:
    parts = []
    for entry in raw:
        text = re.sub(r"\[.*?\]", "", entry.get("text",""))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            parts.append(text)
    return re.sub(r" {2,}", " ", " ".join(parts)).strip()


def chunk_text(text: str, chunk_size: int = 800) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 <= chunk_size:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s if len(s) <= chunk_size else s[:chunk_size]
    if current:
        chunks.append(current)
    return chunks


def build_prompt(video: dict, cleaned: str, chunks: list[str],
                 researcher_notes: str = "", chunk_size: int = 800) -> str:
    terms = "\n".join(f"   • {t}" for t in COMMAND_PRESENCE_TERMS)
    chunks_section = "\n".join(
        f"\n--- SEGMENT {i} of {len(chunks)} ---\n{c}" for i, c in enumerate(chunks, 1)
    )
    notes_block = (
        f"\n\n**RESEARCHER'S NOTES:**\n{researcher_notes.strip()}\n"
        if researcher_notes.strip() else ""
    )

    return f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      MARITIME AGENCY & IDENTITY CLASSIFIER (MAIC) — CHANNEL BATCH         ║
║      Qualitative Analysis Prompt — Occupational Science Dissertation       ║
╚══════════════════════════════════════════════════════════════════════════════╝

SOURCE VIDEO : {video['url']}
TITLE        : {video['title']}
DURATION     : {video['duration']}
PUBLISHED    : {video['date']}
WORD COUNT   : {len(cleaned.split()):,} words across {len(chunks)} segments
GENERATED BY : MAIC Channel Analyzer v1.0
{notes_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## RESEARCH CONTEXT

You are assisting a PhD candidate in Occupational Science who is also a licensed
USCG Captain and NYC public school occupational therapist. This transcript is
part of a batch channel analysis for a dissertation on:

  1. Sailor occupational identity and meaning in a post-labor world
  2. Adaptive technologies and co-occupational partnerships in sailing
  3. Command Presence competencies for USCG OUPV (6-Pack) CTE pedagogy
  4. Photovoice methodology for adaptive sailor empowerment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 1 — Post-Work Occupational Identity & Meaning-Making

Apply Wilcock's doing-being-belonging-becoming model.

  a) What language does the subject use to describe why they sail?
  b) Is sailing framed as WORK, LEISURE, VOCATION, or hybrid?
  c) How does the subject structure time around sailing?
  d) What community or relational belonging does sailing provide?
  e) Evidence of occupational becoming — growth or transformation of self?
  f) How are AI/automation tools (autopilot, routing apps) positioned?
  g) Rate your confidence this supports the post-work thesis (Low/Medium/High).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 2 — Occupational Justice, Ableism & Co-Occupation

  a) Any mentions of disability, chronic illness, injury, or neurodivergence?
  b) Adaptive technologies described or implied?
  c) Environmental modifications to vessel or marina?
  d) Co-occupation moments — two+ people completing a task together?
  e) Expressions of occupational injustice or exclusion?
  f) Any ableist language — even unintentional?
  g) Generate 3 photovoice prompts: "Photograph a moment when ___________"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 3 — USCG Command Presence: CTE Teaching Case Studies

  a) Identify 3–6 critical incidents of decision-making or leadership.
     For each: segment reference | description | USCG competency | discussion Q
  b) Rule-based navigation decisions (COLREGS, VHF, anchoring, right of way)?
  c) Weather decision-making (go/no-go, reefing, seeking shelter)?
  d) Crew leadership moments (briefing, debriefing, managing fear)?
  e) Mistakes made and reflected upon — describe the learning loop.
  f) Rate utility as USCG CTE teaching resource (1–10) with rationale.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 4 — Ethnographic Command Presence Term Frequency

  STEP 1: Count occurrences of each seed term + semantic variants:
{terms}

  STEP 2: Output ranked table (highest frequency first):
  | Rank | Term | Count | Segments | Command Presence Category |

  Categories: SITUATIONAL AWARENESS | DECISION-MAKING UNDER PRESSURE |
  CREW LEADERSHIP & COMMUNICATION | REGULATORY/USCG COMPLIANCE |
  RISK ASSESSMENT & SEAMANSHIP | EMOTIONAL REGULATION | TECHNICAL SKILL

  STEP 3: List emergent terms not in the seed list with counts and rationale.
  STEP 4: Generate 10 photovoice prompts from the top 10 terms.
  STEP 5: 150–200 word curriculum synthesis.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FINAL SYNTHESIS

Write a 300–400 word dissertation memo covering:
  1. Most significant findings across all four lenses
  2. Convergent themes appearing across multiple lenses
  3. Data that challenges or complicates the theoretical framework
  4. 2–3 member-checking interview questions for this sailor
  5. Analytical Richness Score (1–10) with rationale

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TRANSCRIPT DATA

{chunks_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF TRANSCRIPT. Please produce your full four-lens qualitative analysis.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()


def duration_to_minutes(duration_str: str) -> int:
    """Convert HH:MM:SS or MM:SS string to total minutes."""
    parts = duration_str.strip().split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 2:
            return int(parts[0])
        return 0
    except Exception:
        return 0


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
if "videos" not in st.session_state:
    st.session_state.videos = []
if "selected_ids" not in st.session_state:
    st.session_state.selected_ids = set()
if "results" not in st.session_state:
    st.session_state.results = {}   # video_id -> {"prompt": str, "error": str}
if "channel_name" not in st.session_state:
    st.session_state.channel_name = ""

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚢 Channel Analyzer")
    st.markdown("""
**MAIC — Batch Mode**

Analyze entire YouTube channels for your Occupational Science dissertation.

---
### How It Works

1. Paste a channel URL
2. Browse the full video table
3. Filter & select your targets
4. Click **Analyze Selected**
5. Download all prompts as a ZIP

---
### Tips for Delos / Large Channels
- Filter by **minimum duration** to skip shorts
- Sort by **oldest first** for longitudinal analysis
- Select 5–10 videos at a time for best results

---
### Then Paste Into
- [Claude.ai](https://claude.ai) *(recommended)*
- [ChatGPT](https://chat.openai.com)
- [Gemini](https://gemini.google.com)
""")
    st.markdown("---")
    st.markdown(
        "<small style='color:#5ba4d4'>MAIC Channel Analyzer v1.0<br>"
        "PhD Candidate · Occupational Science<br>"
        "UFT AI Development Course</small>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="maic-hero">
  <h1>🚢 MAIC Channel Analyzer</h1>
  <div class="subtitle">
    Paste any YouTube channel URL — browse all videos in a sortable table,
    select the ones relevant to your research, and generate MAIC qualitative
    analysis prompts in bulk. Download everything as a ZIP file.
  </div>
  <div class="badge-row">
    <span class="badge">📺 Full Channel Scrape</span>
    <span class="badge">☑️ Batch Selection</span>
    <span class="badge">⬇️ ZIP Download</span>
    <span class="badge">💰 Zero API Cost</span>
    <span class="badge">200+ Video Channels</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — CHANNEL INPUT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">📡 Phase 1 — Enter Channel URL</div>', unsafe_allow_html=True)

col_url, col_limit = st.columns([3, 1])
with col_url:
    channel_url = st.text_input(
        "Channel URL",
        placeholder="https://www.youtube.com/@svdelos  or  https://www.youtube.com/channel/UC...",
        label_visibility="collapsed",
    )
with col_limit:
    video_limit = st.number_input(
        "Max videos to load",
        min_value=10,
        max_value=500,
        value=200,
        step=10,
        help="Larger channels can have 300+ videos. Start with 200 and increase if needed.",
    )

load_btn = st.button("📺  Load Channel Videos", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

if load_btn:
    if not channel_url.strip():
        st.error("⚠️  Please enter a YouTube channel URL.")
    else:
        identifier, id_type = parse_channel_identifier(channel_url.strip())
        if not identifier:
            st.error("⚠️  Could not parse a channel from that URL. Try the format: https://www.youtube.com/@channelname")
        else:
            with st.spinner(f"🌊  Scanning channel — loading up to {video_limit} videos..."):
                try:
                    videos = fetch_channel_videos(identifier, id_type, limit=video_limit)
                    st.session_state.videos = videos
                    st.session_state.selected_ids = set()
                    st.session_state.results = {}
                    st.session_state.channel_name = identifier
                    st.success(f"✅  Found {len(videos)} videos from **{identifier}**")
                except Exception as e:
                    st.error(f"❌  Could not load channel: {e}")
                    st.info("Make sure the channel URL is public and uses the format: https://www.youtube.com/@channelname")

# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — VIDEO TABLE & SELECTION
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.videos:
    videos = st.session_state.videos

    st.markdown('<div class="card"><div class="card-title">☑️ Phase 2 — Browse & Select Videos</div>', unsafe_allow_html=True)

    # ── Stats ──
    total = len(videos)
    selected_count = len(st.session_state.selected_ids)
    st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{total}</span><span class="stat-lbl">Total Videos</span></div>
  <div class="stat-pill"><span class="stat-val">{selected_count}</span><span class="stat-lbl">Selected</span></div>
</div>
""", unsafe_allow_html=True)

    # ── Filters ──
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search_q = st.text_input("🔍 Search titles", placeholder="e.g. storm, anchor, sailing")
    with col_f2:
        min_minutes = st.number_input("Min duration (minutes)", min_value=0, max_value=120, value=10,
                                       help="Filter out short videos and YouTube Shorts")
    with col_f3:
        sort_order = st.selectbox("Sort by", ["Newest first", "Oldest first", "Longest first", "Shortest first"])

    # Apply filters
    filtered = videos
    if search_q.strip():
        q = search_q.strip().lower()
        filtered = [v for v in filtered if q in v["title"].lower()]
    if min_minutes > 0:
        filtered = [v for v in filtered if duration_to_minutes(v["duration"]) >= min_minutes]

    # Apply sort
    if sort_order == "Oldest first":
        filtered = list(reversed(filtered))
    elif sort_order == "Longest first":
        filtered = sorted(filtered, key=lambda v: duration_to_minutes(v["duration"]), reverse=True)
    elif sort_order == "Shortest first":
        filtered = sorted(filtered, key=lambda v: duration_to_minutes(v["duration"]))

    st.markdown(f"<small style='color:#8fbcd4'>Showing {len(filtered)} of {total} videos</small>", unsafe_allow_html=True)

    # ── Select / Deselect all ──
    col_sa, col_da, col_spacer = st.columns([1, 1, 4])
    with col_sa:
        if st.button("✅ Select all visible"):
            for v in filtered:
                st.session_state.selected_ids.add(v["video_id"])
            st.rerun()
    with col_da:
        if st.button("✖️ Deselect all"):
            st.session_state.selected_ids.clear()
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Video rows ──
    for v in filtered:
        vid_id = v["video_id"]
        is_selected = vid_id in st.session_state.selected_ids
        has_result = vid_id in st.session_state.results

        col_check, col_info = st.columns([0.05, 0.95])
        with col_check:
            checked = st.checkbox("", value=is_selected, key=f"chk_{vid_id}")
            if checked and vid_id not in st.session_state.selected_ids:
                st.session_state.selected_ids.add(vid_id)
            elif not checked and vid_id in st.session_state.selected_ids:
                st.session_state.selected_ids.discard(vid_id)

        with col_info:
            result_badge = ""
            if vid_id in st.session_state.results:
                r = st.session_state.results[vid_id]
                if "error" in r:
                    result_badge = "❌ No transcript"
                else:
                    result_badge = "✅ Prompt ready"

            st.markdown(
                f"**{v['title']}**  "
                f"<span style='color:#8fbcd4;font-size:.78rem'>⏱ {v['duration']} &nbsp;|&nbsp; 📅 {v['date']} &nbsp;|&nbsp; 👁 {v['views']}</span>"
                f"{'&nbsp;&nbsp;<span style=\"font-size:.72rem;color:#c9a84c\">' + result_badge + '</span>' if result_badge else ''}",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 3 — ANALYZE SELECTED
    # ─────────────────────────────────────────────────────────────────────────
    selected_videos = [v for v in videos if v["video_id"] in st.session_state.selected_ids]

    if selected_videos:
        st.markdown('<div class="card"><div class="card-title">⚙️ Phase 3 — Generate Analysis Prompts</div>', unsafe_allow_html=True)

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            chunk_size = st.select_slider(
                "Segment size (chars/chunk)",
                options=[400, 600, 800, 1000, 1200],
                value=800,
            )
        with col_opt2:
            researcher_notes = st.text_area(
                "Research notes to embed in every prompt (optional)",
                placeholder="e.g., 'Analyzing SV Delos channel for post-work identity themes. Brady and Sailing La Vagabonde crew context.'",
                height=80,
            )

        analyze_btn = st.button(
            f"⚓  Generate Prompts for {len(selected_videos)} Selected Video{'s' if len(selected_videos) != 1 else ''}",
            type="primary",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if analyze_btn:
            st.markdown('<div class="card"><div class="card-title">🌊 Processing — Please Wait</div>', unsafe_allow_html=True)
            progress_bar = st.progress(0)
            status_area = st.empty()
            log_lines = []

            for i, v in enumerate(selected_videos):
                vid_id = v["video_id"]
                status_area.markdown(
                    f"<div class='progress-item'><span class='pi-icon'>🌊</span>"
                    f"Fetching transcript for: <strong>{v['title'][:60]}...</strong></div>",
                    unsafe_allow_html=True,
                )
                try:
                    raw = fetch_transcript(vid_id)
                    cleaned = clean_transcript(raw)
                    if len(cleaned.split()) < 50:
                        raise ValueError("Transcript too short — likely music/no speech")
                    chunks = chunk_text(cleaned, chunk_size=chunk_size)
                    prompt = build_prompt(v, cleaned, chunks, researcher_notes, chunk_size)
                    st.session_state.results[vid_id] = {"prompt": prompt, "title": v["title"]}
                    log_lines.append(f"✅  {v['title'][:55]}")
                except (TranscriptsDisabled, NoTranscriptFound):
                    st.session_state.results[vid_id] = {"error": "No transcript available", "title": v["title"]}
                    log_lines.append(f"❌  {v['title'][:55]} — no captions")
                except VideoUnavailable:
                    st.session_state.results[vid_id] = {"error": "Video unavailable", "title": v["title"]}
                    log_lines.append(f"❌  {v['title'][:55]} — unavailable")
                except Exception as e:
                    st.session_state.results[vid_id] = {"error": str(e), "title": v["title"]}
                    log_lines.append(f"⚠️  {v['title'][:55]} — {str(e)[:40]}")

                progress_bar.progress((i + 1) / len(selected_videos))
                time.sleep(0.3)   # be polite to YouTube's servers

            status_area.markdown(
                "<div class='progress-item'><span class='pi-icon'>✅</span><strong>All done!</strong></div>",
                unsafe_allow_html=True,
            )
            for line in log_lines:
                st.markdown(
                    f"<div style='font-size:.8rem;color:#8fbcd4;padding:.1rem 0'>{line}</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 4 — RESULTS & DOWNLOAD
    # ─────────────────────────────────────────────────────────────────────────
    successful = {vid_id: r for vid_id, r in st.session_state.results.items() if "prompt" in r}
    failed = {vid_id: r for vid_id, r in st.session_state.results.items() if "error" in r}

    if successful:
        st.markdown('<div class="card"><div class="card-title">📦 Phase 4 — Download Your Prompts</div>', unsafe_allow_html=True)

        ready_count = len(successful)
        st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{ready_count}</span><span class="stat-lbl">Prompts Ready</span></div>
  <div class="stat-pill"><span class="stat-val">{len(failed)}</span><span class="stat-lbl">No Transcript</span></div>
</div>
""", unsafe_allow_html=True)

        # ── Build ZIP ──
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for vid_id, r in successful.items():
                safe_title = re.sub(r"[^\w\s\-]", "", r["title"])[:50].strip().replace(" ", "_")
                filename = f"MAIC_{safe_title}_{vid_id}.txt"
                zf.writestr(filename, r["prompt"])

            # Add a summary index file
            index_lines = ["MAIC CHANNEL ANALYSIS — BATCH SUMMARY", "=" * 60, ""]
            index_lines.append(f"Channel: {st.session_state.channel_name}")
            index_lines.append(f"Total prompts generated: {ready_count}")
            index_lines.append(f"Videos with no transcript: {len(failed)}")
            index_lines.append("")
            index_lines.append("INCLUDED VIDEOS:")
            for vid_id, r in successful.items():
                v_data = next((v for v in videos if v["video_id"] == vid_id), {})
                index_lines.append(f"  ✅  {r['title']}")
                index_lines.append(f"       https://www.youtube.com/watch?v={vid_id}")
                index_lines.append(f"       Duration: {v_data.get('duration','?')} | {v_data.get('date','?')}")
                index_lines.append("")
            if failed:
                index_lines.append("NO TRANSCRIPT AVAILABLE:")
                for vid_id, r in failed.items():
                    index_lines.append(f"  ❌  {r['title']} — {r['error']}")
            zf.writestr("_INDEX.txt", "\n".join(index_lines))

        zip_buffer.seek(0)
        channel_slug = re.sub(r"[^\w\-]", "_", st.session_state.channel_name)[:30]
        zip_filename = f"MAIC_{channel_slug}_{ready_count}prompts.zip"

        st.download_button(
            label=f"⬇️  Download All {ready_count} Prompts as ZIP",
            data=zip_buffer,
            file_name=zip_filename,
            mime="application/zip",
            use_container_width=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Individual prompt preview ──
        st.markdown("**Preview individual prompts:**")
        for vid_id, r in successful.items():
            with st.expander(f"📄 {r['title'][:70]}"):
                st.text_area(
                    "Prompt",
                    value=r["prompt"],
                    height=280,
                    label_visibility="collapsed",
                    key=f"ta_{vid_id}",
                )
                safe_title = re.sub(r"[^\w\s\-]", "", r["title"])[:50].strip().replace(" ", "_")
                st.download_button(
                    label="⬇️ Download this prompt",
                    data=r["prompt"],
                    file_name=f"MAIC_{safe_title}_{vid_id}.txt",
                    mime="text/plain",
                    key=f"dl_{vid_id}",
                )

        if failed:
            st.markdown("**Videos with no available transcript:**")
            for vid_id, r in failed.items():
                st.markdown(
                    f"<div class='error-row'>❌ {r['title'][:70]} — {r['error']}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#2e6da4;font-size:.75rem;padding:1rem 0 .5rem;
            border-top:1px solid #1b3a5c;">
  🚢 MAIC Channel Analyzer · v1.0 · Built for UFT AI Development Course ·
  Occupational Science PhD Research · Zero API Cost
</div>
""", unsafe_allow_html=True)
