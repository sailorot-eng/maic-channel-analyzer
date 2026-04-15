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

st.set_page_config(
    page_title="MAIC Channel Analyzer",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
  .stButton>button{background:#c9a84c!important;border:2px solid #e8c96a!important;color:#1a0f00!important;font-family:'Cinzel',serif!important;font-weight:700!important;letter-spacing:.06em!important;font-size:.85rem!important;border-radius:6px!important;}
  .stProgress>div>div{background-color:var(--brass)!important;}
  [data-testid="stSidebar"]{background:#07111e!important;border-right:1px solid #1b3a5c;}
  [data-testid="stSidebar"] *{color:var(--chalk)!important;}
  .stat-row{display:flex;gap:.8rem;flex-wrap:wrap;margin:.5rem 0 1rem;}
  .stat-pill{background:rgba(46,109,164,.25);border:1px solid var(--steel);border-radius:8px;padding:.4rem .9rem;text-align:center;}
  .stat-val{font-family:'Cinzel',serif;font-size:1.2rem;color:var(--brass);font-weight:700;}
  .stat-lbl{font-size:.68rem;color:var(--wake);letter-spacing:.05em;text-transform:uppercase;}
  .error-row{font-size:.8rem;color:var(--coral);padding:.2rem 0;}
  hr{border-color:#2a4d6e!important;}
</style>
""", unsafe_allow_html=True)

# ── Session state init ──
for k, v in {"videos": [], "channel_name": "", "results": {}, "analysis_done": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

COMMAND_PRESENCE_TERMS = [
    "decision","authority","responsibility","situation awareness","situational awareness",
    "judgment","calm","composure","navigation","chart","bearing","helm","crew","watch",
    "weather","risk","safe","safety","protocol","rule","right of way","stand-on",
    "give-way","collision","COLREGS","VHF","mayday","pan-pan","distress","anchor",
    "dock","moor","throttle","trim","heel","capsize","rescue","PFD","life jacket",
    "command","lead","leadership","skipper","captain","mate","communication","confidence",
    "adapt","assess","plan","execute","debrief","lesson","mistake","correct","tack","jibe","reef",
]

def parse_channel_identifier(url):
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

def fetch_channel_videos(identifier, id_type, limit=300):
    gen = (scrapetube.get_channel(channel_id=identifier, limit=limit)
           if id_type == "channel_id"
           else scrapetube.get_channel(channel_username=identifier, limit=limit))
    videos = []
    for v in gen:
        vid_id = v.get("videoId", "")
        runs   = v.get("title", {}).get("runs", [])
        title  = runs[0].get("text", "") if runs else ""
        if vid_id and title:
            videos.append({
                "video_id": vid_id, "title": title,
                "duration": v.get("lengthText", {}).get("simpleText", ""),
                "views":    v.get("viewCountText", {}).get("simpleText", ""),
                "date":     v.get("publishedTimeText", {}).get("simpleText", ""),
                "url":      f"https://www.youtube.com/watch?v={vid_id}",
            })
    return videos

def fetch_transcript(video_id):
    """
    Robust fetcher — tries multiple methods to work across all
    versions of youtube-transcript-api.
    """
    # Method 1: get_transcript() class method — most stable across all versions
    try:
        return YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "en-US", "en-GB"]
        )
    except Exception:
        pass

    # Method 2: get_transcript() with no language filter (catches auto-generated)
    try:
        return YouTubeTranscriptApi.get_transcript(video_id)
    except Exception:
        pass

    # Method 3: instance list() — new API style (0.6.x+)
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
                    return fetch_fn() if fetch_fn else list(result)
                except Exception:
                    continue
    except Exception:
        pass

    # Method 4: static list_transcripts — older API style
    try:
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
    except Exception:
        pass

    raise NoTranscriptFound(video_id, ["en"], {})

def clean_transcript(raw):
    parts = []
    for entry in raw:
        text = re.sub(r"\[.*?\]", "", entry.get("text", ""))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            parts.append(text)
    return re.sub(r" {2,}", " ", " ".join(parts)).strip()

def chunk_text(text, chunk_size=800):
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

def build_prompt(video, cleaned, chunks, researcher_notes=""):
    terms = "\n".join(f"   - {t}" for t in COMMAND_PRESENCE_TERMS)
    segs  = "\n".join(f"\n--- SEGMENT {i} of {len(chunks)} ---\n{c}" for i, c in enumerate(chunks, 1))
    notes = f"\n\nRESEARCHER NOTES:\n{researcher_notes.strip()}\n" if researcher_notes.strip() else ""
    return f"""MARITIME AGENCY & IDENTITY CLASSIFIER (MAIC) - CHANNEL BATCH
Qualitative Analysis Prompt - Occupational Science Dissertation

SOURCE VIDEO : {video['url']}
TITLE        : {video['title']}
DURATION     : {video['duration']}
PUBLISHED    : {video['date']}
WORD COUNT   : {len(cleaned.split()):,} words across {len(chunks)} segments
{notes}
=============================================================================
RESEARCH CONTEXT

You are assisting a PhD candidate in Occupational Science who is also a licensed
USCG Captain and NYC public school occupational therapist. Analyze this transcript
for a dissertation on:
  1. Sailor occupational identity and meaning in a post-labor world
  2. Adaptive technologies and co-occupational partnerships in sailing
  3. Command Presence competencies for USCG OUPV (6-Pack) CTE pedagogy
  4. Photovoice methodology for adaptive sailor empowerment

=============================================================================
LENS 1 - Post-Work Occupational Identity (Wilcock: doing-being-belonging-becoming)

  a) Language used to describe why they sail?
  b) Sailing framed as WORK, LEISURE, VOCATION, or hybrid?
  c) How is time structured around sailing?
  d) Community/relational belonging provided by sailing?
  e) Evidence of occupational becoming - growth or transformation of self?
  f) How are AI/automation tools positioned?
  g) Rate confidence for post-work thesis: Low/Medium/High + explanation.

