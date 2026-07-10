#!/usr/bin/env python3
"""Heavy "features" over the stand-up corpus -> features.json (safe to publish).

Ported from the sister project chgk_vocab (similarity.py + phrases.py), adapted
to the stand-up corpus layout (corpus/<slug>/<concert>/tokens.tsv|meta.json).

Similarity — top-3 kindred comics by four independent methods:
  kindred_lex   — lexicon: cosine of weighted log-odds style fingerprints
                  (content lemmas the comic stands out on; proper nouns dropped) →
                  "uses the same distinctive words", not "both talk a lot"
  kindred_delta — manner: Burrows/Eder Cosine Delta over the most frequent
                  (function) words → stylometric "writes in the same style"
  kindred_ngram — letters: cosine of tf-idf character-3-gram profiles
  kindred_lsa   — meaning: cosine in a latent-topic space (truncated SVD / LSA
                  over tf-idf of content lemmas) → "talks about the same things"

Similarity is computed over comics with a large-enough corpus (>= MIN_SIM words),
so neighbours are meaningful. Only aggregates are written; full transcripts are
never emitted.
"""
import json
import math
import collections
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"

# ---- knobs -----------------------------------------------------------------
A0 = 500.0            # Dirichlet prior strength for weighted log-odds
MFW_N = 200           # function words for Cosine Delta
NGRAM_TOP = 1500      # character 3-grams kept
LSA_K = 60            # latent topic dimensions (<= pool size)
TOPK = 3              # neighbours per metric
MIN_SIM = 15000       # min corpus (words) to take part in similarity

# Russian function / stop words + a few stand-up fillers.
STOP = set("""и в во не что он на я с со как а то все всё она так его но да ты к у же вы за бы
по только ее её мне было вот от меня еще ещё нет о из ему теперь когда даже ну вдруг ли если уже или
ни быть был него до вас нибудь опять уж вам ведь там потом себя ничего ей может они тут где есть
надо ней для мы тебя их чем была сам чтоб без будто чего раз тоже себе под будет ж кто этот того
потому этого какой совсем ним здесь этом один почти мой тем чтобы нее сейчас были куда зачем всех
никогда можно при наконец два об другой хоть после над больше тот через эти нас про всего них какая
много разве три эту моя впрочем свою этой перед иногда лучше чуть том нельзя такой им более всегда
конечно всю между это свой которых который которые также этих весь эта наш свои мочь стать самый этими
как-то вообще просто типа блин короче тебе нам ним""".split())

import pymorphy3
_morph = pymorphy3.MorphAnalyzer()
_kind = {}


def kind(lm):
    """Proper-noun class per pymorphy: surn/name/geo/org, else none."""
    k = _kind.get(lm)
    if k is None:
        t = _morph.parse(lm)[0].tag
        k = ("surn" if "Surn" in t else "name" if "Name" in t
             else "geo" if "Geox" in t else "org" if "Orgn" in t else "none")
        _kind[lm] = k
    return k


def collect(display):
    """Aggregate per-comic counters by walking the corpus once."""
    forms = collections.defaultdict(collections.Counter)   # surface forms (delta)
    grams = collections.defaultdict(collections.Counter)   # char 3-grams
    lemc = collections.defaultdict(collections.Counter)    # content lemmas (fp/lsa)

    for artist_dir in sorted(CORPUS.iterdir()):
        if not artist_dir.is_dir():
            continue
        for concert in sorted(artist_dir.iterdir()):
            tsv = concert / "tokens.tsv"
            meta_f = concert / "meta.json"
            if not tsv.exists() or not meta_f.exists():
                continue
            nm = json.loads(meta_f.read_text(encoding="utf-8")).get("artist")
            if nm not in display:
                continue

            toks, lems = [], []
            for line in tsv.read_text(encoding="utf-8").splitlines():
                parts = line.split("\t")
                if len(parts) != 2:
                    continue
                tok, lem = parts[0].strip().lower(), parts[1].strip().lower()
                if tok == "token" or not tok:
                    continue
                toks.append(tok)
                lems.append(lem)

            forms[nm].update(toks)
            for w in toks:                       # char 3-grams with word boundaries
                s = "_" + w + "_"
                for i in range(len(s) - 2):
                    grams[nm][s[i:i + 3]] += 1
            lemc[nm].update(l for l in lems if l not in STOP and len(l) > 2)

    return forms, grams, lemc


def topk(pool, urls, rel, S, i):
    out = []
    for j in np.argsort(-S[i]):
        if j == i:
            continue
        out.append({"name": pool[j], "url": urls[j],
                    "reliable": rel[j], "sim": round(float(S[i, j]), 3)})
        if len(out) == TOPK:
            break
    return out


def logodds(cnt_i, G, N, n_i, min_i):
    """Weighted log-odds with Dirichlet prior (Monroe et al. 2008)."""
    out = []
    for w, yi in cnt_i.items():
        if yi < min_i:
            continue
        gw = G.get(w, yi)
        yj = max(gw - yi, 0)
        aw = A0 * gw / N
        nj = N - n_i
        if n_i + A0 - yi - aw <= 0 or nj + A0 - yj - aw <= 0:
            continue
        delta = (math.log((yi + aw) / (n_i + A0 - yi - aw))
                 - math.log((yj + aw) / (nj + A0 - yj - aw)))
        var = 1.0 / (yi + aw) + 1.0 / (yj + aw)
        out.append((w, delta / math.sqrt(var), yi))
    out.sort(key=lambda x: -x[1])
    return out


