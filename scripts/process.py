"""Process ONE YouTube stand-up video into the corpus.

Usage:
  python process.py <youtube_url> --artist "Имя Комика" [--title "..."] [--year 2023]

Reusable functions (process_one, fetch_subs) are imported by batch.py.

Persistence: raw subtitles + metadata are saved PERMANENTLY under raw_subs/
keyed by video id, so re-runs never re-download and lemmatization can be
redone offline without touching YouTube.

Per-concert output in corpus/<artist_slug>/<video_slug>/:
    meta.json      (url, artist, title, year, video_id, word_count, unique_lemmas)
    transcript.txt (cleaned text)
    lemmas.txt     (space-separated lemma stream, word-tokens only)
    tokens.tsv     (token<TAB>lemma)
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from clean_vtt import clean_vtt
from lemmatize import lemmatize

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
RAW = ROOT / "raw_subs"
# player_client=android/ios/tv use YouTube's innertube API instead of the web
# page, which bypasses the "Sign in to confirm you're not a bot" wall that
# blocks mass web-client extraction.
YTDLP = [sys.executable, "-m", "yt_dlp",
         "--extractor-args", "youtube:player_client=android,ios,tv,web"]


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_")[:80] or "untitled"


def transliterate_slug(s: str) -> str:
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    out = "".join(table.get(ch, ch) for ch in s.lower())
    return slugify(out)


def _dump_info(url: str) -> dict:
    r = subprocess.run(
        YTDLP + ["--dump-single-json", "--skip-download", url],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp metadata failed: {r.stderr.strip()[-500:]}")
    return json.loads(r.stdout)


# Russian caption tracks we accept, best first. We deliberately EXCLUDE
# auto-translated tracks like "ru-en" (Russian from English), which are
# lower quality than the original ASR.
_RU_PREF = ["ru", "ru-orig", "ru-RU"]


def _track_cyr_ratio(p: Path) -> tuple[float, int]:
    """Cleaned-text Cyrillic ratio and length for a cached .vtt.
    Used to detect tracks that are actually English despite a ru* label."""
    txt = clean_vtt(p.read_text(encoding="utf-8"))
    letters = [c for c in txt if c.isalpha()]
    if not letters:
        return 0.0, len(txt)
    cyr = sum(1 for c in letters if ("а" <= c.lower() <= "я") or c.lower() == "ё")
    return cyr / len(letters), len(txt)


def _pick_vtt(vid: str) -> Path | None:
    """Choose the best cached ru .vtt for a video by ACTUAL Russian content,
    not just the language label: some uploaders put English subs under the
    'ru' code. Pick the Cyrillic-dominant track, preferring original ASR."""
    cached = sorted(RAW.glob(f"{vid}*.vtt"))
    if not cached:
        return None
    # drop obvious foreign auto-translations by name (ru-en, ru-de, ru-ru...)
    cands = [p for p in cached
             if not re.search(r"\.ru-(?!orig\b|RU\b)[a-z]{2}\.vtt$", p.name)] or cached
    scored = []
    for p in cands:
        m = re.search(r"\.([\w-]+)\.vtt$", p.name)
        lang = m.group(1) if m else ""
        pref = _RU_PREF.index(lang) if lang in _RU_PREF else 99
        ratio, length = _track_cyr_ratio(p)
        # sort key (all descending): is-Russian, cyr ratio, preference, length
        scored.append(((ratio >= 0.5), round(ratio, 2), -pref, length, p))
    scored.sort(key=lambda x: x[:4], reverse=True)
    return scored[0][4]


def fetch_subs(url: str) -> tuple[Path, dict, str]:
    """Download ru subs + metadata into RAW/ (permanent, cached). Returns
    (vtt_path, info_dict, source) where source is 'manual' or 'auto'.
    Reuses cached files when present. Prefers manual subs, then original
    Russian auto-captions; excludes auto-translated tracks."""
    RAW.mkdir(exist_ok=True)
    info = _dump_info(url)
    vid = info.get("id", "video")
    (RAW / f"{vid}.info.json").write_text(
        json.dumps(info, ensure_ascii=False), encoding="utf-8"
    )

    manual_langs = [k for k in info.get("subtitles", {}) if k.startswith("ru")]
    auto_langs = [k for k in info.get("automatic_captions", {})
                  if k in ("ru", "ru-orig", "ru-RU")]
    source = "manual" if manual_langs else ("auto" if auto_langs else None)
    if source is None:
        raise RuntimeError("no_ru_subs")

    if not sorted(RAW.glob(f"{vid}*.vtt")):
        base = ["--skip-download", "--sub-format", "vtt/best",
                "--retries", "3", "--sleep-requests", "1",
                "-o", str(RAW / f"{vid}.%(ext)s"), url]
        if source == "manual":
            cmd = YTDLP + ["--write-subs", "--sub-langs", ",".join(manual_langs)] + base
        else:
            cmd = YTDLP + ["--write-auto-subs", "--sub-langs", "ru-orig,ru"] + base
        subprocess.run(cmd, capture_output=True, text=True)

    vtt = _pick_vtt(vid)
    if vtt is None:
        raise RuntimeError("no_ru_subs")
    return vtt, info, source


def video_id_from_url(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
    return m.group(1) if m else None


def _existing_meta(vid: str) -> dict | None:
    for p in CORPUS.glob(f"**/*_{vid}"):
        if (p / "meta.json").exists():
            return json.loads((p / "meta.json").read_text(encoding="utf-8"))
    return None


def process_one(url: str, artist: str, title: str | None = None,
                year: str | None = None, skip_existing: bool = True) -> dict:
    """Fetch, clean, lemmatize, write one concert. Returns a result dict."""
    # Fast offline skip BEFORE any network call: derive id from the URL.
    if skip_existing:
        pre_id = video_id_from_url(url)
        if pre_id:
            m = _existing_meta(pre_id)
            if m:
                m["status"] = "skipped_existing"
                return m

    vtt, info, source = fetch_subs(url)
    vid = info.get("id", "video")
    title = title or info.get("title") or vtt.stem
    year = year or (str(info.get("upload_date", ""))[:4] or None)

    artist_slug = transliterate_slug(artist)
    vslug = f"{transliterate_slug(title)}_{vid}"
    dest = CORPUS / artist_slug / vslug

    # Dedup by video_id: a concert is unique by its YouTube id regardless of
    # how the title is spelled. Reuse any existing folder ending with _<vid>.
    if skip_existing:
        existing = [p for p in CORPUS.glob(f"**/*_{vid}") if (p / "meta.json").exists()]
        if existing:
            meta = json.loads((existing[0] / "meta.json").read_text(encoding="utf-8"))
            meta["status"] = "skipped_existing"
            return meta

    text = clean_vtt(vtt.read_text(encoding="utf-8"))
    lemmas, pairs = lemmatize(text)

    dest.mkdir(parents=True, exist_ok=True)
    (dest / "transcript.txt").write_text(text, encoding="utf-8")
    (dest / "lemmas.txt").write_text(" ".join(lemmas), encoding="utf-8")
    with (dest / "tokens.tsv").open("w", encoding="utf-8") as f:
        f.write("token\tlemma\n")
        for tok, lm in pairs:
            f.write(f"{tok}\t{lm}\n")

    meta = {
        "artist": artist,
        "title": title,
        "year": year,
        "url": url,
        "video_id": vid,
        "duration_sec": info.get("duration"),
        "sub_source": source,
        "sub_track": vtt.name.split(".")[-2] if "." in vtt.name else None,
        "word_count": len(lemmas),
        "unique_lemmas": len(set(lemmas)),
        "status": "ok",
    }
    (dest / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--artist", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--year", default=None)
    args = ap.parse_args()
    m = process_one(args.url, args.artist, args.title, args.year)
    print(f"{m['status'].upper()}  {m['artist']} :: {m['title']}")
    print(f"    words: {m.get('word_count')}  unique lemmas: {m.get('unique_lemmas')}  "
          f"subs: {m.get('sub_source')}")


if __name__ == "__main__":
    main()
