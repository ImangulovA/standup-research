"""Discover NEW stand-up candidates per comic via YouTube search, filter out
non-concert formats, dedup against the existing corpus, and (optionally)
download subtitles to score each with the monologue-vs-conversation detector.

smeshno.xyz is exhausted (350 concerts total, only +7 new). The real corpus
growth comes from each comic's own channel + label uploads. This tool finds
them, then classify.py decides which are real solo concerts.

Flow:
    discover.py --targets           # near-threshold comics (18k-25k words)
    discover.py --artist "Имя" ...  # specific comics
    add --fetch to download subs and attach a monologue/conversation verdict.

Writes expansion/candidates.json (append/merge, dedup by video_id). Feed the
result to build_review.py to get a human review page.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classify import classify, title_flag, MIN_DURATION_SEC
from process import fetch_subs, video_id_from_url  # reuse cached, bot-wall-safe

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
EXP = ROOT / "expansion"
CANDIDATES = EXP / "candidates.json"
REPORT = ROOT / "report.json"

YTDLP = [sys.executable, "-m", "yt_dlp",
         "--extractor-args", "youtube:player_client=android,ios,tv,web"]

SEARCH_TERMS = ["стендап концерт", "сольный концерт", "stand up special", "спешл"]


def existing_video_ids() -> set[str]:
    ids = set()
    for m in CORPUS.glob("**/meta.json"):
        try:
            ids.add(json.loads(m.read_text())["video_id"])
        except Exception:
            pass
    return ids


def near_threshold_comics(lo=12000, hi=25000) -> list[str]:
    """Comics short of the 25k reliability threshold, richest-first: best ROI
    targets. Default floor 12k skips near-empty comics (1 short clip) whose
    chase is low value; raise lo to 18k for the tightest near-threshold set."""
    data = json.loads(REPORT.read_text())
    out = [(r["total_words"], r["artist"]) for r in data
           if lo <= r.get("total_words", 0) < hi]
    return [a for _, a in sorted(out, reverse=True)]


def search_comic(artist: str, per_term: int = 6) -> list[dict]:
    """ytsearch across a few query templates; return flat candidate dicts."""
    seen, out = set(), []
    for term in SEARCH_TERMS:
        q = f"ytsearch{per_term}:{artist} {term}"
        r = subprocess.run(
            YTDLP + ["--flat-playlist", "--skip-download",
                     "--print", "%(id)s\t%(duration)s\t%(channel)s\t%(title)s", q],
            capture_output=True, text=True,
        )
        for line in r.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            vid, dur, channel, title = parts[0], parts[1], parts[2], "\t".join(parts[3:])
            if vid in seen:
                continue
            seen.add(vid)
            try:
                dur = int(float(dur))
            except (ValueError, TypeError):
                dur = None
            out.append({"video_id": vid, "artist": artist, "title": title,
                        "channel": channel, "duration_sec": dur})
    return out


def cheap_prefilter(c: dict) -> str | None:
    """Reject reason from metadata alone (no download), or None to keep."""
    hard, _ = title_flag(c["title"])
    if hard:
        return hard
    d = c.get("duration_sec")
    if d is not None and d < MIN_DURATION_SEC:
        return f"too_short:{d // 60}m"
    if d is not None and d > 150 * 60:
        return f"too_long:{d // 60}m"  # likely a compilation
    return None


def load_candidates() -> dict:
    if CANDIDATES.exists():
        return json.loads(CANDIDATES.read_text())
    return {}


def save_candidates(cand: dict) -> None:
    """Atomic checkpoint write so a long run survives interruption."""
    tmp = CANDIDATES.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cand, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CANDIDATES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artist", action="append", default=[], help="repeatable")
    ap.add_argument("--targets", action="store_true",
                    help="use below-threshold comics (default 12k-25k words)")
    ap.add_argument("--min-words", type=int, default=12000,
                    help="floor for --targets (default 12000)")
    ap.add_argument("--max-words", type=int, default=25000)
    ap.add_argument("--per-term", type=int, default=6)
    ap.add_argument("--fetch", action="store_true",
                    help="download subs + attach monologue/conversation verdict")
    args = ap.parse_args()

    EXP.mkdir(exist_ok=True)
    artists = list(args.artist)
    if args.targets:
        artists += near_threshold_comics(args.min_words, args.max_words)
    if not artists:
        ap.error("give --artist or --targets")

    have = existing_video_ids()
    cand = load_candidates()
    new_found = 0

    for artist in artists:
        for c in search_comic(artist, args.per_term):
            vid = c["video_id"]
            if vid in have:
                continue  # already in corpus
            if vid in cand and cand[vid].get("artist") == artist:
                continue  # already a candidate for this comic
            reason = cheap_prefilter(c)
            c["prefilter"] = reason
            c["verdict"] = "reject" if reason else "pending"
            c["reasons"] = [reason] if reason else []
            c["markers_per_min"] = None
            cand[vid] = c
            new_found += 1
        print(f"  {artist}: total candidates now {sum(1 for v in cand.values() if v['artist']==artist)}", flush=True)
        save_candidates(cand)  # checkpoint after each comic's search

    if args.fetch:
        pending = [vid for vid, c in cand.items()
                   if c["verdict"] == "pending" and c["markers_per_min"] is None]
        for i, vid in enumerate(pending, 1):
            c = cand[vid]
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                vtt, info, source = fetch_subs(url)
            except RuntimeError as e:
                c["verdict"] = "reject"
                c["reasons"] = [str(e)]
            else:
                txt = vtt.read_text(encoding="utf-8", errors="ignore")
                dur = c.get("duration_sec") or info.get("duration")
                res = classify(txt, dur, c["title"])
                c.update({"verdict": res["verdict"], "markers_per_min": res["markers_per_min"],
                          "duration_sec": dur, "sub_source": source, "reasons": res["reasons"]})
                print(f"    [{i}/{len(pending)}] {res['verdict']:>6} {res['markers_per_min']}/min  "
                      f"{c['artist']} — {c['title'][:45]}", flush=True)
            if i % 10 == 0:
                save_candidates(cand)  # periodic checkpoint

    save_candidates(cand)
    from collections import Counter
    print(f"\n+{new_found} new candidates. total={len(cand)}  "
          f"verdicts={dict(Counter(v['verdict'] for v in cand.values()))}")
    print(f"written: {CANDIDATES}")


if __name__ == "__main__":
    main()
