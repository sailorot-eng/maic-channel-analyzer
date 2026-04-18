"""
MAIC Channel Analyzer v3.0 — Stable Build
Maritime Agency & Identity Classifier
PhD Dissertation Tool — Occupational Science
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

# ── Optional Gemini import ──────────────────────────────────────────────────
try:
    from google import genai as google_genai
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        import google.generativeai as google_genai
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MAIC v3.0 · Maritime Agency & Identity Classifier",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Source+Sans+3:wght@300;400;600&display=swap');
:root {
  --navy:#0d1b2a; --ocean:#1b3a5c; --steel:#2e6da4;
  --wake:#5ba4d4; --foam:#d6eaf8; --brass:#c9a84c;
  --chalk:#f0f4f8; --coral:#e05555; --green:#1d9e75;
}
html,body,[class*="css"]{font-family:'Source Sans 3',sans-serif;background:#0d1b2a!important;color:#f0f4f8;}
.block-container{padding:1.5rem 2rem 3rem;max-width:1200px;}
.hero{background:linear-gradient(135deg,#0d1b2a,#1b3a5c 60%,#0d2d4a);border:1px solid #2e6da4;border-radius:10px;padding:1.4rem 2rem;margin-bottom:1.2rem;}
.hero h1{font-family:'Cinzel',serif;font-size:1.5rem;color:#c9a84c;margin:0 0 .25rem;}
.hero p{font-size:.85rem;color:#d6eaf8;opacity:.85;margin:0;}
.card{background:#1b3a5c;border:1px solid #2a4d6e;border-radius:10px;padding:1.2rem 1.5rem;margin-bottom:1rem;}
.card-title{font-family:'Cinzel',serif;font-size:.75rem;letter-spacing:.1em;color:#c9a84c;text-transform:uppercase;margin-bottom:.75rem;}
.stTextInput>div>div>input,.stTextArea textarea,.stNumberInput input{background:#0d1b2a!important;border:1px solid #2e6da4!important;color:#f0f4f8!important;border-radius:6px!important;}
.stButton>button{background:#c9a84c!important;border:2px solid #e8c96a!important;color:#1a0f00!important;font-family:'Cinzel',serif!important;font-weight:700!important;font-size:.83rem!important;border-radius:6px!important;}
.stButton>button:hover{background:#e0b94a!important;}
[data-testid="stSidebar"]{background:#07111e!important;border-right:1px solid #1b3a5c;}
[data-testid="stSidebar"] *{color:#f0f4f8!important;}
.stat-row{display:flex;gap:.7rem;flex-wrap:wrap;margin:.4rem 0 .9rem;}
.stat-pill{background:rgba(46,109,164,.25);border:1px solid #2e6da4;border-radius:8px;padding:.4rem .85rem;text-align:center;}
.stat-val{font-family:'Cinzel',serif;font-size:1.1rem;color:#c9a84c;font-weight:700;display:block;}
.stat-lbl{font-size:.66rem;color:#5ba4d4;letter-spacing:.05em;text-transform:uppercase;}
.ok{color:#5dcaa5;font-size:.82rem;}
.err{color:#e05555;font-size:.82rem;}
.stTabs [data-baseweb="tab-list"]{background:#07111e;border-radius:8px 8px 0 0;border:1px solid #2a4d6e;}
.stTabs [data-baseweb="tab"]{color:#8fbcd4!important;font-family:'Cinzel',serif!important;font-size:.72rem!important;}
.stTabs [aria-selected="true"]{color:#c9a84c!important;border-bottom:2px solid #c9a84c!important;}
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ───────────────────────────────────────────────────
DEFAULTS = {
    "videos":            [],
    "channel_name":      "",
    "channel_url":       "",
    "active_ch_name":    "",
    "transcripts":       {},
    "top_videos":        [],
    "gemini_results":    {},
    "synthesis":         "",
    "prompts":           {},
    "just_loaded_ch":    "",
    "gemini_key":        "",
    "loaded":            False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Curated channels ─────────────────────────────────────────────────────────
CURATED = {
    "🦾 Adaptive & Accessible Sailing": [
        {"name":"Impossible Dream Catamaran","url":"https://www.youtube.com/@ImpossibleDreamCatamaran",
         "desc":"World's only universally accessible 60-ft catamaran. Wheelchair users at the helm. Primary dissertation data source.","tags":["adaptive","wheelchair","D1","A5"]},
        {"name":"Blind Sailing International","url":"https://www.youtube.com/@blindsailinginternational",
         "desc":"Visually impaired sailors racing and cruising. Sensory adaptation, tactile navigation.","tags":["adaptive","blind","D1","A4"]},
        {"name":"Shake-A-Leg Miami","url":"https://www.youtube.com/@ShakeALegMiami",
         "desc":"Community adaptive sailing & aquatics. OT connections, occupational justice.","tags":["adaptive","OT","D3"]},
    ],
    "⚓ Experienced Sailors (Baseline)": [
        {"name":"SV Delos","url":"https://www.youtube.com/@svdelos",
         "desc":"14+ years bluewater cruising. Post-work identity, passage planning, Command Presence in real conditions.","tags":["baseline","offshore","C1","B4","E1"]},
        {"name":"Sailing La Vagabonde","url":"https://www.youtube.com/@SailingLaVagabonde",
         "desc":"Family liveaboard sailing. Co-occupation, meaning-making.","tags":["baseline","family","A5","C2"]},
        {"name":"Far Reach Sailing","url":"https://www.youtube.com/@FarReachSailing",
         "desc":"Offshore passages with explicit seamanship narration. COLREGS, weather, watch-keeping.","tags":["baseline","seamanship","B3","B4"]},
    ],
    "🎓 USCG / CTE / Instruction": [
        {"name":"NauticEd Sailing","url":"https://www.youtube.com/@NauticEd",
         "desc":"Structured sailing instruction. COLREGS, anchoring, docking, rules of the road.","tags":["CTE","USCG","B3"]},
        {"name":"Sailing World","url":"https://www.youtube.com/@SailingWorld",
         "desc":"Racing and cruising technique. Tactical decision-making, crew communication.","tags":["CTE","racing","B2"]},
    ],
    "🌊 Heavy Weather / Decision-Making": [
        {"name":"Sailing Nahoa","url":"https://www.youtube.com/@SailingNahoa",
         "desc":"Pacific cruising with detailed passage narration. Weather decisions and risk assessment.","tags":["heavy weather","B4","A2"]},
        {"name":"Gone with the Wynns","url":"https://www.youtube.com/@GoneWithTheWynns",
         "desc":"Catamaran liveaboard. Meaning-making and identity narratives.","tags":["baseline","catamaran","C2"]},
    ],
}

CP_TERMS = [
    "decision","authority","responsibility","judgment","calm","composure",
    "navigation","bearing","helm","crew","watch","weather","risk","safety",
    "protocol","right of way","collision","mayday","distress","anchor",
    "command","leadership","skipper","captain","communication","confidence",
    "adapt","assess","plan","execute","tack","jibe","reef","passage",
    "offshore","chart","waypoint","squall","gust","swell","current","knots",
]

HIGH_TITLE_KW = [
    "passage","offshore","storm","decision","rough","crossing","emergency",
    "weather","command","heavy","adaptive","disability","wheelchair",
    "accessible","blind","rescue","leadership","crew","seamanship","night","helm",
]

STOP = set("""a about above after again all also am an and any are as at be
because been before being below between both but by can did do does doing don't
down during each few for from further get got had has have having he her here
hers him his how i if in into is it its itself just let me more most my no nor
not now of off on once only or other our out over own same she so some such
than that the their them then there these they this those through to too under
until up very was we were what when where which while who will with would you
your yeah okay actually really like just kind sort thing things way one two
three four five six seven eight nine ten yeah gonna pretty good nice""".split())


# ── Utility functions ─────────────────────────────────────────────────────────

def parse_channel(url: str):
    url = url.strip().rstrip("/")
    for pat, kind in [
        (r"youtube\.com/@([\w\-]+)", "username"),
        (r"youtube\.com/channel/(UC[\w\-]+)", "id"),
        (r"youtube\.com/(?:c|user)/([\w\-]+)", "username"),
    ]:
        m = re.search(pat, url)
        if m:
            return m.group(1), kind
    m = re.match(r"@?([\w\-]+)$", url.split("/")[-1])
    return (m.group(1), "username") if m else (None, None)


def load_videos(identifier, kind, limit):
    gen = (scrapetube.get_channel(channel_id=identifier, limit=limit)
           if kind == "id"
           else scrapetube.get_channel(channel_username=identifier, limit=limit))
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


def normalize(entries):
    result = []
    for e in entries:
        if isinstance(e, dict):
            result.append(e)
        else:
            try:
                result.append({
                    "text":     getattr(e, "text", str(e)),
                    "start":    float(getattr(e, "start", 0.0)),
                    "duration": float(getattr(e, "duration", 0.0)),
                })
            except Exception:
                result.append({"text": str(e), "start": 0.0, "duration": 0.0})
    return result


def fetch_transcript(video_id):
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
                    r = attempt(tl)
                    fn = getattr(r, "fetch", None)
                    return normalize(fn() if fn else list(r))
                except Exception:
                    pass
    except Exception:
        pass
    raise NoTranscriptFound(video_id, ["en"], {})


def to_ts(s):
    s = int(s); h, m, sec = s//3600, (s%3600)//60, s%60
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def build_segments(raw):
    segs, buf, t0 = [], [], 0.0
    for e in raw:
        txt = re.sub(r"\[.*?\]", "", e.get("text",""))
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt:
            continue
        if not buf:
            t0 = e.get("start", 0.0)
        buf.append(txt)
        joined = " ".join(buf)
        if len(buf) >= 3 or (joined and joined[-1] in ".!?"):
            segs.append({"text": joined, "start": t0, "timestamp": to_ts(t0)})
            buf, t0 = [], 0.0
    if buf:
        segs.append({"text": " ".join(buf), "start": t0, "timestamp": to_ts(t0)})
    return segs


def dur_mins(d):
    parts = d.strip().split(":")
    try:
        if len(parts) == 3: return int(parts[0])*60+int(parts[1])
        if len(parts) == 2: return int(parts[0])
    except Exception:
        pass
    return 0


def score_video(video, transcripts):
    vid_id = video["video_id"]
    bd = {}
    mins = dur_mins(video.get("duration",""))
    bd["duration"] = min(mins, 60)//3
    kw = 0
    if vid_id in transcripts:
        full = " ".join(s["text"].lower() for s in transcripts[vid_id]["segments"])
        kw = min(sum(1 for t in CP_TERMS if t in full)*2, 40)
    bd["keyword"] = kw
    tl = sum(5 for k in HIGH_TITLE_KW if k in video.get("title","").lower())
    bd["title"] = min(tl, 25)
    try:
        v = int(re.sub(r"[^\d]","",video.get("views","0")))
        bd["views"] = 15 if v>500000 else 10 if v>100000 else 7 if v>50000 else 4 if v>10000 else 1
    except Exception:
        bd["views"] = 0
    bd["total"] = sum(bd.values())
    return bd


def search_corpus(kw, transcripts):
    kw = kw.strip().lower()
    if not kw: return []
    counts = {vid: sum(1 for s in d["segments"] if kw in s["text"].lower())
              for vid, d in transcripts.items()}
    results = []
    for vid_id, data in transcripts.items():
        for seg in data["segments"]:
            if kw in seg["text"].lower():
                results.append({
                    "video_id": vid_id,
                    "title":    data["title"],
                    "url":      data["url"],
                    "timestamp": seg["timestamp"],
                    "start":    seg["start"],
                    "excerpt":  re.sub(re.escape(kw), f"**{kw.upper()}**", seg["text"], flags=re.IGNORECASE),
                    "count":    counts[vid_id],
                })
    results.sort(key=lambda r: (-r["count"], r["start"]))
    return results


def auto_discover(transcripts, top_n=50):
    wc = collections.Counter()
    for data in transcripts.values():
        for seg in data["segments"]:
            for w in re.findall(r"[a-zA-Z']+", seg["text"].lower()):
                w = w.strip("'")
                if len(w) >= 4 and w not in STOP:
                    wc[w] += 1
    return wc.most_common(top_n)


def gemini_analyze(video_url, title, api_key, notes=""):
    prompt = f"""You are a qualitative research assistant for a PhD dissertation in Occupational Science.
