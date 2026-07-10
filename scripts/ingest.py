"""Ingest the concerts you APPROVED on the review page into the corpus.

Input: expansion/approved.json - the list exported from review.html, e.g.
    [{"video_id": "...", "artist": "Иван Абрамов", "title": "..."}, ...]

For each entry it runs the normal pipeline (fetch cached subs -> clean ->
lemmatize -> corpus), re-classifies as a final safety gate (skips anything the
detector now rejects), then reminds you to rebuild the report + infographic.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from classify import classify_video_id
from process import process_one

ROOT = Path(__file__).resolve().parent.parent
APPROVED = ROOT / "expansion" / "approved.json"
REVIEWED = ROOT / "expansion" / "reviewed.json"


def mark_reviewed(video_ids: list[str]) -> None:
    """Add ids to reviewed.json so they never reappear on the review page."""
    seen = set(json.loads(REVIEWED.read_text())) if REVIEWED.exists() else set()
    seen.update(video_ids)
    REVIEWED.write_text(json.dumps(sorted(seen), ensure_ascii=False, indent=2),
                        encoding="utf-8")


def main():
    if not APPROVED.exists():
        sys.exit(f"missing {APPROVED} - export it from review.html first")
    items = json.loads(APPROVED.read_text())
    mark_reviewed([it["video_id"] for it in items])
    ok = skipped = rejected = 0
    for it in items:
        vid, artist = it["video_id"], it["artist"]
        url = f"https://www.youtube.com/watch?v={vid}"
        try:
            meta = process_one(url, artist, it.get("title"))
        except RuntimeError as e:
            print(f"  SKIP {artist} — {vid}: {e}")
            skipped += 1
            continue
        # Final safety gate: re-check the ingested track.
        res = classify_video_id(vid, meta.get("duration_sec"), meta.get("title") or "")
        if res and res["verdict"] == "reject":
            print(f"  REJECT (gate) {artist} — {meta.get('title')}: {res['reasons']}")
            rejected += 1
            continue
        tag = meta["status"]
        print(f"  {tag.upper():15} {artist} — {meta.get('title','')[:45]} "
              f"({meta.get('word_count','?')}w)")
        ok += 1
    print(f"\ningested={ok} skipped={skipped} rejected={rejected}")
    print("next: ./.venv/bin/python scripts/report.py && "
          "./.venv/bin/python scripts/build_infographic.py")


if __name__ == "__main__":
    main()
