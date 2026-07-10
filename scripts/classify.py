"""Distinguish a SOLO stand-up (monologue) from CONVERSATIONAL content
(podcast, interview, ЧБД/roast, talk-show, improv, crowd-heavy panels).

Why this exists
---------------
Expanding the corpus via channel/ytsearch enumeration surfaces a lot of
non-concert material: podcasts, interviews, roasts, panel shows. Their
transcripts contain OTHER people's speech, which pollutes the "unique lemmas"
metric (which is supposed to measure ONE comic's vocabulary).

The signal
----------
YouTube auto-captions insert a ">>" marker (stored as "&gt;&gt;") whenever a
NEW SPEAKER starts. A solo monologue has almost none; a conversation has many.
Empirically, over 645 known-good concert tracks: median 0 markers/min,
p95 = 1.7, p99 = 4.7, <1% above 5/min. Conversational content sits at
30-50 markers/min. So markers/min cleanly separates the two with a huge margin.

Crucially, ">>" counts OTHER speech that actually made it into the transcript.
Pure crowd-work where the audience is off-mic produces no markers (only the
comic's words are captioned) - which is exactly what we want to keep.

Verdict bands (markers/min):
    <= 5   -> keep    (solo monologue / concert, incl. mild crowd work)
    5 - 15 -> review  (rare; heavy crowd-work concert OR light dialogue)
    > 15   -> reject  (conversational: podcast / interview / panel)

Plus cheap pre-filters that need no download:
    duration < 10 min                 -> too_short
    title matches a conversational fmt -> reject (podcast/interview/ЧБД/...)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw_subs"

MIN_DURATION_SEC = 10 * 60          # user floor: 10 minutes
KEEP_MAX_MPM = 5.0                  # <= keep
REVIEW_MAX_MPM = 15.0              # (5, 15] review; > reject

# Conversational-format keywords in the TITLE. These formats are, by name,
# multi-person and should never enter a solo-vocabulary corpus. A match here is
# a HARD reject: the format itself is unambiguous.
TITLE_BLOCKLIST = [
    "подкаст", "podcast", "интервью", "interview", "разговор", "беседа",
    "диалог", "баттл", "battle", "прожарк", "roast", "ток-шоу", "ток шоу",
    "talkshow", "talk show", "импровизац", "improvisation", "improv",
    "что было дальше", "чбд", "квартирник", "открытый микрофон", "опен майк",
    "open mic", "q&a", "вопрос-ответ", "ответы на вопросы", "реакция",
    "reaction", "обзор", "разбор", "вдвоём", "вдвоем", "мне стыдно",
    "камеди баттл", "comedy баттл", "stand up баттл",
]
# Collab markers ("A x B", "A × B", "A vs B", "feat"): two performers. Only a
# STANDALONE separator counts - never the Russian prepositions в/с/у, which the
# earlier character-class version wrongly matched ("Концерт В Киеве").
# Collab is a SOFT signal (-> review), because a lone " х " can misfire; the
# markers/min check is the authoritative backstop.
COLLAB_RE = re.compile(r"\s[xх×]\s|\bvs\.?\b|\bfeat\b|\bft\.?\b", re.I)

MARKER_RE = re.compile(r"&gt;&gt;|>>")
TS_RE = re.compile(r"(\d{2}):(\d{2}):(\d{2})")


def count_markers(vtt_text: str) -> int:
    return len(MARKER_RE.findall(vtt_text))


def last_timestamp_sec(vtt_text: str) -> int:
    t = 0
    for m in TS_RE.finditer(vtt_text):
        t = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
    return t


def title_flag(title: str) -> tuple[str | None, str | None]:
    """Return (hard_reason, soft_reason). hard -> reject, soft -> review."""
    t = (title or "").lower()
    for kw in TITLE_BLOCKLIST:
        if kw in t:
            return f"title:{kw}", None
    if COLLAB_RE.search(f" {t} "):
        return None, "title:collab"
    return None, None


def classify(vtt_text: str, duration_sec: int | None, title: str = "") -> dict:
    """Classify one item. `vtt_text` is the RAW .vtt (markers intact)."""
    dur = duration_sec or last_timestamp_sec(vtt_text)
    markers = count_markers(vtt_text)
    mpm = markers / (dur / 60) if dur else 0.0

    reasons = []
    verdict = "keep"

    hard, soft = title_flag(title)
    if hard:
        verdict = "reject"
        reasons.append(hard)
    if soft and verdict != "reject":
        verdict = "review"
        reasons.append(soft)

    if dur and dur < MIN_DURATION_SEC:
        verdict = "reject"
        reasons.append(f"too_short:{dur // 60}m")

    if mpm > REVIEW_MAX_MPM:
        verdict = "reject"
        reasons.append(f"markers:{mpm:.1f}/min")
    elif mpm > KEEP_MAX_MPM:
        if verdict != "reject":
            verdict = "review"
        reasons.append(f"markers:{mpm:.1f}/min")

    return {
        "verdict": verdict,
        "markers_per_min": round(mpm, 2),
        "markers": markers,
        "duration_sec": dur,
        "reasons": reasons,
    }


def classify_video_id(vid: str, duration_sec: int | None = None,
                      title: str = "") -> dict | None:
    """Classify by cached raw_subs/<vid>*.vtt. Returns None if no track."""
    cached = sorted(RAW.glob(f"{vid}*.vtt"))
    if not cached:
        return None
    text = cached[0].read_text(encoding="utf-8", errors="ignore")
    if duration_sec is None:
        info = RAW / f"{vid}.info.json"
        if info.exists():
            try:
                duration_sec = json.loads(info.read_text()).get("duration")
            except Exception:
                pass
    return classify(text, duration_sec, title)


if __name__ == "__main__":
    p = Path(sys.argv[1])
    txt = p.read_text(encoding="utf-8", errors="ignore")
    print(json.dumps(classify(txt, None, sys.argv[2] if len(sys.argv) > 2 else ""),
                     ensure_ascii=False, indent=2))