The researcher is a USCG Captain and occupational therapist studying sailor AGENCY and COMMAND PRESENCE.

Watch the full YouTube video and produce ALL six sections:

SECTION 1 — TIMESTAMPED CODING TABLE (minimum 20 rows)
| Timestamp | Code | Channel (V/VI/P) | What You See/Hear | Analytical Note |
Codes: AGENCY+ AGENCY- CP+ CP-  |  V=Verbal VI=Visual P=Paralinguistic

SECTION 2 — FREQUENCY SUMMARY
| Code | Count | % | Peak timestamp |
Agency Effectiveness Ratio: ___% | Command Presence Ratio: ___%

SECTION 3 — TOP 5 CTE TEACHING MOMENTS
Timestamp | What is happening | Why it matters for USCG students | Discussion question | Photovoice prompt

SECTION 4 — NEGATIVE CASES
3-5 moments of AGENCY- or CP-. What should have happened instead?

SECTION 5 — WHAT THE TRANSCRIPT MISSES
3-5 moments where VIDEO/PARALINGUISTIC data is richer than text alone.
Timestamp | Words spoken | What video shows | Why this matters methodologically

SECTION 6 — DISSERTATION MEMO (250-350 words)
Overall assessment | Most significant finding | Verbal vs nonverbal relationship |
Connection to post-work sailing identity | Command Presence Composite Score (0-100)

