"""Convert a YouTube .vtt subtitle file into clean plain text.

Handles YouTube auto-generated captions, which repeat each line across
consecutive cues and carry inline timing tags like <00:00:01.234><c>word</c>.
Strategy: strip tags/timestamps, then drop exact duplicate lines (per
Inozemtsev methodology: "точные повторы строк удаляются").
"""
import re
import sys

TAG_RE = re.compile(r"<[^>]+>")            # inline <...> tags
TS_RE = re.compile(r"^\d\d:\d\d:\d\d")     # cue timestamp lines
CTRL_RE = re.compile(r"\s+")


def clean_vtt(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line or TS_RE.match(line):
            continue
        if line.isdigit():  # cue index
            continue
        line = TAG_RE.sub("", line)
        line = line.replace("&nbsp;", " ").replace("&amp;", "&")
        line = CTRL_RE.sub(" ", line).strip()
        if line:
            lines.append(line)

    # Drop consecutive duplicates (auto-sub rolling repeats)
    deduped = []
    prev = None
    for line in lines:
        if line != prev:
            deduped.append(line)
        prev = line

    # Drop remaining EXACT duplicate lines globally (methodology)
    seen = set()
    final = []
    for line in deduped:
        key = line.lower()
        if key not in seen:
            seen.add(key)
            final.append(line)
    return "\n".join(final)


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        print(clean_vtt(f.read()))