def main():
    report = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    disp = {r["artist"]: r for r in report}

    forms, grams, lemc = collect(disp)

    # global lemma counts + document frequency (background = all comics)
    G = collections.Counter()
    author_df = collections.Counter()
    for c in lemc.values():
        G.update(c)
        author_df.update(set(c))
    Nlem = sum(G.values())

    # similarity pool: comics with enough text for stable stylometry
    pool = sorted((nm for nm in disp if disp[nm]["total_words"] >= MIN_SIM),
                  key=lambda nm: -disp[nm]["unique_lemmas_25k"])
    n = len(pool)
    urls = [disp[nm].get("url") for nm in pool]
    rel = [disp[nm]["reliable"] for nm in pool]
    print(f"comics={len(disp)}  similarity pool={n} (>= {MIN_SIM} words)", flush=True)

    # ---------- (1) lexicon: log-odds style fingerprint cosine ----------
    def fingerprint(nm):
        c = lemc.get(nm, collections.Counter())
        n_i = sum(c.values()) or 1
        v = {}
        for w, z, yi in logodds(c, G, Nlem, n_i, min_i=3):
            if z <= 1.0:
                break
            if kind(w) != "none" or author_df[w] < 2:
                continue
            v[w] = z
            if len(v) >= 120:
                break
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return v, norm

    FP = {nm: fingerprint(nm) for nm in pool}
    S_lex = np.zeros((n, n))
    for a in range(n):
        vi, ni = FP[pool[a]]
        for b in range(a + 1, n):
            vj, nj = FP[pool[b]]
            small, big = (vi, vj) if len(vi) < len(vj) else (vj, vi)
            dot = sum(val * big.get(w, 0.0) for w, val in small.items())
            s = dot / (ni * nj) if dot > 0 else 0.0
            S_lex[a, b] = S_lex[b, a] = s
    print("lexicon done", flush=True)

    # ---------- (2) manner: Cosine Delta over most-frequent words ----------
    gform = collections.Counter()
    for nm in pool:
        gform.update(forms[nm])
    mfw = [w for w, _ in gform.most_common(MFW_N)]
    M = np.zeros((n, len(mfw)))
    for a in range(n):
        tot = sum(forms[pool[a]].values()) or 1
        for j, w in enumerate(mfw):
            M[a, j] = forms[pool[a]][w] / tot
    Z = (M - M.mean(0)) / (M.std(0) + 1e-9)
    Zn = Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-9)
    S_delta = Zn @ Zn.T
    print("delta done", flush=True)

    # ---------- (3) letters: tf-idf character 3-gram cosine ----------
    ggram = collections.Counter()
    for nm in pool:
        ggram.update(grams[nm])
    topg = [g for g, _ in ggram.most_common(NGRAM_TOP)]
    gi = {g: j for j, g in enumerate(topg)}
    Gm = np.zeros((n, len(topg)))
    for a in range(n):
        tot = sum(grams[pool[a]].values()) or 1
        for g, cnt in grams[pool[a]].items():
            j = gi.get(g)
            if j is not None:
                Gm[a, j] = cnt / tot
    idf = np.log((n + 1) / ((Gm > 0).sum(0) + 1)) + 1
    Gn = Gm * idf
    Gn = Gn / (np.linalg.norm(Gn, axis=1, keepdims=True) + 1e-9)
    S_ngram = Gn @ Gn.T
    print("ngram done", flush=True)

    # ---------- (4) meaning: LSA (tf-idf of content lemmas -> truncated SVD) ----------
    vocab = [w for w, c in G.items()
             if c >= 5 and author_df[w] >= 3 and len(w) > 2]
    vi = {w: j for j, w in enumerate(vocab)}
    df = np.array([author_df[w] for w in vocab])
    lidf = np.log((n + 1) / (df + 1)) + 1
    T = np.zeros((n, len(vocab)))
    for a in range(n):
        tot = sum(lemc[pool[a]].values()) or 1
        for w, cnt in lemc[pool[a]].items():
            j = vi.get(w)
            if j is not None:
                T[a, j] = cnt / tot
    T = T * lidf
    T = T / (np.linalg.norm(T, axis=1, keepdims=True) + 1e-9)
    U, sig_, Vt = np.linalg.svd(T, full_matrices=False)
    k = min(LSA_K, U.shape[1])
    L = U[:, :k] * sig_[:k]                       # comic vectors in topic space
    Ln = L / (np.linalg.norm(L, axis=1, keepdims=True) + 1e-9)
    S_lsa = Ln @ Ln.T
    print(f"lsa done (dims={k}, vocab={len(vocab)})", flush=True)

    # ---------- assemble ----------
    similar = []
    for a, nm in enumerate(pool):
        r = disp[nm]
        similar.append({
            "artist": nm, "url": r.get("url"), "reliable": r["reliable"],
            "concerts": r["concerts"], "total_words": r["total_words"],
            "kindred_lex": topk(pool, urls, rel, S_lex, a),
            "kindred_delta": topk(pool, urls, rel, S_delta, a),
            "kindred_ngram": topk(pool, urls, rel, S_ngram, a),
            "kindred_lsa": topk(pool, urls, rel, S_lsa, a),
        })

    out = {
        "meta": {"comics": len(disp), "sim_pool": n, "min_sim": MIN_SIM,
                 "mfw": MFW_N, "lsa_dim": k, "ngram_top": NGRAM_TOP},
        "similar": similar,
    }
    (ROOT / "features.json").write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {ROOT / 'features.json'}  (sim={n})")

    # spot check
    ex = next((c for c in similar if c["artist"] == "Иван Абрамов"), similar[0])
    print("example:", ex["artist"])
    for m in ("kindred_lex", "kindred_delta", "kindred_ngram", "kindred_lsa"):
        print(f"  {m:14}:", [x["name"] for x in ex[m]])


if __name__ == "__main__":
    main()
