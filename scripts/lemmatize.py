"""Lemmatize cleaned Russian text: razdel (tokenize) + pymorphy3 (lemma).

Matches Inozemtsev methodology. Produces:
  - lemma stream (space-separated lemmas, word-tokens only) -> lemmas.txt
  - token/lemma pairs                                       -> tokens.tsv
"""
import re
from razdel import tokenize
import pymorphy3

_MORPH = pymorphy3.MorphAnalyzer()
# Russian-only research: a token counts as a "word" ONLY if it contains
# Cyrillic letters. Pure Latin/English tokens are dropped from the corpus.
_WORD_RE = re.compile(r"[а-яёА-ЯЁ]")
_lemma_cache: dict[str, str] = {}


def lemma(token: str) -> str:
    key = token.lower()
    hit = _lemma_cache.get(key)
    if hit is None:
        hit = _MORPH.parse(key)[0].normal_form
        _lemma_cache[key] = hit
    return hit


def is_word(token: str) -> bool:
    return bool(_WORD_RE.search(token))


def lemmatize(text: str):
    """Return (lemmas, pairs). lemmas = word-token lemma stream;
    pairs = list of (token, lemma) for word tokens only."""
    lemmas = []
    pairs = []
    for sub in tokenize(text):
        tok = sub.text
        if not is_word(tok):
            continue
        lm = lemma(tok)
        lemmas.append(lm)
        pairs.append((tok, lm))
    return lemmas, pairs