VIDEO URL: {video_url}
TITLE: {title}
RESEARCHER NOTES: {notes or 'No additional notes.'}

Watch the full video. Produce all six sections."""

    if not GEMINI_AVAILABLE:
        raise ImportError("google-genai not installed")

    try:
        # New google.genai SDK (v1.0+)
        client = google_genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=f"Please watch this YouTube video: {video_url}\n\n{prompt}",
        )
        return response.text
    except AttributeError:
        pass

    try:
        # Fallback: older google.generativeai style
        google_genai.configure(api_key=api_key)
        model = google_genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(
            f"Please watch this YouTube video: {video_url}\n\n{prompt}",
            generation_config={"max_output_tokens": 8192, "temperature": 0.3},
        )
        return response.text
    except Exception as e:
        raise Exception(f"Gemini error: {str(e)[:300]}")


def maic_prompt(video, segments, notes=""):
    terms = "\n".join(f"   - {t}" for t in CP_TERMS)
    segs  = "\n".join(f"\n--- {i+1} | {s['timestamp']} ---\n{s['text']}"
                      for i, s in enumerate(segments))
    wc = sum(len(s["text"].split()) for s in segments)
    return f"""MAIC v3.0 — 4-Lens Qualitative Analysis Prompt
SOURCE : {video['url']}
TITLE  : {video['title']}
WORDS  : {wc:,} | SEGMENTS: {len(segments)}
{f'NOTES: {notes}' if notes else ''}

LENS 1 — Post-Work Occupational Identity (Wilcock)
a) Why does this sailor sail? b) Work/leisure/vocation framing?
c) Temporal structure? d) Belonging/community? e) Becoming/growth?
f) AI/automation relationship? g) Post-work thesis confidence: Low/Medium/High

LENS 2 — Occupational Justice & Adaptive Sailing
a) Disability/chronic illness mentioned? b) Adaptive technologies?
c) Environmental modifications? d) Co-occupation moments?
e) Occupational injustice or exclusion? f) Ableist language?
g) 3 photovoice prompts: "Photograph a moment when ___"

LENS 3 — USCG Command Presence: CTE Case Studies
a) 3-6 critical incidents with USCG competency mapping
b) Navigation rule decisions? c) Weather decision-making?
d) Crew leadership? e) Learning from mistakes?
f) CTE utility rating 1-10

LENS 4 — Command Presence Term Frequency
Count each: {terms}
Output: | Rank | Term | Count | Timestamp | Category |
Then: emergent terms, 10 photovoice prompts, 150-word curriculum synthesis.

FINAL SYNTHESIS (300 words):
Key findings | Convergent themes | Framework challenges |
Member-checking questions | Analytical Richness Score 1-10

