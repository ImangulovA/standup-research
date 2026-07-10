"""Build docs/similar.html (kindred comics, 4 metrics) and docs/phrases.html
(signature word n-grams) from features.json. Self-contained, light neobrutalism,
matching docs/index.html. Only aggregates + short n-grams are embedded.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

CSS = r""":root{
  --bg:#FBFBF9; --ink:#1C293C; --paper:#ffffff;
  --primary:#FDC800; --secondary:#432DD7; --success:#16A34A; --warning:#D97706; --danger:#DC2626;
  --primary-soft:#FFF3C4; --secondary-soft:#E7E3FB; --danger-soft:#FBE3E3;
  --muted:#5b6678; --faint:#8a93a3;
  --font:'Inter',-apple-system,BlinkMacSystemFont,sans-serif; --mono:'JetBrains Mono',monospace;
  --bd:3px solid var(--ink); --bd2:2px solid var(--ink);
  --sh:5px 5px 0 var(--ink); --sh-sm:3px 3px 0 var(--ink); --sh-lg:8px 8px 0 var(--ink);
  --r:12px;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font-family:var(--font);
  background-image:radial-gradient(var(--secondary-soft) 1.4px,transparent 1.4px);background-size:26px 26px}
::selection{background:var(--primary);color:var(--ink)}
a{color:inherit}
@keyframes pop{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
.pop{opacity:0;animation:pop .5s cubic-bezier(.2,.8,.2,1) forwards}
.wrap{max-width:1040px;margin:0 auto;padding:22px 18px 90px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-bottom:30px}
.brand{font-weight:900;font-size:14px;letter-spacing:.02em;text-transform:uppercase}
.brand .s{color:var(--secondary)}
.chips{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.chip{display:inline-flex;align-items:center;gap:8px;padding:9px 15px;border:var(--bd2);border-radius:999px;
  font-weight:800;font-size:13px;text-decoration:none;box-shadow:var(--sh-sm);transition:transform .1s,box-shadow .1s}
.chip:hover{transform:translate(-2px,-2px);box-shadow:5px 5px 0 var(--ink)}
.chip:active{transform:translate(0,0);box-shadow:1px 1px 0 var(--ink)}
.chip.c1{background:var(--primary);color:var(--ink)}
.chip.nav{background:var(--secondary-soft);color:var(--ink)}
.chip .d{width:9px;height:9px;border-radius:50%;border:1.5px solid var(--ink)}
header h1{font-size:clamp(24px,4.2vw,40px);line-height:1.06;font-weight:900;letter-spacing:-.02em;margin:0 0 14px;max-width:900px}
header h1 mark{background:var(--primary);padding:0 8px;border:var(--bd2);border-radius:8px;box-shadow:var(--sh-sm)}
.sub{color:var(--muted);font-size:16px;line-height:1.55;max-width:780px;font-weight:500}
.sub b{color:var(--ink);background:var(--primary-soft);padding:0 5px;border-radius:5px}
.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:stretch;margin:26px 0 8px}
.search{flex:1;min-width:210px;padding:12px 15px;border:var(--bd2);border-radius:10px;background:var(--paper);
  font-family:var(--font);font-weight:600;font-size:15px;color:var(--ink);outline:none;box-shadow:var(--sh-sm)}
.search:focus{box-shadow:var(--sh)} .search::placeholder{color:var(--faint)}
.seg{display:inline-flex;border:var(--bd2);border-radius:10px;overflow:hidden;box-shadow:var(--sh-sm);flex-wrap:wrap}
.seg button{background:var(--paper);color:var(--muted);border:0;padding:10px 15px;font-family:var(--font);
  font-weight:800;font-size:13px;cursor:pointer;text-transform:uppercase;letter-spacing:.02em}
.seg button+button{border-left:var(--bd2)}
.seg button.on{background:var(--secondary);color:#fff}
.metricnote{color:var(--faint);font-size:13.5px;font-weight:600;margin:6px 2px 18px;min-height:18px}
.metricnote b{color:var(--secondary)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--paper);border:var(--bd);border-radius:var(--r);padding:16px 18px;box-shadow:var(--sh)}
.card h2{font-size:16px;font-weight:900;letter-spacing:-.01em;margin-bottom:3px;line-height:1.2}
.card h2 a{text-decoration:none}
.card h2 a:hover{border-bottom:2px solid var(--secondary)}
.card .meta{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--faint);margin-bottom:12px}
.badge{display:inline-block;font-family:var(--mono);font-size:10px;font-weight:700;padding:0 5px;
  border:1.5px solid var(--warning);border-radius:5px;color:var(--warning);margin-left:4px}
