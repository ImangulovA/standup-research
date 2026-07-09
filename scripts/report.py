"""Aggregate the corpus per artist and compute the Inozemtsev metric:
unique lemmas within the first 25 000 word-tokens of the artist's combined,
cleaned corpus.

Concerts are concatenated per artist (in filename order). Artists with a
combined corpus < 25 000 words are flagged as low-reliability ("pale circle").
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
WINDOW = 25000


def artist_rows():
    rows = []
    for artist_dir in sorted(CORPUS.iterdir()):
        if not artist_dir.is_dir():
            continue
        lemmas = []
        concerts = 0
        display = artist_dir.name
        url = None
        best_wc = -1
        for concert in sorted(artist_dir.iterdir()):
            lem_file = concert / "lemmas.txt"
            if not lem_file.exists():
                continue
            concerts += 1
            lemmas.extend(lem_file.read_text(encoding="utf-8").split())
            meta_file = concert / "meta.json"
            if meta_file.exists():
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
                display = meta.get("artist", display)
                # representative link: the concert with the most words
                wc = meta.get("word_count") or 0
                if meta.get("url") and wc > best_wc:
                    best_wc = wc
                    url = meta["url"]
        if not lemmas:
            continue
        total = len(lemmas)
        window = lemmas[:WINDOW]
        rows.append({
            "artist": display,
            "concerts": concerts,
            "total_words": total,
            "unique_lemmas_25k": len(set(window)),
            "reliable": total >= WINDOW,
            "url": url,
        })
    rows.sort(key=lambda r: r["unique_lemmas_25k"], reverse=True)
    return rows


def main():
    rows = artist_rows()
    if not rows:
        print("Corpus is empty. Run process.py on some videos first.")
        return
    (ROOT / "report.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    w = max(len(r["artist"]) for r in rows)
    print(f"{'artist':<{w}}  concerts  total_words  uniq_lemmas_25k  reliable")
    print("-" * (w + 45))
    for r in rows:
        flag = "" if r["reliable"] else "  (pale: <25k words)"
        print(f"{r['artist']:<{w}}  {r['concerts']:>8}  {r['total_words']:>11}  "
              f"{r['unique_lemmas_25k']:>15}  {str(r['reliable']):>8}{flag}")
    print(f"\nWritten: {ROOT / 'report.json'}")


if __name__ == "__main__":
    main()