TRANSCRIPT:
{segs}""".strip()


# ── Load Gemini key from Streamlit secrets if available ──────────────────────
if not st.session_state.gemini_key:
    try:
        st.session_state.gemini_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚓ MAIC v3.0")
    st.markdown("**Research Pipeline:**")
    steps = [
        ("1. Find Channels",     st.session_state.channel_url != ""),
        ("2. Load & Fetch",      st.session_state.loaded),
        ("3. Search & Discover", len(st.session_state.transcripts) > 0),
        ("4. Select for Gemini", len(st.session_state.top_videos) > 0),
        ("5. Gemini Analysis",   len(st.session_state.gemini_results) > 0),
        ("6. Synthesis",         st.session_state.synthesis != ""),
        ("7. MAIC Prompts",      len(st.session_state.prompts) > 0),
    ]
    for label, done in steps:
        icon = "✅" if done else "○"
        color = "#5dcaa5" if done else "#8fbcd4"
        st.markdown(f"<div style='font-size:.82rem;color:{color};padding:.1rem 0'>{icon} {label}</div>",
                    unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**🔑 Gemini API Key**")
    key_input = st.text_input(
        "Key", value=st.session_state.gemini_key,
        type="password", placeholder="AIza...",
        label_visibility="collapsed",
        help="Free key from aistudio.google.com — stored permanently in Streamlit Secrets",
    )
    if key_input != st.session_state.gemini_key:
        st.session_state.gemini_key = key_input

    if st.session_state.gemini_key:
        st.markdown("<div class='ok'>✅ Gemini API key set</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='err'>⚠️ No key — Gemini disabled.<br>"
            "<a href='https://aistudio.google.com' target='_blank' style='color:#5ba4d4'>Get free key →</a><br>"
            "<small style='color:#8fbcd4'>To save permanently: App Settings → Secrets → GEMINI_API_KEY</small></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    if st.session_state.transcripts:
        n  = len(st.session_state.transcripts)
        wc = sum(sum(len(s["text"].split()) for s in d["segments"])
                 for d in st.session_state.transcripts.values())
        st.markdown(
            f"<div style='font-size:.78rem;color:#8fbcd4'>"
            f"<strong style='color:#c9a84c'>Corpus:</strong><br>"
            f"{n} transcripts · {wc:,} words<br>"
            f"Channel: {st.session_state.channel_name}</div>",
            unsafe_allow_html=True,
        )

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
<h1>⚓ MAIC v3.0 · Maritime Agency & Identity Classifier</h1>
<p>Full research pipeline: discover channels → load & analyze corpus → auto-score videos →
Gemini multimodal video coding → synthesize findings. Minimal copy-paste.</p>
</div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5,t6,t7 = st.tabs([
    "🔍 Find Channels","📡 Load Channel","🔎 Search & Discover",
    "⭐ Select for Gemini","🎬 Gemini Analysis","📊 Synthesis","📄 MAIC Prompts",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — FIND CHANNELS
# ════════════════════════════════════════════════════════════════════════════════
with t1:
    # ── Confirmation banner after Load → is clicked ──────────────────────────
    if st.session_state.get("just_loaded_ch"):
        st.markdown(
            f"<div style='background:rgba(29,158,117,.2);border:2px solid #5dcaa5;"
            f"border-radius:8px;padding:.8rem 1.2rem;margin-bottom:1rem;font-size:.95rem;color:#5dcaa5'>"
            f"✅ <strong>{st.session_state.just_loaded_ch}</strong> is ready! "
            f"Now click the <strong>📡 Load Channel</strong> tab above to continue.</div>",
            unsafe_allow_html=True,
        )
        st.session_state.just_loaded_ch = ""

    # ── Custom URL entry ──────────────────────────────────────────────────────
    st.markdown('<div class="card"><div class="card-title">🔗 Enter Any YouTube Channel URL</div>',
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.82rem;color:#8fbcd4;margin-bottom:.6rem'>"
        "Paste any YouTube channel URL here, or pick one from the curated list below.</div>",
        unsafe_allow_html=True,
    )
    c_custom_url, c_custom_btn = st.columns([4,1])
    with c_custom_url:
        custom_url = st.text_input(
            "Custom URL",
            value="",
            placeholder="https://www.youtube.com/@ImpossibleDreamCatamaran",
            label_visibility="collapsed",
        )
    with c_custom_btn:
        if st.button("Use This URL", use_container_width=True):
            if custom_url.strip():
                st.session_state.channel_url    = custom_url.strip()
                st.session_state.active_ch_name = custom_url.strip().split("@")[-1].split("/")[0]
                st.session_state.videos          = []
                st.session_state.transcripts     = {}
                st.session_state.top_videos      = []
                st.session_state.gemini_results  = {}
                st.session_state.synthesis       = ""
                st.session_state.loaded          = False
                st.session_state.prompts         = {}
                st.session_state.just_loaded_ch  = st.session_state.active_ch_name
                st.rerun()
            else:
                st.warning("Please paste a URL first.")
    if st.session_state.channel_url:
        st.markdown(
            f"<div style='font-size:.8rem;color:#5dcaa5;margin-top:.3rem'>"
            f"Current: <strong>{st.session_state.channel_url}</strong></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">📚 Curated Research Channels — by Population Group</div>',
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.82rem;color:#8fbcd4;margin-bottom:.8rem'>"
        "Pre-vetted channels for your three-group purposive sample. "
        "Click <strong>Load →</strong> — a green banner will confirm the channel is ready, "
        "then click the <strong>📡 Load Channel</strong> tab."
        "</div>", unsafe_allow_html=True,
    )

    for group, channels in CURATED.items():
        st.markdown(f"**{group}**")
        for ch in channels:
            c_info, c_tags, c_btn = st.columns([3, 2, 1])
            with c_info:
                st.markdown(
                    f"<div style='font-weight:600;color:#d6eaf8;font-size:.88rem'>{ch['name']}</div>"
                    f"<div style='font-size:.76rem;color:#8fbcd4'>{ch['desc'][:100]}...</div>",
                    unsafe_allow_html=True,
                )
            with c_tags:
                badges = " ".join(
                    f"<span style='background:rgba(201,168,76,.15);border:1px solid rgba(201,168,76,.3);"
                    f"border-radius:10px;padding:.1rem .4rem;font-size:.68rem;color:#c9a84c'>{t}</span>"
                    for t in ch["tags"][:4]
                )
                st.markdown(f"<div style='padding-top:.5rem'>{badges}</div>", unsafe_allow_html=True)
            with c_btn:
                safe = re.sub(r"[^\w]","_",ch["name"])
                if st.button("Load →", key=f"cur_{safe}"):
                    st.session_state.channel_url    = ch["url"]
                    st.session_state.active_ch_name = ch["name"]
                    st.session_state.videos          = []
                    st.session_state.transcripts     = {}
                    st.session_state.top_videos      = []
                    st.session_state.gemini_results  = {}
                    st.session_state.synthesis       = ""
                    st.session_state.loaded          = False
                    st.session_state.prompts         = {}
                    st.session_state.just_loaded_ch  = ch["name"]
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — LOAD CHANNEL
# ════════════════════════════════════════════════════════════════════════════════
with t2:
    # Green banner when channel was selected from Tab 1
    if st.session_state.channel_url and st.session_state.active_ch_name:
        st.markdown(
            f"<div style='background:rgba(29,158,117,.15);border:1px solid #5dcaa5;border-radius:8px;"
            f"padding:.6rem 1rem;margin-bottom:.8rem;font-size:.85rem;color:#5dcaa5'>"
            f"✅ <strong>{st.session_state.active_ch_name}</strong> is loaded — URL pre-filled below. "
            f"Click <strong>Load Channel Videos</strong> to continue.</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="card"><div class="card-title">📡 Load Channel & Fetch Transcripts</div>',
                unsafe_allow_html=True)

    c_url, c_lim = st.columns([3,1])
    with c_url:
        url_val = st.text_input(
            "Channel URL",
            value=st.session_state.channel_url,
            placeholder="https://www.youtube.com/@ImpossibleDreamCatamaran",
            label_visibility="collapsed",
        )
        if url_val != st.session_state.channel_url:
            st.session_state.channel_url    = url_val
            st.session_state.active_ch_name = ""
    with c_lim:
        vlimit = st.number_input("Max videos", min_value=3, max_value=500, value=200, step=10)

    test_mode = st.checkbox("🧪 Test mode — 3 videos only (recommended for first run)", value=True)

    if st.button("📺  Load Channel Videos", use_container_width=True):
        url_use = st.session_state.channel_url.strip()
        if not url_use:
            st.error("Please enter a channel URL or pick one from the Find Channels tab.")
        else:
            ident, kind = parse_channel(url_use)
            if not ident:
                st.error("Could not parse that URL. Try: https://www.youtube.com/@channelname")
            else:
                limit = 3 if test_mode else vlimit
                with st.spinner(f"Loading {ident} — up to {limit} videos..."):
                    try:
                        vids = load_videos(ident, kind, limit)
                        st.session_state.videos       = vids
                        st.session_state.channel_name = ident
                        st.session_state.transcripts  = {}
                        st.session_state.loaded       = False
                        st.session_state.top_videos   = []
                        st.session_state.gemini_results = {}
                        st.session_state.synthesis    = ""
                        st.session_state.prompts      = {}
                        st.success(f"✅ Found {len(vids)} videos from **{ident}**")
                    except Exception as ex:
                        st.error(f"Could not load channel: {ex}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Video list ──────────────────────────────────────────────────────────
    if st.session_state.videos:
        videos = st.session_state.videos

        st.markdown('<div class="card"><div class="card-title">☑️ Select Videos & Fetch Transcripts</div>',
                    unsafe_allow_html=True)

        f1, f2, f3 = st.columns([2,1,1])
        with f1: filt = st.text_input("Filter by title", placeholder="Sailing, storm, accessible...")
        with f2: min_d = st.number_input("Min duration (min)", 0, 120, 0)
        with f3: srt  = st.selectbox("Sort", ["Newest first","Oldest first","Longest first"])

        filtered = [v for v in videos
                    if (not filt.strip() or filt.strip().lower() in v["title"].lower())
                    and dur_mins(v["duration"]) >= min_d]
        if srt == "Oldest first":    filtered = list(reversed(filtered))
        elif srt == "Longest first": filtered = sorted(filtered, key=lambda v: dur_mins(v["duration"]), reverse=True)

        sel = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]

        st.markdown(f"""<div class="stat-row">