.kin{display:flex;flex-direction:column;gap:7px}
.kin a{display:flex;align-items:center;gap:9px;text-decoration:none;padding:6px 8px;border:var(--bd2);
  border-radius:9px;font-weight:700;font-size:14px;box-shadow:var(--sh-sm);transition:transform .1s,box-shadow .1s;background:var(--bg)}
.kin a:hover{transform:translate(-2px,-2px);box-shadow:var(--sh)}
.kin .rk{font-family:var(--mono);font-weight:800;color:#fff;background:var(--secondary);border:1.5px solid var(--ink);
  border-radius:6px;width:20px;height:20px;display:grid;place-items:center;font-size:11px;flex:0 0 auto}
.kin .nm{flex:1}
.kin .sim{font-family:var(--mono);font-size:11px;color:var(--muted);font-weight:700}
.kin a.pale .nm{color:var(--faint)}
.phr{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:12px}
.phr:last-child{margin-bottom:0}
.tag3{display:inline-flex;align-items:baseline;gap:6px;background:var(--primary);border:var(--bd2);border-radius:8px;
  padding:5px 10px;font-weight:800;font-size:14px;box-shadow:var(--sh-sm)}
.tag2{display:inline-flex;align-items:baseline;gap:5px;background:var(--secondary-soft);border:1.5px solid var(--ink);
  border-radius:7px;padding:3px 8px;font-weight:700;font-size:12.5px}
.tag3 .c,.tag2 .c{font-family:var(--mono);font-size:10px;font-weight:700;color:var(--muted)}
.lbl{font-size:10.5px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--faint);margin:2px 0 6px}
.empty{color:var(--faint);font-weight:700;padding:24px 4px;font-size:15px}
.method{background:var(--paper);border:var(--bd2);border-radius:var(--r);padding:20px 22px;box-shadow:var(--sh-sm);
  font-size:14px;line-height:1.6;color:var(--muted);font-weight:500;margin-top:30px}
