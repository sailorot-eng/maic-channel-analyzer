"""
Maritime Agency & Identity Classifier (MAIC)
============================================
A zero-cost qualitative research pre-processor for Occupational Science
dissertation research on sailor identity, adaptive sailing, and Command Presence.

Author: Built for PhD Candidate | Occupational Science | UFT AI Development Course
"""

import streamlit as st
import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MAIC · Maritime Agency & Identity Classifier",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS  — nautical dark-chart aesthetic
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
  /* ── Google Fonts ── */
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Source+Sans+3:wght@300;400;600&display=swap');

  /* ── Root variables ── */
  :root {
    --navy:   #0d1b2a;
    --ocean:  #1b3a5c;
    --steel:  #2e6da4;
    --wake:   #5ba4d4;
    --foam:   #d6eaf8;
    --brass:  #c9a84c;
    --chalk:  #f0f4f8;
    --coral:  #e05555;
    --radius: 10px;
  }

  /* ── Global ── */
  html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
    background-color: var(--navy) !important;
    color: var(--chalk);
  }

  /* ── Main container ── */
  .block-container { padding: 2rem 2.5rem 3rem; max-width: 1100px; }

  /* ── Header / Hero ── */
  .maic-hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b3a5c 60%, #0d2d4a 100%);
    border: 1px solid var(--steel);
    border-radius: var(--radius);
    padding: 2.2rem 2.5rem 1.8rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }
  .maic-hero::before {
    content: "⚓";
    font-size: 9rem;
    opacity: 0.05;
    position: absolute;
    right: 1.5rem;
    top: -1rem;
    line-height: 1;
  }
  .maic-hero h1 {
    font-family: 'Cinzel', serif;
    font-size: 2rem;
    font-weight: 900;
    color: var(--brass);
    letter-spacing: 0.05em;
    margin: 0 0 0.3rem;
  }
  .maic-hero .subtitle {
    font-size: 0.95rem;
    color: var(--foam);
    opacity: 0.85;
    max-width: 700px;
    line-height: 1.55;
  }
  .maic-hero .badge-row {
    margin-top: 1rem;
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
  }
  .badge {
    background: rgba(91,164,212,0.18);
    border: 1px solid var(--wake);
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.75rem;
    color: var(--wake);
    letter-spacing: 0.03em;
  }

  /* ── Section cards ── */
  .card {
    background: var(--ocean);
    border: 1px solid #2a4d6e;
    border-radius: var(--radius);
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.2rem;
  }
  .card-title {
    font-family: 'Cinzel', serif;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    color: var(--brass);
    text-transform: uppercase;
    margin-bottom: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* ── Lens info boxes ── */
  .lens-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.8rem;
    margin-top: 0.5rem;
  }
  .lens-box {
    background: rgba(13,27,42,0.6);
    border-left: 3px solid var(--brass);
    border-radius: 0 6px 6px 0;
    padding: 0.75rem 1rem;
  }
  .lens-box .lens-num {
    font-family: 'Cinzel', serif;
    font-size: 0.7rem;
    color: var(--brass);
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .lens-box .lens-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--foam);
    margin: 0.15rem 0 0.3rem;
  }
  .lens-box .lens-desc {
    font-size: 0.78rem;
    color: #8fbcd4;
    line-height: 1.45;
  }

  /* ── Streamlit widget overrides ── */
  .stTextInput > div > div > input,
  .stTextArea textarea {
    background-color: #0d1b2a !important;
    border: 1px solid var(--steel) !important;
    color: var(--chalk) !important;
    border-radius: 6px !important;
    font-family: 'Source Sans 3', sans-serif !important;
  }
  .stButton > button {
    background: linear-gradient(135deg, var(--steel), var(--ocean)) !important;
    border: 1px solid var(--wake) !important;
    color: white !important;
    border-radius: 6px !important;
    font-family: 'Cinzel', serif !important;
    letter-spacing: 0.06em !important;
    font-size: 0.85rem !important;
    padding: 0.55rem 1.5rem !important;
    transition: all 0.2s ease !important;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #3a8acc, #2e6da4) !important;
    border-color: var(--brass) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(91,164,212,0.25) !important;
  }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--brass), #a07830) !important;
    border-color: var(--brass) !important;
  }

  /* ── Copy box ── */
  .copy-prompt-box {
    background: #07111e;
    border: 1px solid var(--steel);
    border-radius: var(--radius);
    padding: 1.2rem 1.5rem;
    font-family: 'Courier New', monospace;
    font-size: 0.78rem;
    color: #a8d8f0;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 400px;
    overflow-y: auto;
    line-height: 1.55;
  }

  /* ── Stats row ── */
  .stat-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin: 0.5rem 0 1.2rem;
  }
  .stat-pill {
    background: rgba(46,109,164,0.25);
    border: 1px solid var(--steel);
    border-radius: 8px;
    padding: 0.4rem 0.9rem;
    text-align: center;
  }
  .stat-pill .stat-val {
    font-family: 'Cinzel', serif;
    font-size: 1.25rem;
    color: var(--brass);
    font-weight: 700;
  }
  .stat-pill .stat-lbl {
    font-size: 0.7rem;
    color: var(--wake);
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  /* ── Alerts ── */
  .stAlert { border-radius: var(--radius) !important; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #07111e !important;
    border-right: 1px solid #1b3a5c;
  }
  [data-testid="stSidebar"] * { color: var(--chalk) !important; }
  [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    font-family: 'Cinzel', serif !important;
    color: var(--brass) !important;
  }

  /* ── Divider ── */
  hr { border-color: #2a4d6e !important; }

  /* ── Success ── */
  .success-banner {
    background: rgba(91,164,212,0.12);
    border: 1px solid var(--wake);
    border-radius: var(--radius);
    padding: 0.8rem 1.2rem;
    color: var(--foam);
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1rem;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #07111e; }
  ::-webkit-scrollbar-thumb { background: var(--steel); border-radius: 3px; }
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> Optional[str]:
    """
    Parse a YouTube video ID from any common URL format:
      - https://www.youtube.com/watch?v=ID
      - https://youtu.be/ID
      - https://youtube.com/shorts/ID
      - https://www.youtube.com/embed/ID
    """
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_transcript(video_id: str) -> list:
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
                lambda t: t.find_manually_created_transcript(["en", "en-US", "en-GB"]),
                lambda t: t.find_generated_transcript(["en", "en-US", "en-GB"]),
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
            lambda t: t.find_manually_created_transcript(["en", "en-US", "en-GB"]),
            lambda t: t.find_generated_transcript(["en", "en-US", "en-GB"]),
            lambda t: next(iter(t)),
        ]:
            try:
                return attempt(tl).fetch()
            except Exception:
                continue
    except Exception:
        pass

    raise NoTranscriptFound(video_id, ["en"], {})


def clean_transcript(raw: list[dict]) -> str:
    """
    Convert the list of {text, start, duration} dicts into a clean,
    timestampless paragraph string.
    """
    parts = []
    for entry in raw:
        text = entry.get("text", "")
        # Remove [Music], [Applause], etc.
        text = re.sub(r"\[.*?\]", "", text)
        # Collapse multiple whitespace
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            parts.append(text)

    joined = " ".join(parts)
    # Merge repeated spaces / fix common asr artifacts
    joined = re.sub(r" {2,}", " ", joined)
    return joined.strip()


def chunk_text(text: str, chunk_size: int = 800) -> list[str]:
    """
    Split cleaned text into sentence-aware chunks of ~chunk_size characters.
    Tries to break at sentence boundaries (. ! ?) rather than mid-sentence.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= chunk_size:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # If a single sentence exceeds chunk_size, split on word boundaries
            if len(sentence) > chunk_size:
                words = sentence.split()
                buffer = ""
                for word in words:
                    if len(buffer) + len(word) + 1 <= chunk_size:
                        buffer = (buffer + " " + word).strip()
                    else:
                        if buffer:
                            chunks.append(buffer)
                        buffer = word
                if buffer:
                    current = buffer
                else:
                    current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    return chunks


def word_count(text: str) -> int:
    return len(text.split())


def estimate_read_time(wc: int) -> int:
    """Average adult reads ~200 wpm."""
    return max(1, round(wc / 200))


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

COMMAND_PRESENCE_TERMS = [
    "decision", "authority", "responsibility", "situation awareness", "situational awareness",
    "judgment", "calm", "composure", "navigation", "chart", "bearing", "helm",
    "crew", "watch", "weather", "risk", "safe", "safety", "protocol", "rule",
    "right of way", "stand-on", "give-way", "collision", "COLREGS", "VHF",
    "mayday", "pan-pan", "distress", "anchor", "dock", "moor", "throttle",
    "trim", "heel", "capsize", "rescue", "PFD", "life jacket",
    "command", "lead", "leadership", "skipper", "captain", "mate", "crew",
    "communication", "confidence", "adapt", "assess", "plan", "execute",
    "debrief", "lesson", "mistake", "correct", "tack", "jibe", "reef",
]


def build_analysis_prompt(
    cleaned_text: str,
    chunks: list[str],
    video_url: str,
    custom_notes: str = "",
) -> str:
    """
    Wrap the transcript in a richly engineered qualitative analysis prompt
    grounded in Occupational Science, USCG CTE pedagogy, and photovoice research.
    """

    num_chunks = len(chunks)
    wc = word_count(cleaned_text)
    terms_formatted = "\n".join(f"   • {t}" for t in COMMAND_PRESENCE_TERMS)

    # Format chunks for the prompt
    chunks_section = ""
    for i, chunk in enumerate(chunks, 1):
        chunks_section += f"\n--- SEGMENT {i} of {num_chunks} ---\n{chunk}\n"

    custom_block = (
        f"\n\n**RESEARCHER'S NOTES / ADDITIONAL CONTEXT:**\n{custom_notes.strip()}\n"
        if custom_notes.strip()
        else ""
    )

    prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║      MARITIME AGENCY & IDENTITY CLASSIFIER (MAIC)                          ║
║      Qualitative Analysis Prompt — Occupational Science Dissertation        ║
╚══════════════════════════════════════════════════════════════════════════════╝

SOURCE VIDEO : {video_url}
WORD COUNT   : {wc:,} words across {num_chunks} segments
GENERATED BY : MAIC v1.0 — Maritime Agency & Identity Classifier
{custom_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## RESEARCH CONTEXT

You are assisting a PhD candidate in Occupational Science who is also a licensed
USCG Captain and NYC public school occupational therapist. This transcript is
being analyzed for a mixed-methods dissertation study on:

  1. How sailors construct occupational identity and meaning in a post-labor world
     where AI and automation are eroding traditional employment.
  2. How adaptive technologies and co-occupational partnerships enable sailors
     with disabilities to access the maritime environment.
  3. How observable "Command Presence" behaviors in sailing can be extracted as
     competency-based learning objectives for high school CTE students pursuing
     USCG OUPV (6-Pack Captain's License) certification.
  4. How photovoice methodology can empower adaptive sailors to document and
     reflect on moments that build or inhibit Command Presence, feeding into a
     community gallery and curriculum development.

The theoretical grounding spans: Wilcock's Occupational Perspective of Health,
Townsend & Marval's Occupational Justice framework, Heidegger's concept of
"thrownness," and Wenger's Communities of Practice.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## YOUR TASK

Please read ALL transcript segments carefully, then produce a structured
qualitative analysis using EACH of the four analytical lenses below.
Be specific: quote relevant phrases from the transcript (with segment numbers),
identify silences and absences as much as presences, and flag tensions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 1 — Post-Work Occupational Identity & Meaning-Making

**Theoretical Frame:** How do individuals find meaning, temporal structure, and
a coherent sense of self when sailing sits outside the conventional 40-hour
paid work economy? Apply Wilcock's "doing, being, belonging, becoming" model.

**Analytical Questions — answer each explicitly:**
  a) What language does the subject use to describe why they sail?
     (purpose, passion, calling, escape, identity, duty, therapy, etc.)
  b) Is sailing framed as WORK, LEISURE, VOCATION, or something hybrid?
     Provide direct textual evidence.
  c) How does the subject structure time around sailing?
     (routines, seasons, tides, voyages as temporal anchors)
  d) What community or relational belonging does sailing provide?
     (crew relationships, harbormasters, online communities, race clubs)
  e) Is there evidence of "occupational becoming"—growth, mastery, transformation
     of self-concept through sailing practice?
  f) If AI/automation is mentioned (navigation apps, autopilots, weather routing
     AI, electric propulsion), how does the subject position themselves relative
     to these tools? Threat, partner, tool, or irrelevance?
  g) **Post-Work Thesis:** Does this transcript support the hypothesis that
     sailing provides an alternative, non-wage occupational identity matrix?
     Rate your confidence (Low/Medium/High) and explain.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 2 — Occupational Justice, Ableism & Co-Occupation

**Theoretical Frame:** Townsend & Marval's Occupational Justice asks: who gets
to access occupations, and what structural, attitudinal, or environmental
barriers exclude participation? Apply this to adaptive sailing contexts.

**Analytical Questions — answer each explicitly:**
  a) Are there any mentions of disability, chronic illness, injury, aging, or
     neurodivergence (explicit or implied)?
  b) Identify any ADAPTIVE TECHNOLOGIES described or implied:
     (one-hand sailing systems, voice-controlled instruments, accessible
     cockpit layouts, adaptive PFDs, sensory navigation aids, etc.)
  c) Identify any ENVIRONMENTAL MODIFICATIONS to the vessel or marina:
     (ramps, accessible heads, modified winches, tiller extensions, etc.)
  d) Flag any CO-OCCUPATION moments — where two or more people work together
     to accomplish a sailing task that one person could not complete alone,
     especially if one participant has a disability or limitation.
  e) Are there any expressions of OCCUPATIONAL INJUSTICE?
     (being told you can't sail, being excluded from clubs or races,
     financial barriers, geographic barriers to accessible sailing programs)
  f) Identify any language that is explicitly or subtly ABLEIST, even if
     unintentionally so (e.g., "overcoming" disability framing, inspiration
     porn tropes, etc.)
  g) **Photovoice Implication:** What scenes or moments described here would
     make powerful photovoice prompts for adaptive sailors?
     List at least 3 specific suggestions in the format:
       "Photograph a moment when ___________"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 3 — USCG Command Presence: CTE Teaching Case Studies

**Theoretical Frame:** Command Presence in the USCG OUPV (6-Pack) License
framework refers to the constellation of skills that define a competent,
responsible vessel operator: situational awareness, decision-making under
pressure, crew leadership, risk assessment, and regulatory compliance.

**Analytical Questions — answer each explicitly:**
  a) Identify 3–6 CRITICAL INCIDENTS described in this transcript — specific
     moments of decision, emergency, error, or leadership that could serve as
     CTE teaching case studies. For each incident, provide:
       • Segment reference
       • Brief description (2–3 sentences)
       • USCG competency domain it illustrates
       • A discussion question for high school CTE students

  b) Identify any moments of RULE-BASED NAVIGATION decision-making:
     (COLREGS, VHF radio protocol, anchoring rules, right of way, etc.)

  c) Identify any WEATHER DECISION-MAKING described:
     (go/no-go decisions, heaving-to, reefing, seeking shelter, etc.)

  d) Flag any CREW LEADERSHIP moments:
     (assigning roles, briefing, debriefing, managing fear, crew conflict)

  e) Are there any moments where the sailor MADE A MISTAKE and reflected on it?
     These are especially valuable for CTE pedagogy. Describe the reflective
     learning loop demonstrated.

  f) Overall: Rate this transcript's utility as a USCG CTE teaching resource
     (1–10 scale) with a brief rationale.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYTICAL LENS 4 — Ethnographic Command Presence Term Frequency Analysis

**Purpose:** This lens produces a prioritized vocabulary of "Command Presence"
as it actually manifests in authentic sailor discourse, to be used as:
  (a) a coding codebook for the dissertation,
  (b) learning objective language for the adaptive sailing curriculum, and
  (c) photovoice prompt vocabulary for adaptive sailors.

**Instructions:**
  STEP 1 — TERM FREQUENCY COUNT
  Search the entire transcript for each of the following seed terms AND any
  semantically related variants you discover. Count occurrences and note
  which segments they appear in.

  SEED TERMS TO TRACK:
{terms_formatted}

  STEP 2 — OUTPUT TABLE
  Present your findings as a ranked table (highest frequency first):

  | Rank | Term / Phrase | Count | Segments | Command Presence Category |
  |------|--------------|-------|----------|--------------------------|
  | 1    | [term]       | [n]   | [list]   | [category]               |
  ...

  **Command Presence Categories to use:**
    - SITUATIONAL AWARENESS
    - DECISION-MAKING UNDER PRESSURE
    - CREW LEADERSHIP & COMMUNICATION
    - REGULATORY / USCG COMPLIANCE
    - RISK ASSESSMENT & SEAMANSHIP
    - EMOTIONAL REGULATION & COMPOSURE
    - TECHNICAL SKILL / BOAT HANDLING

  STEP 3 — EMERGENT TERMS
  List any additional terms NOT in the seed list that appear frequently and
  seem semantically related to Command Presence in sailing. Include count
  and your rationale for inclusion.

  STEP 4 — PHOTOVOICE VOCABULARY
  From the top 10 terms, generate 10 photovoice prompts in the format:
    "Take a photograph that shows _____________ in your sailing experience."
  These should be accessible, concrete, and actionable for adaptive sailors
  with varying abilities.

  STEP 5 — CURRICULUM IMPLICATION
  In 150–200 words, synthesize: What does this frequency analysis suggest
  about how Command Presence is ACTUALLY constructed through sailor discourse,
  compared to how it is formally defined in USCG training materials?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FINAL SYNTHESIS (Required)

After completing all four lenses, write a 300–400 word DISSERTATION MEMO in
academic qualitative research voice that:

  1. Summarizes the most significant findings across all four lenses.
  2. Identifies convergent themes that appear across multiple lenses.
  3. Flags any data that CHALLENGES or COMPLICATES your theoretical framework.
  4. Recommends 2–3 follow-up interview questions you would ask this sailor
     if you could conduct a member-checking session.
  5. Assigns an overall ANALYTICAL RICHNESS SCORE (1–10) for this transcript
     as a dissertation data source, with brief rationale.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TRANSCRIPT DATA — BEGIN ANALYSIS

The transcript has been segmented into {num_chunks} sections for readability.
Please analyze ALL segments before beginning your structured response.

{chunks_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF TRANSCRIPT. Please now produce your full four-lens qualitative analysis
and final dissertation memo as instructed above.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    return prompt.strip()




# ─────────────────────────────────────────────────────────────────────────────
# GEMINI VIDEO ANALYSIS PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

CODEBOOK_DOMAINS = {
    "A": {
        "name": "Occupational Agency",
        "codes": {
            "A1": "Environmental Reading — assessing wind, sea state, weather, traffic",
            "A2": "Intentional Decision-Making — conscious choices at critical junctures",
            "A3": "Self-Efficacy & Competence Narration — expressed belief in own ability",
            "A4": "Adaptive Problem-Solving — improvising when standard approaches fail",
            "A5": "Co-Occupation & Collaborative Agency — joint agency with crew/partner",
        }
    },
    "B": {
        "name": "Command Presence",
        "codes": {
            "B1": "Situational Awareness — continuous monitoring of vessel, crew, environment",
            "B2": "Voice & Communication Authority — clarity, tone, brevity under pressure",
            "B3": "Regulatory Knowledge & Application — COLREGS, VHF, maritime protocol",
            "B4": "Risk Assessment & Seamanship — go/no-go decisions, conservative seamanship",
            "B5": "Emotional Regulation & Composure — calm function under fear/fatigue/stress",
            "B6": "Crew Leadership & Mentorship — developing others' competence and agency",
        }
    },
    "C": {
        "name": "Occupational Identity & Meaning",
        "codes": {
            "C1": "Sailor Identity Claim — sailing as central to sense of self",
            "C2": "Meaning & Purpose Narration — why sailing matters beyond recreation",
            "C3": "Temporal Structure & Occupation — sailing as rhythm and routine",
        }
    },
    "D": {
        "name": "Occupational Justice & Adaptive Sailing",
        "codes": {
            "D1": "Adaptive Technology — modifications enabling participation",
            "D2": "Occupational Injustice — barriers that exclude or marginalize",
            "D3": "Occupational Enablement — structures enabling adaptive participation",
        }
    },
    "E": {
        "name": "Post-Work Identity",
        "codes": {
            "E1": "Non-Wage Occupation — sailing as primary occupation outside employment",
            "E2": "AI & Automation Relationship — positioning relative to technological tools",
        }
    }
}


def build_gemini_prompt(video_url: str, researcher_notes: str = "",
                        focus_codes: list = None) -> str:
    """
    Build a Gemini-specific multimodal video analysis prompt.
    Gemini can watch YouTube videos directly — this prompt instructs it
    to code for agency and command presence across verbal, visual,
    and paralinguistic channels simultaneously.
    """

    # Build codebook section
    codebook_text = ""
    for domain_id, domain in CODEBOOK_DOMAINS.items():
        if focus_codes:
            relevant = {k: v for k, v in domain["codes"].items()
                       if k in focus_codes}
            if not relevant:
                continue
            codebook_text += f"\n**DOMAIN {domain_id}: {domain['name']}**\n"
            for code_id, desc in relevant.items():
                codebook_text += f"  [{code_id}] {desc}\n"
        else:
            codebook_text += f"\n**DOMAIN {domain_id}: {domain['name']}**\n"
            for code_id, desc in domain["codes"].items():
                codebook_text += f"  [{code_id}] {desc}\n"

    notes_block = (
        f"\n\n**RESEARCHER NOTES / CONTEXT:**\n{researcher_notes.strip()}\n"
        if researcher_notes.strip() else ""
    )

    focus_note = ""
    if focus_codes:
        focus_note = f"\n**PRIORITY CODES FOR THIS ANALYSIS:** {', '.join(focus_codes)}\n"

    prompt = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   MAIC — MULTIMODAL ETHNOGRAPHIC VIDEO ANALYSIS                            ║
║   Gemini Video Coding Prompt — Occupational Science Dissertation           ║
╚══════════════════════════════════════════════════════════════════════════════╝

VIDEO URL    : {video_url}
ANALYSIS TYPE: Multimodal Ethnographic Qualitative Coding
PASTE INTO   : gemini.google.com (Gemini 1.5 Pro — supports YouTube video input)
{notes_block}{focus_note}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## INSTRUCTIONS TO GEMINI

Please watch the YouTube video at the URL above in its entirety. You are
acting as a qualitative research assistant for a PhD dissertation in
Occupational Science. Your task is to perform ethnographic qualitative
coding of this sailing video across THREE data channels simultaneously:

  (V)  VERBAL     — what is said (words, narration, dialogue)
  (VI) VISUAL     — what is shown (body language, environment, equipment,
                    facial expression, posture, helm behavior, crew dynamics)
  (P)  PARALINGUISTIC — HOW things are said (tone, pace, pitch, hesitation,
                    composure under pressure, silence)

This is NOT a summary. This is structured qualitative coding using the
codebook below. Every coded moment must include:
  • Timestamp (MM:SS or HH:MM:SS)
  • Code ID (e.g., B5)
  • Data channel (V / VI / P)
  • Direct evidence (quote or visual description)
  • Analytical note (1–2 sentences interpreting the evidence)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## CODEBOOK — APPLY THESE CODES TO THE VIDEO
{codebook_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## CODING OUTPUT FORMAT

### SECTION 1 — CODED MOMENTS TABLE

Present your coded moments in this format:

| Timestamp | Code | Channel | Evidence | Analytical Note |
|-----------|------|---------|----------|-----------------|
| 03:42 | B5 | P | Voice remains flat and measured while describing 35-knot squall | Demonstrates emotional regulation — paralinguistic composure signals command presence even in recalled crisis |
| 07:15 | A2 | V | "We had two options. I chose to heave-to." | Explicit decision narration with ownership language — hallmark of intentional agency |
| 12:03 | B1 | VI | Sailor scans horizon, checks instruments, looks at crew before speaking | 3-point situational awareness check performed instinctively — non-verbal command competency |

Code as many moments as you find. Quality over quantity — only code moments
with clear, defensible evidence.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 2 — CODE FREQUENCY SUMMARY

After completing the table, produce a frequency count:

| Code | Code Name | V Count | VI Count | P Count | Total | Density |
|------|-----------|---------|----------|---------|-------|---------|

Density = Total coded moments ÷ video length in minutes (codes per minute)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 3 — COMMAND PRESENCE COMPOSITE SCORE (CPCS)

Rate each domain 0–3 based on evidence quality and frequency:
  0 = Absent from this video
  1 = Present but brief or weak
  2 = Present and clearly demonstrated
  3 = Strong, sustained, exemplary

| Domain | Code | Rating (0-3) | Weight | Weighted Score |
|--------|------|-------------|--------|----------------|
| Situational Awareness | B1 | ? | 20% | ? |
| Decision-Making | A2 + B4 | ? | 25% | ? |
| Communication Authority | B2 | ? | 20% | ? |
| Emotional Regulation | B5 | ? | 20% | ? |
| Regulatory Knowledge | B3 | ? | 15% | ? |

**CPCS = (sum of weighted scores) × 33.3**
(Scale: 0–100. Score 70+ = rich CTE teaching case study)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 4 — KEY MOMENTS FOR PHOTOVOICE & CTE TEACHING

Identify the 5 most powerful moments in the video — moments that best
illustrate agency and command presence for:
  (a) CTE classroom discussion with high school students pursuing USCG OUPV
  (b) Photovoice prompts for adaptive sailors

For each moment:
  • Timestamp
  • What is happening (verbal + visual description)
  • Which codes apply
  • Suggested CTE discussion question
  • Suggested photovoice prompt that connects to this moment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 5 — WHAT THE TRANSCRIPT MISSES

This is critical for the dissertation's methodological contribution.

Describe 3–5 moments where the VISUAL or PARALINGUISTIC data tells a
different or richer story than the words alone. These are your cases
for arguing why multimodal analysis is essential to understanding
agency and command presence in sailing — and why transcript-only
coding is insufficient for this research question.

Format:
  Timestamp: XX:XX
  What the transcript says: "..."
  What the video shows/sounds: [describe]
  Methodological significance: [1–2 sentences]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SECTION 6 — DISSERTATION MEMO

Write a 250–350 word analytical memo suitable for inclusion in a
dissertation field notes document. Address:

  1. Overall assessment of agency and command presence in this video
  2. Most significant finding across all three data channels
  3. How this video's evidence relates to the post-work identity thesis
  4. One finding that surprised you or challenged your expectations
  5. Recommended follow-up: what would you want to ask this sailor?
  6. Recommended use: transcript coding, CTE case study, photovoice seed,
     or longitudinal comparison

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
END OF CODING INSTRUCTIONS. Please watch the full video and produce your
complete multimodal ethnographic analysis as specified above.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".strip()
    return prompt



# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚓ MAIC Guide")
    st.markdown(
        """
**Maritime Agency & Identity Classifier**

A zero-cost qualitative research pre-processor for Occupational Science.

---

### How to Use

1. Paste any public YouTube URL
2. *(Optional)* Add your own research notes
3. Click **Extract & Build Prompt**
4. Copy the generated prompt
5. Paste into **Claude, ChatGPT, or Gemini**

---

### Zero-Cost Philosophy

This tool extracts transcripts without a paid YouTube API key and generates
a fully engineered prompt — so your AI analysis costs **$0**.

---

### The 4 Analytical Lenses

🌊 **Post-Work Identity**  
🦾 **Occupational Justice**  
⚓ **USCG Command Presence**  
📊 **Term Frequency Coding**

---

### Paste Into
"""
    )
    st.markdown(
        "- [Claude.ai](https://claude.ai) (recommended)\n"
        "- [ChatGPT](https://chat.openai.com)\n"
        "- [Gemini](https://gemini.google.com)"
    )
    st.markdown("---")
    st.markdown(
        "<small style='color:#5ba4d4'>Built for UFT AI Development Course<br>"
        "PhD Candidate · Occupational Science</small>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="maic-hero">
  <h1>⚓ MAIC</h1>
  <div style="font-family:'Cinzel',serif; font-size:0.85rem; letter-spacing:0.12em;
              color:#5ba4d4; text-transform:uppercase; margin-bottom:0.6rem;">
    Maritime Agency &amp; Identity Classifier
  </div>
  <div class="subtitle">
    A zero-cost qualitative research pre-processor. Paste a YouTube sailing video URL,
    and MAIC will extract the transcript and wrap it in a richly engineered
    Occupational Science analysis prompt — ready to paste into any free AI chatbot.
  </div>
  <div class="badge-row">
    <span class="badge">🎓 PhD Dissertation Tool</span>
    <span class="badge">⚓ USCG CTE Pedagogy</span>
    <span class="badge">♿ Adaptive Sailing</span>
    <span class="badge">📸 Photovoice Research</span>
    <span class="badge">💰 Zero API Cost</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# TABS — Transcript Analysis | Video Analysis (Gemini) | Codebook
# ─────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    "📄 Transcript Analysis (Claude/ChatGPT)",
    "🎬 Video Analysis (Gemini)",
    "📋 Codebook"
])

with tab1:
    # ─────────────────────────────────────────────────────────────────────────────
    # LENS OVERVIEW CARDS
    # ─────────────────────────────────────────────────────────────────────────────
    
    st.markdown(
        """
    <div class="card">
      <div class="card-title">🔭 The Four Analytical Lenses</div>
      <div class="lens-grid">
        <div class="lens-box">
          <div class="lens-num">Lens 1</div>
          <div class="lens-title">Post-Work Identity</div>
          <div class="lens-desc">How do sailors find meaning, structure, and occupational identity outside the 40-hour wage economy? Grounded in Wilcock's doing-being-belonging-becoming model.</div>
        </div>
        <div class="lens-box">
          <div class="lens-num">Lens 2</div>
          <div class="lens-title">Occupational Justice &amp; Ableism</div>
          <div class="lens-desc">Adaptive technologies, environmental modifications, co-occupation, and barriers to participation. Identifies photovoice prompt opportunities.</div>
        </div>
        <div class="lens-box">
          <div class="lens-num">Lens 3</div>
          <div class="lens-title">USCG Command Presence — CTE Cases</div>
          <div class="lens-desc">Flags critical incidents of decision-making, leadership, and maritime responsibility as teaching case studies for high school OUPV license students.</div>
        </div>
        <div class="lens-box">
          <div class="lens-num">Lens 4</div>
          <div class="lens-title">Term Frequency Coding</div>
          <div class="lens-desc">Ethnographic frequency count of Command Presence vocabulary — produces a ranked codebook, photovoice prompts, and curriculum synthesis.</div>
        </div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
    
    # ─────────────────────────────────────────────────────────────────────────────
    # INPUT SECTION
    # ─────────────────────────────────────────────────────────────────────────────
    
    st.markdown(
        '<div class="card"><div class="card-title">📡 Step 1 — Enter YouTube URL</div>',
        unsafe_allow_html=True,
    )
    
    youtube_url = st.text_input(
        label="YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Any public YouTube video with captions/subtitles enabled. Works with auto-generated captions too.",
        label_visibility="collapsed",
    )
    
    chunk_size = st.select_slider(
        "Segment size (characters per chunk)",
        options=[400, 600, 800, 1000, 1200, 1500],
        value=800,
        help="Smaller chunks = more segments but easier for AI to process. Larger = fewer segments.",
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Optional researcher notes
    custom_notes = ""
    with st.expander("📝 Optional: Add Your Research Notes / Context", expanded=False):
        custom_notes = st.text_area(
            "Researcher notes",
            placeholder=(
                "e.g., 'This sailor is a double amputee who races competitively. "
                "Pay particular attention to how they describe boat modifications.' "
                "Or: 'This video is from a Blind Sailing International event.'"
            ),
            height=120,
            label_visibility="collapsed",
        )
    
    # ─────────────────────────────────────────────────────────────────────────────
    # MAIN ACTION
    # ─────────────────────────────────────────────────────────────────────────────
    
    col_btn, col_spacer = st.columns([2, 5])
    with col_btn:
        run_button = st.button("⚓  Extract & Build Prompt", use_container_width=True)
    
    # ─────────────────────────────────────────────────────────────────────────────
    # PROCESSING
    # ─────────────────────────────────────────────────────────────────────────────
    
    if run_button:
        if not youtube_url.strip():
            st.error("⚠️  Please enter a YouTube URL before running.")
        else:
            video_id = extract_video_id(youtube_url.strip())
            if not video_id:
                st.error(
                    "⚠️  Could not parse a valid YouTube video ID from that URL. "
                    "Please check the link and try again."
                )
            else:
                with st.spinner("🌊  Fetching transcript from YouTube..."):
                    try:
                        raw_transcript = fetch_transcript(video_id)
                        cleaned = clean_transcript(raw_transcript)
                        chunks = chunk_text(cleaned, chunk_size=chunk_size)
                        prompt = build_analysis_prompt(
                            cleaned, chunks, youtube_url, custom_notes
                        )
    
                        # ── Stats ──
                        wc = word_count(cleaned)
                        read_min = estimate_read_time(wc)
    
                        st.markdown(
                            '<div class="success-banner">✅  Transcript extracted and analysis prompt generated successfully!</div>',
                            unsafe_allow_html=True,
                        )
    
                        st.markdown(
                            f"""
    <div class="stat-row">
      <div class="stat-pill">
        <div class="stat-val">{wc:,}</div>
        <div class="stat-lbl">Words</div>
      </div>
      <div class="stat-pill">
        <div class="stat-val">{len(chunks)}</div>
        <div class="stat-lbl">Segments</div>
      </div>
      <div class="stat-pill">
        <div class="stat-val">~{read_min} min</div>
        <div class="stat-lbl">Read Time</div>
      </div>
      <div class="stat-pill">
        <div class="stat-val">{len(prompt):,}</div>
        <div class="stat-lbl">Prompt Chars</div>
      </div>
      <div class="stat-pill">
        <div class="stat-val">4</div>
        <div class="stat-lbl">Lenses Active</div>
      </div>
    </div>
    """,
                            unsafe_allow_html=True,
                        )
    
                        # ── Prompt display + copy ──
                        st.markdown(
                            '<div class="card"><div class="card-title">🗂️ Step 2 — Your Analysis Prompt</div>',
                            unsafe_allow_html=True,
                        )
    
                        st.markdown(
                            "👇 **Select all text in the box below (Ctrl+A or Cmd+A) and copy it, "
                            "then paste into Claude, ChatGPT, or Gemini.**",
                        )
    
                        # Use st.text_area so users can easily select all & copy
                        st.text_area(
                            label="Generated Prompt",
                            value=prompt,
                            height=350,
                            label_visibility="collapsed",
                            key="prompt_output",
                        )
    
                        # Download button as backup
                        st.download_button(
                            label="⬇️  Download Prompt as .txt",
                            data=prompt,
                            file_name=f"MAIC_prompt_{video_id}.txt",
                            mime="text/plain",
                            help="Download the full prompt as a text file if copying is difficult.",
                        )
    
                        st.markdown("</div>", unsafe_allow_html=True)
    
                        # ── Preview of raw transcript ──
                        with st.expander("🔍 Preview: Cleaned Transcript (first 2,000 characters)", expanded=False):
                            st.markdown(
                                f'<div class="copy-prompt-box">{cleaned[:2000]}{"…" if len(cleaned) > 2000 else ""}</div>',
                                unsafe_allow_html=True,
                            )
    
                        # ── How to use instructions ──
                        st.markdown(
                            """
    <div class="card">
    <div class="card-title">🧭 Step 3 — Paste Into a Free AI & Get Your Analysis</div>
    
    **Recommended workflow:**
    
    1. Click inside the text box above → **Ctrl+A** (Windows) or **Cmd+A** (Mac) to select all
    2. **Ctrl+C / Cmd+C** to copy
    3. Open **[Claude.ai](https://claude.ai)** (free tier works fine) — or ChatGPT / Gemini
    4. Start a new chat and **paste** (Ctrl+V / Cmd+V) the entire prompt
    5. Press Enter — the AI will produce your full four-lens qualitative analysis
    
    **Pro tip:** Claude tends to follow complex multi-part structured prompts most reliably.
    If the response is cut off, simply type *"Please continue"* to resume.
    </div>
    """,
                            unsafe_allow_html=True,
                        )
    
                    except VideoUnavailable:
                        st.error(
                            "❌  This video is unavailable or private. "
                            "Please use a public YouTube video."
                        )
                    except TranscriptsDisabled:
                        st.error(
                            "❌  Transcripts are disabled for this video. "
                            "Try a different video, or one where the creator has enabled captions."
                        )
                    except NoTranscriptFound:
                        st.error(
                            "❌  No English transcript was found for this video. "
                            "The video may only have captions in another language, "
                            "or captions may not be available."
                        )
                    except Exception as e:
                        st.error(f"❌  An unexpected error occurred: {e}")
                        st.info(
                            "If the error persists, check that the URL is a standard public "
                            "YouTube link and the video has captions enabled."
                        )
    
    
with tab2:
    st.markdown("""
<div class="maic-hero" style="margin-bottom:1rem;">
  <h1 style="font-size:1.4rem;">🎬 Multimodal Video Analysis</h1>
  <div class="subtitle">
    Gemini can <strong>watch YouTube videos directly</strong> — paste the generated
    prompt into <a href="https://gemini.google.com" style="color:#c9a84c;">gemini.google.com</a>
    and it will code the video for agency and command presence across verbal,
    visual, and paralinguistic channels simultaneously.
  </div>
</div>
""", unsafe_allow_html=True)

    # Info cards
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
<div class="card" style="text-align:center;">
  <div style="font-size:2rem;">🎬</div>
  <div style="font-family:'Cinzel',serif;font-size:.75rem;color:#c9a84c;margin:.4rem 0;">Watches the Video</div>
  <div style="font-size:.8rem;color:#8fbcd4;">Gemini sees body language, helm behavior, crew dynamics — not just words</div>
</div>
""", unsafe_allow_html=True)
    with col_b:
        st.markdown("""
<div class="card" style="text-align:center;">
  <div style="font-size:2rem;">📊</div>
  <div style="font-family:'Cinzel',serif;font-size:.75rem;color:#c9a84c;margin:.4rem 0;">Structured Coding</div>
  <div style="font-size:.8rem;color:#8fbcd4;">Applies the MAIC codebook with timestamps, code IDs, and evidence</div>
</div>
""", unsafe_allow_html=True)
    with col_c:
        st.markdown("""
<div class="card" style="text-align:center;">
  <div style="font-size:2rem;">🔬</div>
  <div style="font-family:'Cinzel',serif;font-size:.75rem;color:#c9a84c;margin:.4rem 0;">Triangulation</div>
  <div style="font-size:.8rem;color:#8fbcd4;">Use alongside transcript analysis to build multimodal validity</div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="card"><div class="card-title">🎬 Enter YouTube URL for Video Analysis</div>', unsafe_allow_html=True)

    gem_url = st.text_input(
        "YouTube URL for Gemini Analysis",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
        key="gem_url",
    )

    gem_notes = st.text_area(
        "Researcher context (optional)",
        placeholder="e.g., Focus on the skipper's body language during the storm sequence. Note any moments of co-occupation with the crew.",
        height=80,
        key="gem_notes",
    )

    # Code focus selector
    st.markdown("**Select focus codes** (leave all checked for full analysis):")
    all_codes = []
    for domain_id, domain in CODEBOOK_DOMAINS.items():
        for code_id in domain["codes"]:
            all_codes.append(code_id)

    col_codes = st.columns(4)
    selected_codes = []
    for i, code_id in enumerate(all_codes):
        domain_id = code_id[0]
        domain = CODEBOOK_DOMAINS[domain_id]
        desc   = domain["codes"][code_id]
        short  = desc.split("—")[0].strip()
        with col_codes[i % 4]:
            if st.checkbox(f"{code_id}: {short}", value=True, key=f"code_{code_id}"):
                selected_codes.append(code_id)

    st.markdown("</div>", unsafe_allow_html=True)

    gem_btn_col, _ = st.columns([2, 5])
    with gem_btn_col:
        gem_btn = st.button("🎬  Generate Gemini Prompt", use_container_width=True, key="gem_btn")

    if gem_btn:
        if not gem_url.strip():
            st.error("Please enter a YouTube URL.")
        else:
            vid_id_check = extract_video_id(gem_url.strip())
            if not vid_id_check:
                st.error("Could not parse a valid YouTube video ID from that URL.")
            else:
                focus = selected_codes if len(selected_codes) < len(all_codes) else None
                gem_prompt = build_gemini_prompt(gem_url.strip(), gem_notes, focus)

                st.markdown("""
<div style="background:rgba(201,168,76,.12);border:1px solid rgba(201,168,76,.4);
     border-radius:8px;padding:.7rem 1rem;font-size:.85rem;color:#c9a84c;margin-bottom:.8rem;">
  ✅ Gemini prompt generated! Copy it below and paste into
  <a href="https://gemini.google.com" target="_blank" style="color:#e8c96a;font-weight:600;">gemini.google.com</a>
  — Gemini will watch the video and return structured qualitative coding.
</div>
""", unsafe_allow_html=True)

                col_header, col_copy = st.columns([4, 1])
                with col_header:
                    st.markdown("<span style='font-size:.85rem;color:#5ba4d4;'>Click inside → Ctrl+A → Ctrl+C, or use the Copy button</span>", unsafe_allow_html=True)
                with col_copy:
                    pass

                st.text_area(
                    "Gemini Prompt",
                    value=gem_prompt,
                    height=320,
                    label_visibility="collapsed",
                    key="gem_output",
                )

                vid_id_g = extract_video_id(gem_url.strip())
                st.download_button(
                    "⬇️ Download Gemini Prompt as .txt",
                    data=gem_prompt,
                    file_name=f"MAIC_Gemini_{vid_id_g}.txt",
                    mime="text/plain",
                )

                st.markdown("""
<div class="card" style="margin-top:1rem;">
<div class="card-title">🧭 How to Use This in Gemini</div>
<div style="font-size:.85rem;color:#d6eaf8;line-height:1.8;">
  <strong style="color:#c9a84c;">Step 1</strong> — Go to
  <a href="https://gemini.google.com" style="color:#5ba4d4;">gemini.google.com</a>
  and sign in with a Google account<br>
  <strong style="color:#c9a84c;">Step 2</strong> — Make sure you're using
  <strong>Gemini 1.5 Pro</strong> (free tier works — select from the model dropdown)<br>
  <strong style="color:#c9a84c;">Step 3</strong> — Paste the entire prompt above into the chat<br>
  <strong style="color:#c9a84c;">Step 4</strong> — Gemini will watch the video and return a
  full coded analysis with timestamps<br>
  <strong style="color:#c9a84c;">Step 5</strong> — Compare with your MAIC transcript analysis
  (Tab 1) to triangulate findings<br><br>
  <span style="color:#8fbcd4;font-size:.8rem;">
  <strong>Methodological note:</strong> Section 5 of Gemini's output ("What the Transcript Misses")
  is your key evidence for why multimodal analysis is necessary — save this for
  your dissertation's methods chapter.
  </span>
</div>
</div>
""", unsafe_allow_html=True)


with tab3:
    st.markdown("""
<div class="maic-hero" style="margin-bottom:1rem;">
  <h1 style="font-size:1.4rem;">📋 MAIC Qualitative Codebook</h1>
  <div class="subtitle">
    The formal coding schema for agency and command presence in sailing.
    Use this codebook with MAIC transcript analysis, Gemini video analysis,
    and manual ethnographic coding. Download for NVivo, MAXQDA, or field notes.
  </div>
</div>
""", unsafe_allow_html=True)

    # Domain cards
    for domain_id, domain in CODEBOOK_DOMAINS.items():
        st.markdown(f'<div class="card"><div class="card-title">Domain {domain_id}: {domain["name"]}</div>', unsafe_allow_html=True)
        for code_id, desc in domain["codes"].items():
            parts = desc.split("—")
            code_name = parts[0].strip()
            code_def  = parts[1].strip() if len(parts) > 1 else ""
            st.markdown(
                f"<div style='padding:.4rem 0;border-bottom:1px solid #1b3a5c;'>"
                f"<span style='font-family:Cinzel,serif;color:#c9a84c;font-size:.8rem;'>[{code_id}]</span> "
                f"<strong style='color:#d6eaf8;'>{code_name}</strong>"
                f"<span style='color:#8fbcd4;font-size:.82rem;'> — {code_def}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Command Presence Composite Score explainer
    st.markdown("""
<div class="card">
<div class="card-title">⚓ Command Presence Composite Score (CPCS)</div>
<div style="font-size:.85rem;color:#d6eaf8;line-height:1.8;">
Rate each domain 0–3 based on evidence:
<br>0 = Absent &nbsp;|&nbsp; 1 = Present but weak &nbsp;|&nbsp;
2 = Clearly demonstrated &nbsp;|&nbsp; 3 = Strong and sustained
<br><br>
<strong style="color:#c9a84c;">Weights:</strong>
Situational Awareness (B1) 20% ·
Decision-Making (A2+B4) 25% ·
Communication (B2) 20% ·
Emotional Regulation (B5) 20% ·
Regulatory Knowledge (B3) 15%
<br><br>
<strong style="color:#c9a84c;">CPCS = weighted average × 33.3 (0–100 scale)</strong>
<br>
Videos scoring 70+ are your richest CTE teaching case studies.
</div>
</div>
""", unsafe_allow_html=True)

    # Download codebook
    try:
        with open("MAIC_Codebook_v1.md", "r") as f:
            codebook_text = f.read()
    except Exception:
        codebook_text = "Codebook file not found. Please ensure MAIC_Codebook_v1.md is in the repository."

    st.download_button(
        "⬇️ Download Full Codebook as .md",
        data=codebook_text,
        file_name="MAIC_Codebook_v1.md",
        mime="text/markdown",
        use_container_width=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
<div style="text-align:center; color:#2e6da4; font-size:0.78rem; padding:1rem 0 0.5rem;
            border-top:1px solid #1b3a5c; font-family:'Source Sans 3',sans-serif;">
  ⚓ MAIC · Maritime Agency &amp; Identity Classifier · v1.0<br>
  <span style="color:#1b3a5c;">
    Built for UFT AI Development Course · Occupational Science PhD Research ·
    Zero API Cost · Open Source
  </span>
</div>
""",
    unsafe_allow_html=True,
)