<div class="stat-pill"><span class="stat-val">{len(videos)}</span><span class="stat-lbl">Loaded</span></div>
<div class="stat-pill"><span class="stat-val">{len(filtered)}</span><span class="stat-lbl">Showing</span></div>
<div class="stat-pill"><span class="stat-val">{len(sel)}</span><span class="stat-lbl">Selected</span></div>
<div class="stat-pill"><span class="stat-val">{len(st.session_state.transcripts)}</span><span class="stat-lbl">Stored</span></div>
</div>""", unsafe_allow_html=True)

        ca, cb, _ = st.columns([1,1,4])
        with ca:
            if st.button("✅ Select all visible"):
                for v in filtered: st.session_state[f"chk_{v['video_id']}"] = True
                st.rerun()
        with cb:
            if st.button("✖ Deselect all"):
                for v in videos: st.session_state[f"chk_{v['video_id']}"] = False
                st.rerun()

        for v in filtered:
            vid_id = v["video_id"]
            stored = " ✅" if vid_id in st.session_state.transcripts else ""
            cc, ci = st.columns([0.05, 0.95])
            with cc:
                st.checkbox("Select", key=f"chk_{vid_id}", label_visibility="collapsed")
            with ci:
                st.markdown(
                    f"**{v['title']}{stored}**  "
                    f"<span style='color:#8fbcd4;font-size:.76rem'>⏱ {v['duration']} | 📅 {v['date']} | 👁 {v['views']}</span>",
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

        sel = [v for v in videos if st.session_state.get(f"chk_{v['video_id']}", False)]
        if sel:
            st.markdown('<div class="card"><div class="card-title">⬇️ Step 3 — Fetch & Store Transcripts</div>',
                        unsafe_allow_html=True)
            st.info(f"**{len(sel)} videos selected.** Transcripts stored with timestamps for keyword search and Gemini scoring.")

            if st.button(f"⬇️  Fetch Transcripts for {len(sel)} Video{'s' if len(sel)!=1 else ''}", use_container_width=True):
                prog = st.progress(0)
                log  = st.empty()
                lines = []

                for i, v in enumerate(sel):
                    vid_id = v["video_id"]
                    lines.append(f"🌊 {v['title'][:55]}...")
                    log.markdown("<br>".join(
                        f"<div style='font-size:.78rem;color:#8fbcd4'>{l}</div>" for l in lines[-6:]
                    ), unsafe_allow_html=True)
                    try:
                        raw  = fetch_transcript(vid_id)
                        segs = build_segments(raw)
                        if len(segs) < 3:
                            raise ValueError("Too few segments")
                        st.session_state.transcripts[vid_id] = {
                            "title":    v["title"],
                            "url":      v["url"],
                            "duration": v["duration"],
                            "segments": segs,
                        }
                        wc = sum(len(s["text"].split()) for s in segs)
                        lines[-1] = f"✅ {v['title'][:50]} ({wc:,} words, {len(segs)} segments)"
                    except (TranscriptsDisabled, NoTranscriptFound):
                        lines[-1] = f"❌ No captions: {v['title'][:50]}"
                    except Exception as ex:
                        lines[-1] = f"⚠️ {v['title'][:45]}: {str(ex)[:40]}"
                    prog.progress((i+1)/len(sel))
                    log.markdown("<br>".join(
                        f"<div style='font-size:.78rem;color:#8fbcd4'>{l}</div>" for l in lines[-6:]
                    ), unsafe_allow_html=True)
                    time.sleep(0.3)

                st.session_state.loaded = True
                n = len(st.session_state.transcripts)
                st.success(f"✅ {n} transcript{'s' if n!=1 else ''} stored and ready to search. Go to Search & Discover →")

            st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — SEARCH & DISCOVER
# ════════════════════════════════════════════════════════════════════════════════
with t3:
    if not st.session_state.transcripts:
        st.info("⚓ Fetch transcripts first in the Load Channel tab.")
    else:
        tr = st.session_state.transcripts
        n_t  = len(tr)
        tot_w = sum(sum(len(s["text"].split()) for s in d["segments"]) for d in tr.values())
        tot_s = sum(len(d["segments"]) for d in tr.values())

        st.markdown(f"""<div class="stat-row">