.method b{color:var(--ink)} .method p{margin-bottom:9px} .method p:last-child{margin-bottom:0}
.method .dim{color:var(--faint);font-size:13px}
footer{margin-top:40px;border-top:var(--bd2);padding-top:20px;color:var(--muted);font-size:13px;line-height:1.8;font-weight:500}
footer a{color:var(--muted);font-weight:700}
footer a.f1{color:var(--ink);background:var(--primary);padding:1px 6px;border-radius:5px;border:1.5px solid var(--ink);text-decoration:none}
footer a.f2{color:#fff;background:var(--secondary);padding:1px 6px;border-radius:5px;border:1.5px solid var(--ink);text-decoration:none}"""

TOPBAR = """  <div class="topbar pop">
    <div class="brand">СТЕНДАП<span class="s">·</span>ЛЕКСИКОН</div>
    <div class="chips">
      <a class="chip nav" href="index.html">← Рейтинг</a>
      <a class="chip nav" href="{other_href}">{other_label}</a>
      <a class="chip c1" href="https://t.me/newezha" target="_blank" rel="noopener"><span class="d"></span>Невежда</a>
    </div>
  </div>"""

FOOTER = """  <footer class="pop">
    Проект каналов <a class="f1" href="https://t.me/newezha" target="_blank" rel="noopener">Невежда</a>
    и <a class="f2" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener">Шаппелл позвонит</a>.<br>
    Считаются только агрегаты и короткие n-граммы; полные тексты выступлений не публикуются.
  </footer>"""


def page(title, body):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
{body}
</div>
</body>
</html>"""


def build_similar(feat):
    m = feat["meta"]
    data = feat["similar"]
    topbar = TOPBAR.format(other_href="phrases.html", other_label="Фирменные обороты →")
    body = f"""{topbar}

  <header class="pop" style="animation-delay:.05s">
    <h1>Кто на кого <mark>похож</mark>: родственные комики</h1>
    <p class="sub">Для каждого комика — три самых близких по четырём независимым метрикам.
      Считаем только среди <b>{m['sim_pool']} комиков</b> с корпусом от {m['min_sim']:,} слов
      (иначе соседи случайны). Переключай способ похожести кнопками ниже.</p>
  </header>

  <div class="controls pop" style="animation-delay:.1s">
    <input type="search" id="q" class="search" placeholder="Найти комика…" autocomplete="off">
    <div class="seg" id="seg">
      <button data-m="lsa" class="on">Смысл</button>
      <button data-m="lex">Лексика</button>
      <button data-m="delta">Манера</button>
      <button data-m="ngram">Буквы</button>
    </div>
  </div>
  <div class="metricnote" id="mnote"></div>

  <div class="grid pop" id="grid" style="animation-delay:.14s"></div>

  <div class="method pop">
    <p><b>Смысл</b> (LSA): о чём комик шутит. tf-idf по леммам сворачивается в
      латентные темы (усечённое SVD), близость — косинус в этом пространстве.</p>
    <p><b>Лексика</b>: какими характерными словами комик выделяется. Косинус
      «стилевых отпечатков» — векторов weighted log-odds по нарицательным словам.</p>
    <p><b>Манера</b> (Cosine Delta, стилометрия Бёрроуза): как комик строит речь.
      z-нормированные частоты самых частых служебных слов.</p>
    <p><b>Буквы</b>: косинус профилей символьных 3-грамм (tf-idf). Тонкий
      фонетико-орфографический след; на одном языке значения близки у всех.</p>
    <p class="dim">Оценки разных способов не сравнимы между собой по величине —
      важен только порядок соседей внутри одного способа. Бледные — корпус меньше
      25 000 слов.</p>
  </div>

{FOOTER}

<script>
const DATA=__DATA__;
const NOTE={{
  lsa:'<b>Смысл</b>: о чём шутит — близость по темам (LSA над леммами).',
  lex:'<b>Лексика</b>: какими характерными словами выделяется (log-odds отпечаток).',
  delta:'<b>Манера</b>: как строит речь — Cosine Delta по служебным словам.',
  ngram:'<b>Буквы</b>: символьные 3-граммы; на одном языке все близки.'
}};
let metric='lsa';
function esc(s){{return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&quot;').replace(/"/g,'&quot;');}}
function render(){{
  document.getElementById('mnote').innerHTML=NOTE[metric];
  const f=(document.getElementById('q').value||'').trim().toLowerCase();
  const rows=DATA.filter(c=>!f||c.artist.toLowerCase().includes(f));
  const html=rows.map(c=>{{
    const kin=c['kindred_'+metric].map((k,i)=>{{
      const inner=`<span class="rk">${{i+1}}</span><span class="nm">${{esc(k.name)}}</span>`+
        `<span class="sim">${{k.sim.toFixed(3)}}</span>`;
      return k.url?`<a href="${{esc(k.url)}}" target="_blank" rel="noopener" class="${{k.reliable?'':'pale'}}">${{inner}}</a>`
                 :`<a class="${{k.reliable?'':'pale'}}">${{inner}}</a>`;
    }}).join('');
    const head=c.url?`<a href="${{esc(c.url)}}" target="_blank" rel="noopener">${{esc(c.artist)}}</a>`:esc(c.artist);
    const badge=c.reliable?'':'<span class="badge">&lt;25k</span>';
    return `<div class="card"><h2>${{head}}${{badge}}</h2>`+
      `<div class="meta">${{c.concerts}} выст. · ${{c.total_words.toLocaleString('ru-RU')}} слов</div>`+
      `<div class="kin">${{kin}}</div></div>`;
  }}).join('');
  document.getElementById('grid').innerHTML=html||'<div class="empty">Ничего не найдено.</div>';
}}
document.getElementById('seg').addEventListener('click',e=>{{
  const b=e.target.closest('button'); if(!b) return;
  document.querySelectorAll('#seg button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); metric=b.dataset.m; render();
}});
document.getElementById('q').addEventListener('input',render);
render();
</script>"""
    return page("Родственные комики — Стендап·Лексикон",
                body).replace("__DATA__", json.dumps(data, ensure_ascii=False))


def build_phrases(feat):
    m = feat["meta"]
    data = feat["phrases"]
    topbar = TOPBAR.format(other_href="similar.html", other_label="Родственные комики →")
    body = f"""{topbar}

  <header class="pop" style="animation-delay:.05s">
    <h1>Фирменные <mark>обороты</mark> комиков</h1>
    <p class="sub">Словосочетания, которыми комик выделяется на фоне всех остальных:
      триграммы и биграммы с самым высоким weighted log-odds против общего корпуса.
      Показаны для <b>{m['phr_pool']} комиков</b> с корпусом от {m['min_phr']:,} слов.
      Рядом с оборотом — сколько раз он встретился.</p>
  </header>

  <div class="controls pop" style="animation-delay:.1s">
    <input type="search" id="q" class="search" placeholder="Найти комика или оборот…" autocomplete="off">
  </div>

  <div class="grid pop" id="grid" style="animation-delay:.14s"></div>

  <div class="method pop">
    <p><b>Как считаем.</b> Для каждого комика берём все его словесные три- и биграммы
      (по одному разу на концерт) и сравниваем их долю с долей во всём корпусе через
      <b>weighted log-odds</b> с приором Дирихле (Monroe et al. 2008). Наверх всплывают
      обороты, характерные именно для него, а не общие для всех.</p>
    <p class="dim">Показываются только короткие n-граммы (2–3 слова) — как маркеры стиля;
      полные тексты выступлений не публикуются. Бледные — корпус меньше 25 000 слов.</p>
  </div>

{FOOTER}

<script>
const DATA=__DATA__;
function esc(s){{return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&quot;').replace(/"/g,'&quot;');}}
function render(){{
  const f=(document.getElementById('q').value||'').trim().toLowerCase();
  const rows=DATA.map(c=>{{
    if(!f) return c;
    if(c.artist.toLowerCase().includes(f)) return c;
    const tri=c.sig_tri.filter(p=>p.phrase.includes(f));
    const bi=c.sig_bi.filter(p=>p.phrase.includes(f));
    return (tri.length||bi.length)?{{...c,sig_tri:tri,sig_bi:bi}}:null;
  }}).filter(Boolean);
  const html=rows.map(c=>{{
    const head=c.url?`<a href="${{esc(c.url)}}" target="_blank" rel="noopener">${{esc(c.artist)}}</a>`:esc(c.artist);
    const badge=c.reliable?'':'<span class="badge">&lt;25k</span>';
    const tri=c.sig_tri.map(p=>`<span class="tag3">${{esc(p.phrase)}} <span class="c">${{p.count}}</span></span>`).join('');
    const bi=c.sig_bi.map(p=>`<span class="tag2">${{esc(p.phrase)}} <span class="c">${{p.count}}</span></span>`).join('');
    return `<div class="card"><h2>${{head}}${{badge}}</h2>`+
      `<div class="meta">${{c.concerts}} выст. · ${{c.total_words.toLocaleString('ru-RU')}} слов</div>`+
      (tri?`<div class="lbl">Триграммы</div><div class="phr">${{tri}}</div>`:'')+
      (bi?`<div class="lbl">Биграммы</div><div class="phr">${{bi}}</div>`:'')+
      `</div>`;
  }}).join('');
  document.getElementById('grid').innerHTML=html||'<div class="empty">Ничего не найдено.</div>';
}}
document.getElementById('q').addEventListener('input',render);
render();
</script>"""
    return page("Фирменные обороты — Стендап·Лексикон",
                body).replace("__DATA__", json.dumps(data, ensure_ascii=False))


def main():
    feat = json.loads((ROOT / "features.json").read_text(encoding="utf-8"))
    DOCS.mkdir(exist_ok=True)
    (DOCS / "similar.html").write_text(build_similar(feat), encoding="utf-8")
    (DOCS / "phrases.html").write_text(build_phrases(feat), encoding="utf-8")
    print(f"wrote {DOCS/'similar.html'} and {DOCS/'phrases.html'}")
    print(f"similar={len(feat['similar'])} phrases={len(feat['phrases'])}")


if __name__ == "__main__":
    main()
