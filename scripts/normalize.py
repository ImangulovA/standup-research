"""Normalize the whole corpus for the Russian-only research:

  1. Re-pick the best ORIGINAL Russian cached track per concert (never a
     translated ru-XX track).
  2. Rebuild transcript.txt from that track.
  3. Re-lemmatize in Cyrillic-only mode (Latin/English tokens dropped).
  4. Update meta.json with sub_track, cyr_ratio, word_count, unique_lemmas.
  5. Flag concerts that are English-heavy or only have a translated track
     (candidates for re-download / removal).

Offline: uses cached .vtt files in raw_subs/. No network.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from process import CORPUS, _pick_vtt
from clean_vtt import clean_vtt
from lemmatize import lemmatize


def cyr_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    cyr = sum(1 for c in letters if ("а" <= c.lower() <= "я") or c.lower() == "ё")
    return round(cyr / len(letters), 3)


def is_translated(track: str) -> bool:
    return bool(re.fullmatch(r"ru-(?!orig|RU$)[a-z]{2}", track))


def main():
    count = 0
    flagged = []
    for meta_path in sorted(CORPUS.glob("**/meta.json")):
        d = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        vid = meta.get("video_id")
        vtt = _pick_vtt(vid) if vid else None
        if vtt is None:
            flagged.append((0.0, "NO_CACHE", meta.get("artist"), meta.get("title"), vid))
            continue

        text = clean_vtt(vtt.read_text(encoding="utf-8"))
        lemmas, pairs = lemmatize(text)
        track = vtt.name.split(".")[-2]
        r = cyr_ratio(text)

        (d / "transcript.txt").write_text(text, encoding="utf-8")
        (d / "lemmas.txt").write_text(" ".join(lemmas), encoding="utf-8")
        with (d / "tokens.tsv").open("w", encoding="utf-8") as f:
            f.write("token\tlemma\n")
            for t, l in pairs:
                f.write(f"{t}\t{l}\n")

        meta["sub_track"] = track
        meta["cyr_ratio"] = r
        meta["word_count"] = len(lemmas)
        meta["unique_lemmas"] = len(set(lemmas))
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        count += 1

        if r < 0.5 or is_translated(track):
            flagged.append((r, track, meta.get("artist"), meta.get("title"), vid))

    print(f"re-lemmatized {count} concerts (Cyrillic-only, original ru track)")
    print(f"FLAGGED (English-heavy / translated / no-cache): {len(flagged)}")
    for r, tr, a, t, v in sorted(flagged):
        print(f"  cyr={r} track={tr}  {a} — {t}  [{v}]")


if __name__ == "__main__":
    main()