=============================================================================
LENS 2 - Occupational Justice, Ableism & Co-Occupation

  a) Mentions of disability, chronic illness, injury, or neurodivergence?
  b) Adaptive technologies described or implied?
  c) Environmental modifications to vessel or marina?
  d) Co-occupation moments - two or more people completing a task together?
  e) Expressions of occupational injustice or exclusion?
  f) Ableist language - even unintentional?
  g) Generate 3 photovoice prompts: "Photograph a moment when ___________"

=============================================================================
LENS 3 - USCG Command Presence: CTE Teaching Case Studies

  a) Identify 3-6 critical incidents of decision-making or leadership.
     For each: segment | description | USCG competency | discussion question
  b) Rule-based navigation decisions (COLREGS, VHF, anchoring, right of way)?
  c) Weather decision-making (go/no-go, reefing, seeking shelter)?
  d) Crew leadership moments (briefing, debriefing, managing fear)?
  e) Mistakes made and reflected upon - describe the learning loop.
  f) Rate utility as USCG CTE teaching resource (1-10) with rationale.

=============================================================================
LENS 4 - Ethnographic Command Presence Term Frequency

  STEP 1: Count occurrences of seed terms and semantic variants:
{terms}

  STEP 2: Ranked table (highest frequency first):
  | Rank | Term | Count | Segments | Command Presence Category |

  Categories: SITUATIONAL AWARENESS | DECISION-MAKING UNDER PRESSURE |
  CREW LEADERSHIP & COMMUNICATION | REGULATORY/USCG COMPLIANCE |
  RISK ASSESSMENT & SEAMANSHIP | EMOTIONAL REGULATION | TECHNICAL SKILL

  STEP 3: Emergent terms not in seed list with counts and rationale.
  STEP 4: 10 photovoice prompts from top 10 terms.
  STEP 5: 150-200 word curriculum synthesis.