<div class="stat-pill"><span class="stat-val">{n_t}</span><span class="stat-lbl">Transcripts</span></div>
<div class="stat-pill"><span class="stat-val">{tot_w:,}</span><span class="stat-lbl">Total Words</span></div>
<div class="stat-pill"><span class="stat-val">{tot_s:,}</span><span class="stat-lbl">Segments</span></div>
</div>""", unsafe_allow_html=True)

        s_tab, d_tab = st.tabs(["🔍 Keyword Search","🧠 Auto-Discover Themes"])

        with s_tab:
            st.markdown('<div class="card"><div class="card-title">🔍 Search Across All Transcripts</div>',
                        unsafe_allow_html=True)
            ck, cb2 = st.columns([4,1])
            with ck: kw = st.text_input("Keyword", placeholder="confidence, command, decision, helm...", label_visibility="collapsed")
            with cb2: do_s = st.button("🔍 Search", use_container_width=True)

            st.markdown("**Quick search — Agency & Command Presence terms:**")
            quick = ["confidence","command","decision","risk","calm","crew",
                     "leadership","weather","safety","anchor","helm","navigate"]
            cols = st.columns(6)
            for i, term in enumerate(quick):
                with cols[i%6]:
                    if st.button(term, key=f"q_{term}"):
                        kw = term; do_s = True

            st.markdown("</div>", unsafe_allow_html=True)

            if do_s and kw.strip():
                results = search_corpus(kw.strip(), tr)
                if not results:
                    st.warning(f"No results for **'{kw}'** across {n_t} transcripts.")
                else:
                    hits = len(results)
                    vids = len(set(r["video_id"] for r in results))
                    top  = results[0]["count"]
                    st.markdown(f"""<div class="stat-row">
