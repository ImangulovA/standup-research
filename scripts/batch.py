"""Process a SHARD of the smeshno catalog into the corpus.

Used by the agent swarm: each agent runs one shard.

Usage:
  python batch.py --shard <i> --nshards <K>   # process rows where index % K == i

Idempotent: already-processed concerts are skipped. Raw subtitles are cached
in raw_subs/, so re-runs never re-download. Writes a per-shard log to
logs/shard_<i>_of_<K>.json with a status for every assigned row.
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from process import process_one, ROOT

SOURCES = ROOT / "sources_smeshno.json"
LOGDIR = ROOT / "logs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--nshards", type=int, required=True)
    args = ap.parse_args()

    rows = json.loads(SOURCES.read_text(encoding="utf-8"))
    mine = [(i, r) for i, r in enumerate(rows) if i % args.nshards == args.shard]

    LOGDIR.mkdir(exist_ok=True)
    logpath = LOGDIR / f"shard_{args.shard}_of_{args.nshards}.json"

    results = []
    for n, (idx, r) in enumerate(mine, 1):
        entry = {"idx": idx, "comic": r["comic"], "title": r["title"], "url": r["url"]}
        try:
            m = process_one(r["url"], r["comic"], title=r["title"], year=r.get("year"))
            entry["status"] = m.get("status", "ok")
            entry["word_count"] = m.get("word_count")
            entry["unique_lemmas"] = m.get("unique_lemmas")
            entry["sub_source"] = m.get("sub_source")
        except Exception as e:  # noqa: BLE001
            msg = str(e)
            entry["status"] = "no_subs" if msg == "no_ru_subs" else "error"
            entry["error"] = msg[:300]
            if entry["status"] == "error":
                entry["trace"] = traceback.format_exc()[-600:]
        results.append(entry)
        print(f"[{args.shard}/{args.nshards}] {n}/{len(mine)} "
              f"{entry['status']:<16} {r['comic']} — {r['title']}", flush=True)
        # persist log after each item (resumable / observable)
        logpath.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for e in results if e["status"] in ("ok", "skipped_existing"))
    nosubs = sum(1 for e in results if e["status"] == "no_subs")
    err = sum(1 for e in results if e["status"] == "error")
    print(f"[shard {args.shard}] DONE  ok={ok} no_subs={nosubs} error={err} total={len(results)}",
          flush=True)


if __name__ == "__main__":
    main()