=============================================================================
FINAL SYNTHESIS - Dissertation Memo (300-400 words)

  1. Most significant findings across all four lenses
  2. Convergent themes across multiple lenses
  3. Data that challenges or complicates the theoretical framework
  4. 2-3 member-checking interview questions for this sailor
  5. Analytical Richness Score (1-10) with rationale

=============================================================================
TRANSCRIPT DATA
{segs}
=============================================================================
END OF TRANSCRIPT. Please produce your full four-lens qualitative analysis.
=============================================================================
""".strip()

def duration_to_minutes(d):
    parts = d.strip().split(":")
    try:
        return int(parts[0]) * 60 + int(parts[1]) if len(parts) == 3 else int(parts[0]) if len(parts) == 2 else 0
    except Exception:
        return 0

# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🚢 Channel Analyzer")
    st.markdown("""
**MAIC Batch Mode**

1. Paste a channel URL
2. Browse & filter videos
3. Check the ones you want
4. Click Analyze Selected
5. Download ZIP of all prompts

---
**Tips for Large Channels**
- Set min duration to 10+ min to skip Shorts
- Sort oldest-first for longitudinal work
- Start with 5-10 videos

---
**Paste prompts into:**
- [Claude.ai](https://claude.ai)
- [ChatGPT](https://chat.openai.com)
- [Gemini](https://gemini.google.com)
""")

# ── Hero ──
st.markdown("""
<div class="maic-hero">
  <h1>🚢 MAIC Channel Analyzer</h1>
  <div class="subtitle">
    Paste any YouTube channel URL, browse all videos in a filterable table,
    select the ones relevant to your research, and generate MAIC qualitative
    analysis prompts in bulk. Download everything as a ZIP.
  </div>
  <div class="badge-row">
    <span class="badge">📺 Full Channel Scrape</span>
    <span class="badge">☑️ Batch Selection</span>
    <span class="badge">⬇️ ZIP Download</span>
    <span class="badge">💰 Zero API Cost</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Phase 1: Load channel ──
st.markdown('<div class="card"><div class="card-title">📡 Phase 1 — Enter Channel URL</div>', unsafe_allow_html=True)
col_url, col_limit = st.columns([3, 1])
with col_url:
    channel_url = st.text_input("Channel URL", placeholder="https://www.youtube.com/@svdelos", label_visibility="collapsed")
with col_limit:
    video_limit = st.number_input("Max videos", min_value=10, max_value=500, value=200, step=10)

if st.button("📺  Load Channel Videos", use_container_width=True):
    if not channel_url.strip():
        st.error("Please enter a YouTube channel URL.")
    else:
        identifier, id_type = parse_channel_identifier(channel_url.strip())
        if not identifier:
            st.error("Could not parse that URL. Try: https://www.youtube.com/@channelname")
        else:
            with st.spinner(f"Scanning channel — loading up to {video_limit} videos..."):
                try:
                    vids = fetch_channel_videos(identifier, id_type, limit=video_limit)
                    st.session_state.videos       = vids
                    st.session_state.channel_name = identifier
                    st.session_state.results      = {}
                    st.session_state.analysis_done = False
                    # clear old checkbox state
                    for v in vids:
                        key = f"chk_{v['video_id']}"
                        if key in st.session_state:
                            del st.session_state[key]
                    st.success(f"Found {len(vids)} videos from **{identifier}**")
                except Exception as e:
                    st.error(f"Could not load channel: {e}")
st.markdown("</div>", unsafe_allow_html=True)

# ── Phase 2: Browse & Select ──
if st.session_state.videos:
    videos = st.session_state.videos

    st.markdown('<div class="card"><div class="card-title">☑️ Phase 2 — Browse & Select Videos</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        search_q = st.text_input("Search titles", placeholder="storm, anchor, Pacific...")
    with col_f2:
        min_minutes = st.number_input("Min duration (min)", min_value=0, max_value=120, value=10)
    with col_f3:
        sort_order = st.selectbox("Sort by", ["Newest first", "Oldest first", "Longest first", "Shortest first"])

    filtered = [v for v in videos
                if (not search_q.strip() or search_q.strip().lower() in v["title"].lower())
                and duration_to_minutes(v["duration"]) >= min_minutes]
    if sort_order == "Oldest first":
        filtered = list(reversed(filtered))
    elif sort_order == "Longest first":
        filtered = sorted(filtered, key=lambda v: duration_to_minutes(v["duration"]), reverse=True)
    elif sort_order == "Shortest first":
        filtered = sorted(filtered, key=lambda v: duration_to_minutes(v["duration"]))

    all_selected = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]

    st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{len(videos)}</span><span class="stat-lbl">Total</span></div>
  <div class="stat-pill"><span class="stat-val">{len(filtered)}</span><span class="stat-lbl">Showing</span></div>
  <div class="stat-pill"><span class="stat-val">{len(all_selected)}</span><span class="stat-lbl">Selected</span></div>
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

    st.markdown(f"<small style='color:#8fbcd4'>Showing {len(filtered)} of {len(videos)}</small>", unsafe_allow_html=True)

    for v in filtered:
        vid_id = v["video_id"]
        result_tag = ""
        if vid_id in st.session_state.results:
            result_tag = " ✅" if "prompt" in st.session_state.results[vid_id] else " ❌"
        col_chk, col_info = st.columns([0.05, 0.95])
        with col_chk:
            st.checkbox("", key=f"chk_{vid_id}")
        with col_info:
            st.markdown(
                f"**{v['title']}{result_tag}**  "
                f"<span style='color:#8fbcd4;font-size:.78rem'>⏱ {v['duration']} | 📅 {v['date']} | 👁 {v['views']}</span>",
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Phase 3: Analyze ──
    all_selected = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]

    if all_selected:
        st.markdown('<div class="card"><div class="card-title">⚙️ Phase 3 — Generate Analysis Prompts</div>', unsafe_allow_html=True)
        col_o1, col_o2 = st.columns(2)
        with col_o1:
            chunk_size = st.select_slider("Segment size (chars)", options=[400, 600, 800, 1000, 1200], value=800)
        with col_o2:
            researcher_notes = st.text_area("Research notes (optional)", placeholder="e.g., Analyzing SV Delos for post-work identity...", height=80)

        st.info(f"**{len(all_selected)} video{'s' if len(all_selected) != 1 else ''} selected** and ready to analyze.")

        if st.button(f"⚓  Analyze {len(all_selected)} Selected Video{'s' if len(all_selected)!=1 else ''}", use_container_width=True):
            st.session_state.results       = {}
            st.session_state.analysis_done = False

            progress_bar = st.progress(0)
            log_area     = st.empty()
            log_lines    = []

            for i, v in enumerate(all_selected):
                vid_id = v["video_id"]
                log_lines.append(f"🌊 Fetching: {v['title'][:60]}...")
                log_area.markdown(
                    "<br>".join(f"<div style='font-size:.8rem;color:#8fbcd4'>{l}</div>" for l in log_lines[-8:]),
                    unsafe_allow_html=True,
                )
                try:
                    raw     = fetch_transcript(vid_id)
                    cleaned = clean_transcript(raw)
                    if len(cleaned.split()) < 50:
                        raise ValueError("Transcript too short")
                    chunks  = chunk_text(cleaned, chunk_size=chunk_size)
                    prompt  = build_prompt(v, cleaned, chunks, researcher_notes)
                    st.session_state.results[vid_id] = {"prompt": prompt, "title": v["title"]}
                    log_lines[-1] = f"✅ Done: {v['title'][:60]}"
                except (TranscriptsDisabled, NoTranscriptFound):
                    st.session_state.results[vid_id] = {"error": "No transcript available", "title": v["title"]}
                    log_lines[-1] = f"❌ No captions: {v['title'][:55]}"
                except VideoUnavailable:
                    st.session_state.results[vid_id] = {"error": "Video unavailable", "title": v["title"]}
                    log_lines[-1] = f"❌ Unavailable: {v['title'][:55]}"
                except Exception as e:
                    st.session_state.results[vid_id] = {"error": str(e)[:80], "title": v["title"]}
                    log_lines[-1] = f"⚠️ Error on {v['title'][:45]}: {str(e)[:35]}"

                progress_bar.progress((i + 1) / len(all_selected))
                log_area.markdown(
                    "<br>".join(f"<div style='font-size:.8rem;color:#8fbcd4'>{l}</div>" for l in log_lines[-8:]),
                    unsafe_allow_html=True,
                )
                time.sleep(0.4)

            st.session_state.analysis_done = True
            st.success(f"✅ Complete! {len(all_selected)} videos processed.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Phase 4: Results ──
    successful = {k: r for k, r in st.session_state.results.items() if "prompt" in r}
    failed     = {k: r for k, r in st.session_state.results.items() if "error"  in r}

    if successful:
        st.markdown('<div class="card"><div class="card-title">📦 Phase 4 — Download Your Prompts</div>', unsafe_allow_html=True)

        st.markdown(f"""
<div class="stat-row">
  <div class="stat-pill"><span class="stat-val">{len(successful)}</span><span class="stat-lbl">Prompts Ready</span></div>
  <div class="stat-pill"><span class="stat-val">{len(failed)}</span><span class="stat-lbl">No Transcript</span></div>
</div>""", unsafe_allow_html=True)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for vid_id, r in successful.items():
                safe = re.sub(r"[^\w\s\-]", "", r["title"])[:50].strip().replace(" ", "_")
                zf.writestr(f"MAIC_{safe}_{vid_id}.txt", r["prompt"])
            idx = [f"MAIC CHANNEL BATCH INDEX", "="*50, "",
                   f"Channel: {st.session_state.channel_name}",
                   f"Prompts: {len(successful)}  |  Skipped: {len(failed)}", ""]
            for vid_id, r in successful.items():
                vd = next((v for v in videos if v["video_id"] == vid_id), {})
                idx += [f"+ {r['title']}", f"  {vd.get('url','')}", ""]
            if failed:
                idx += ["NO TRANSCRIPT:"] + [f"- {r['title']} ({r['error']})" for r in failed.values()]
            zf.writestr("_INDEX.txt", "\n".join(idx))

        zip_buffer.seek(0)
        slug = re.sub(r"[^\w\-]", "_", st.session_state.channel_name)[:30]
        st.download_button(
            label=f"⬇️  Download All {len(successful)} Prompts as ZIP",
            data=zip_buffer,
            file_name=f"MAIC_{slug}_{len(successful)}prompts.zip",
            mime="application/zip",
            use_container_width=True,
        )

        st.markdown("<br>**Preview & download individual prompts:**")
        for vid_id, r in successful.items():
            with st.expander(f"📄 {r['title'][:70]}"):
                st.text_area("Prompt", value=r["prompt"], height=280,
                             label_visibility="collapsed", key=f"ta_{vid_id}")
                safe = re.sub(r"[^\w\s\-]", "", r["title"])[:50].strip().replace(" ", "_")
                st.download_button("⬇️ Download this prompt", data=r["prompt"],
                                   file_name=f"MAIC_{safe}_{vid_id}.txt",
                                   mime="text/plain", key=f"dl_{vid_id}")

        if failed:
            st.markdown("**Videos with no available transcript:**")
            for r in failed.values():
                st.markdown(f"<div class='error-row'>❌ {r['title'][:70]} — {r['error']}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;color:#2e6da4;font-size:.75rem;padding:1rem 0 .5rem;border-top:1px solid #1b3a5c;">
  🚢 MAIC Channel Analyzer v1.1 · UFT AI Development Course · Occupational Science PhD · Zero API Cost
</div>
""", unsafe_allow_html=True)