<div class="stat-pill"><span class="stat-val">{hits}</span><span class="stat-lbl">Matches</span></div>
<div class="stat-pill"><span class="stat-val">{vids}</span><span class="stat-lbl">Videos</span></div>
<div class="stat-pill"><span class="stat-val">{top}</span><span class="stat-lbl">Most in One Video</span></div>
</div>""", unsafe_allow_html=True)

                    by_vid = {}
                    for r in results:
                        by_vid.setdefault(r["video_id"], []).append(r)

                    for vid_id, vr in by_vid.items():
                        with st.expander(f"📹 {vr[0]['title'][:65]}  [{vr[0]['count']} matches]",
                                         expanded=(vr[0]['count'] == top)):
                            for r in vr:
                                st.markdown(
                                    f"<div style='background:#0d1b2a;border:1px solid #2a4d6e;border-radius:5px;"
                                    f"padding:.4rem .7rem;margin-bottom:.3rem'>"
                                    f"<span style='color:#5ba4d4;font-family:monospace;font-size:.75rem'>⏱ {r['timestamp']}</span>  "
                                    f"<span style='color:#d6eaf8;font-size:.82rem'>{r['excerpt']}</span></div>",
                                    unsafe_allow_html=True,
                                )
                            st.markdown(f"<a href='{vr[0]['url']}' target='_blank' style='font-size:.75rem;color:#5ba4d4'>▶ Watch on YouTube</a>",
                                        unsafe_allow_html=True)

                    csv = "Video Title,Timestamp,Excerpt,Count\n" + "\n".join(
                        f'"{r["title"].replace(chr(34),chr(39))}","{r["timestamp"]}","{r["excerpt"].replace(chr(34),chr(39))}",{r["count"]}'
                        for r in results
                    )
                    st.download_button(f"⬇️ Download '{kw}' results as CSV", data=csv,
                                       file_name=f"MAIC_{kw.replace(' ','_')}.csv", mime="text/csv")

        with d_tab:
            st.markdown('<div class="card"><div class="card-title">🧠 Auto-Discover Themes — Inductive Analysis</div>',
                        unsafe_allow_html=True)
            st.markdown("<div style='font-size:.83rem;color:#8fbcd4;margin-bottom:.7rem'>Surfaces the most frequent meaningful words in your corpus — your inductive coding starting point.</div>",
                        unsafe_allow_html=True)
            top_n = st.slider("Terms to surface", 20, 100, 50, 10)
            if st.button("🧠  Discover Top Terms", use_container_width=True):
                discovered = auto_discover(tr, top_n)
                if discovered:
                    chips = " ".join(
                        f"<span style='display:inline-block;background:rgba(91,164,212,.12);border:1px solid #2e6da4;"
                        f"border-radius:12px;padding:.15rem .55rem;font-size:.75rem;color:#5ba4d4;margin:.15rem'>"
                        f"{w} <strong style='color:#c9a84c'>{c}</strong></span>"
                        for w, c in discovered
                    )
                    st.markdown(chips, unsafe_allow_html=True)
                    csv_d = "Term,Frequency\n" + "\n".join(f'"{w}",{c}' for w,c in discovered)
                    st.download_button("⬇️ Download as CSV", data=csv_d,
                                       file_name="MAIC_auto_discovery.csv", mime="text/csv")
            st.markdown("</div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — SELECT FOR GEMINI
# ════════════════════════════════════════════════════════════════════════════════
with t4:
    if not st.session_state.transcripts:
        st.info("⚓ Fetch transcripts first — the scoring engine needs them.")
    else:
        st.markdown('<div class="card"><div class="card-title">⭐ Smart Video Scoring — Select Top Picks for Gemini</div>',
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:.83rem;color:#8fbcd4;margin-bottom:.8rem'>"
            "MAIC scores every transcript on keyword density, duration, title relevance, and views. "
            "Top-ranked videos are your best candidates for Gemini's multimodal video analysis.</div>",
            unsafe_allow_html=True,
        )

        top_n_s = st.slider("Videos to recommend", 3, 10, 5)
        if st.button("⭐  Score & Rank All Videos", use_container_width=True):
            scored = []
            for vid_id, data in st.session_state.transcripts.items():
                v_meta = next((v for v in st.session_state.videos if v["video_id"] == vid_id), {
                    "video_id": vid_id, "title": data["title"], "url": data["url"],
                    "duration": data.get("duration",""), "views": "", "date": "",
                })
                bd = score_video(v_meta, st.session_state.transcripts)
                scored.append({**v_meta, "breakdown": bd, "total": bd["total"]})
            scored.sort(key=lambda x: -x["total"])
            st.session_state.top_videos = scored[:top_n_s]

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.top_videos:
            st.markdown(f"### 🏆 Top {len(st.session_state.top_videos)} Videos for Gemini")
            mx = max(v["total"] for v in st.session_state.top_videos) or 1

            for rank, v in enumerate(st.session_state.top_videos, 1):
                b = v["breakdown"]
                with st.expander(f"#{rank}  {v['title'][:65]}  — Score: {v['total']}", expanded=(rank<=3)):
                    cm, cs = st.columns([3,2])
                    with cm:
                        st.markdown(
                            f"<div style='font-size:.82rem;color:#d6eaf8;line-height:1.8'>"
                            f"⏱ {v.get('duration','')} &nbsp;|&nbsp; 📅 {v.get('date','')} &nbsp;|&nbsp; 👁 {v.get('views','')}<br>"
                            f"<a href='{v['url']}' target='_blank' style='color:#5ba4d4;font-size:.78rem'>▶ Watch on YouTube</a>"
                            f"</div>", unsafe_allow_html=True,
                        )
                    with cs:
                        for label, val, mx_val in [
                            ("Keyword Density", b.get("keyword",0), 40),
                            ("Title Relevance", b.get("title",0), 25),
                            ("Duration",        b.get("duration",0), 20),
                            ("Popularity",      b.get("views",0), 15),
                        ]:
                            pct = int(val/mx_val*100) if mx_val else 0
                            st.markdown(
                                f"<div style='font-size:.72rem;color:#8fbcd4'>{label}: <strong style='color:#c9a84c'>{val}</strong>/{mx_val}</div>"
                                f"<div style='background:#1b3a5c;border-radius:4px;height:6px'>"
                                f"<div style='background:#c9a84c;border-radius:4px;height:6px;width:{pct}%'></div></div>",
                                unsafe_allow_html=True,
                            )

            st.markdown("<div style='font-size:.83rem;color:#8fbcd4;margin-top:.5rem'>✅ Go to <strong>Gemini Analysis</strong> tab to run automated analysis →</div>",
                        unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — GEMINI ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════
with t5:
    st.markdown('<div class="card"><div class="card-title">🎬 Automated Gemini Video Analysis</div>',
                unsafe_allow_html=True)

    if not st.session_state.top_videos:
        st.info("⭐ Score and select top videos in the Select for Gemini tab first.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='font-size:.83rem;color:#8fbcd4;margin-bottom:.8rem'>"
            "MAIC sends each selected video to Gemini automatically, one at a time. "
            "Gemini watches the full video and returns timestamped coding across verbal, visual, and paralinguistic channels. "
            "<strong>No copy-paste required.</strong></div>",
            unsafe_allow_html=True,
        )

        if not st.session_state.gemini_key:
            st.warning("⚠️ Add your Gemini API key in the sidebar first.")

        notes = st.text_area(
            "Researcher context (added to every Gemini prompt)",
            placeholder="e.g., Focus on command presence. Note co-occupation between disabled and non-disabled crew. Researcher is a licensed USCG Captain and OT.",
            height=65,
        )

        st.markdown(f"**{len(st.session_state.top_videos)} videos queued:**")
        for v in st.session_state.top_videos:
            done = v["video_id"] in st.session_state.gemini_results
            icon = "✅" if done else "○"
            color = "#5dcaa5" if done else "#8fbcd4"
            st.markdown(f"<div style='font-size:.82rem;color:{color};padding:.15rem 0'>{icon} {v['title'][:70]}</div>",
                        unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        c_run, c_clr = st.columns([3,1])
        with c_run:
            run_btn = st.button(
                f"🎬  Analyze {len(st.session_state.top_videos)} Video{'s' if len(st.session_state.top_videos)!=1 else ''} with Gemini",
                use_container_width=True,
                disabled=not st.session_state.gemini_key,
            )
        with c_clr:
            if st.button("🗑 Clear", use_container_width=True):
                st.session_state.gemini_results = {}
                st.session_state.synthesis = ""
                st.rerun()

        if run_btn and st.session_state.gemini_key:
            prog   = st.progress(0)
            status = st.empty()
            n_vids = len(st.session_state.top_videos)

            for i, v in enumerate(st.session_state.top_videos):
                vid_id = v["video_id"]
                if vid_id in st.session_state.gemini_results:
                    prog.progress((i+1)/n_vids)
                    continue

                status.markdown(
                    f"<div style='font-size:.85rem;color:#c9a84c'>🎬 Analyzing ({i+1}/{n_vids}): <strong>{v['title'][:60]}</strong>...</div>",
                    unsafe_allow_html=True,
                )
                try:
                    analysis = gemini_analyze(v["url"], v["title"], st.session_state.gemini_key, notes)
                    st.session_state.gemini_results[vid_id] = {
                        "analysis": analysis, "title": v["title"], "url": v["url"],
                    }
                    status.markdown(f"<div style='font-size:.85rem;color:#5dcaa5'>✅ Done: {v['title'][:60]}</div>",
                                    unsafe_allow_html=True)
                except Exception as ex:
                    st.session_state.gemini_results[vid_id] = {
                        "error": str(ex)[:200], "title": v["title"], "url": v["url"],
                    }
                    status.markdown(f"<div style='font-size:.83rem;color:#e05555'>⚠️ Error: {v['title'][:50]}: {str(ex)[:80]}</div>",
                                    unsafe_allow_html=True)

                prog.progress((i+1)/n_vids)
                if i < n_vids - 1:
                    for remaining in range(32, 0, -1):
                        status.markdown(
                            f"<div style='font-size:.8rem;color:#8fbcd4'>⏳ Rate limit pause — next video in {remaining}s...</div>",
                            unsafe_allow_html=True,
                        )
                        time.sleep(1)

            status.markdown("<div style='font-size:.9rem;color:#5dcaa5;font-weight:600'>✅ All videos processed. Go to Synthesis tab →</div>",
                            unsafe_allow_html=True)
            st.rerun()

        ok = {k:r for k,r in st.session_state.gemini_results.items() if "analysis" in r}
        bad = {k:r for k,r in st.session_state.gemini_results.items() if "error" in r}

        if ok:
            st.markdown(f"### 📋 Gemini Results ({len(ok)} complete)")
            for vid_id, r in ok.items():
                with st.expander(f"🎬 {r['title'][:70]}", expanded=False):
                    st.markdown(f"<a href='{r['url']}' target='_blank' style='font-size:.75rem;color:#5ba4d4'>▶ Watch on YouTube</a>",
                                unsafe_allow_html=True)
                    st.text_area("Analysis", value=r["analysis"], height=300,
                                 label_visibility="collapsed", key=f"gem_{vid_id}")
                    safe = re.sub(r"[^\w]","_",r["title"])[:40]
                    st.download_button("⬇️ Download", data=r["analysis"],
                                       file_name=f"MAIC_Gemini_{safe}.txt", mime="text/plain",
                                       key=f"gdl_{vid_id}")
        if bad:
            st.markdown("**Could not analyze:**")
            for r in bad.values():
                st.markdown(f"<div class='err'>❌ {r['title'][:65]} — {r.get('error','')[:100]}</div>",
                            unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# TAB 6 — SYNTHESIS
# ════════════════════════════════════════════════════════════════════════════════
with t6:
    ok_gem = {k:r for k,r in st.session_state.gemini_results.items() if "analysis" in r}
    if not st.session_state.transcripts:
        st.info("⚓ Complete transcript and Gemini analysis first.")
    else:
        st.markdown('<div class="card"><div class="card-title">📊 Cross-Video Synthesis</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""<div class="stat-row">
<div class="stat-pill"><span class="stat-val">{len(st.session_state.transcripts)}</span><span class="stat-lbl">Transcripts</span></div>
<div class="stat-pill"><span class="stat-val">{len(ok_gem)}</span><span class="stat-lbl">Gemini Analyses</span></div>
</div>""", unsafe_allow_html=True)

        if st.button("📊  Build Synthesis Prompt for Claude", use_container_width=True):
            parts = [
                "MAIC CROSS-VIDEO SYNTHESIS PROMPT","="*60,
                f"Channel: {st.session_state.channel_name}",
                f"Transcripts: {len(st.session_state.transcripts)} | Gemini analyses: {len(ok_gem)}","",
                "Produce a cross-video synthesis addressing:","",
                "1. CONVERGENT THEMES — patterns across multiple videos",
                "   (agency expression, command presence, identity language, occupational justice)","",
                "2. DIVERGENT CASES — where videos contradict each other or your framework","",
                "3. HAPTIC-VISUAL LOOP & EMBODIED FINDINGS",
                "   (emergent concepts where visual data diverged from transcript data)","",
                "4. COMMAND PRESENCE COMPOSITE SCORE COMPARISON across videos","",
                "5. ADAPTIVE SAILING IMPLICATIONS",
                "   (what does this corpus tell us about occupational justice in sailing?)","",
                "6. PHOTOVOICE PROMPT SYNTHESIS — 10 most powerful prompts",
                "   Frame each as: 'Photograph a moment when...'","",
                "7. CURRICULUM IMPLICATIONS",
                "   3 learning objectives for USCG OUPV CTE curriculum","","="*60,
                "TRANSCRIPT DATA:","",
            ]
            for vid_id, data in st.session_state.transcripts.items():
                wc = sum(len(s["text"].split()) for s in data["segments"])
                parts += [f"[TRANSCRIPT] {data['title']}", f"  Words: {wc:,} | URL: {data['url']}", ""]

            if ok_gem:
                parts += ["","="*60,"GEMINI VIDEO ANALYSIS DATA:",""]
                for vid_id, r in ok_gem.items():
                    parts += [f"[GEMINI] {r['title']}", f"  URL: {r['url']}",
                               f"  Preview: {r['analysis'][:600].replace(chr(10),' ')}...",""]

            parts += ["="*60,"Produce a comprehensive dissertation-ready synthesis.", "="*60]
            st.session_state.synthesis = "\n".join(parts)

        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.synthesis:
            st.markdown("### 📋 Paste into Claude.ai for synthesis")
            st.text_area("Synthesis Prompt", value=st.session_state.synthesis, height=300,
                         label_visibility="collapsed")
            st.download_button("⬇️ Download Synthesis Prompt",
                               data=st.session_state.synthesis,
                               file_name=f"MAIC_Synthesis_{st.session_state.channel_name}.txt",
                               mime="text/plain")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 7 — MAIC PROMPTS
# ════════════════════════════════════════════════════════════════════════════════
with t7:
    if not st.session_state.transcripts:
        st.info("⚓ Load transcripts first.")
    else:
        st.markdown('<div class="card"><div class="card-title">📄 Generate MAIC 4-Lens Prompts</div>',
                    unsafe_allow_html=True)
        p_notes = st.text_area("Research notes (embedded in every prompt)",
                               placeholder="Analyzing for post-work identity and command presence...",
                               height=60)
        if st.button("⚓  Generate All MAIC Prompts", use_container_width=True):
            st.session_state.prompts = {}
            prog = st.progress(0)
            items = list(st.session_state.transcripts.items())
            for i, (vid_id, data) in enumerate(items):
                v_dict = {"title": data["title"], "url": data["url"]}
                st.session_state.prompts[vid_id] = {
                    "prompt": maic_prompt(v_dict, data["segments"], p_notes),
                    "title":  data["title"],
                }
                prog.progress((i+1)/len(items))
            st.success(f"✅ {len(st.session_state.prompts)} prompts generated!")
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.prompts:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for vid_id, r in st.session_state.prompts.items():
                    safe = re.sub(r"[^\w]","_",r["title"])[:50]
                    zf.writestr(f"MAIC_{safe}_{vid_id}.txt", r["prompt"])
            buf.seek(0)
            st.download_button(
                f"⬇️  Download All {len(st.session_state.prompts)} Prompts as ZIP",
                data=buf,
                file_name=f"MAIC_{st.session_state.channel_name}_{len(st.session_state.prompts)}prompts.zip",
                mime="application/zip",
                use_container_width=True,
            )
            for vid_id, r in st.session_state.prompts.items():
                with st.expander(f"📄 {r['title'][:70]}"):
                    st.text_area("Prompt", value=r["prompt"], height=250,
                                 label_visibility="collapsed", key=f"pt_{vid_id}")
                    safe = re.sub(r"[^\w]","_",r["title"])[:50]
                    st.download_button("⬇️ Download", data=r["prompt"],
                                       file_name=f"MAIC_{safe}.txt", mime="text/plain",
                                       key=f"pdl_{vid_id}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#2e6da4;font-size:.74rem;padding:.8rem 0 .4rem;border-top:1px solid #1b3a5c;margin-top:1rem">
⚓ MAIC v3.0 · Maritime Agency & Identity Classifier · UFT AI Development Course · Occupational Science PhD
</div>
""", unsafe_allow_html=True)
