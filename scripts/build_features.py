"""Build docs/similar.html (kindred comics, 4 metrics) and docs/method.html
(the maths behind the similarity) from features.json. Self-contained, light
neobrutalism, matching docs/index.html. Only aggregates are embedded.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO = "https://github.com/ImangulovA/standup-research"

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
.chip.c2{background:var(--secondary);color:#fff}
.chip.nav{background:var(--secondary-soft);color:var(--ink)}
.chip .d{width:9px;height:9px;border-radius:50%;border:1.5px solid var(--ink)}
.chip.c2 .d{border-color:#fff}
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
.empty{color:var(--faint);font-weight:700;padding:24px 4px;font-size:15px}
.msec{display:flex;align-items:center;gap:12px;margin:34px 0 14px;font-weight:900;font-size:13px;
  text-transform:uppercase;letter-spacing:.08em}
.msec .tag{font-family:var(--mono);background:var(--ink);color:var(--bg);padding:3px 9px;border-radius:6px;font-size:12px}
.msec::after{content:'';flex:1;height:3px;background:var(--ink);border-radius:3px}
.prose{background:var(--paper);border:var(--bd2);border-radius:var(--r);padding:20px 22px;box-shadow:var(--sh-sm);
  font-size:15px;line-height:1.65;color:var(--ink);font-weight:500}
.prose p{margin-bottom:11px} .prose p:last-child{margin-bottom:0}
.prose b{font-weight:800} .prose .dim{color:var(--muted);font-size:13.5px}
.prose code{font-family:var(--mono);font-size:13px;background:var(--secondary-soft);padding:1px 5px;border-radius:5px}
.fbox{background:var(--bg);border:var(--bd2);border-radius:10px;padding:6px 14px;margin:12px 0;overflow-x:auto;box-shadow:var(--sh-sm)}
.gh{display:flex;flex-wrap:wrap;gap:12px;margin-top:6px}
.gh a{display:inline-flex;align-items:center;gap:8px;background:var(--ink);color:var(--bg);text-decoration:none;
  font-weight:800;font-size:14px;padding:11px 16px;border:var(--bd2);border-radius:10px;box-shadow:var(--sh-sm);
  font-family:var(--mono);transition:transform .1s,box-shadow .1s}
.gh a:hover{transform:translate(-2px,-2px);box-shadow:var(--sh)}
.refs{list-style:none;font-size:13.5px;line-height:1.6;color:var(--muted);font-weight:500}
.refs li{padding:5px 0;border-top:2px solid #eceae4} .refs li:first-child{border-top:0}
footer{margin-top:40px;border-top:var(--bd2);padding-top:20px;color:var(--muted);font-size:13px;line-height:1.8;font-weight:500}
footer a{color:var(--muted);font-weight:700}
footer a.f1{color:var(--ink);background:var(--primary);padding:1px 6px;border-radius:5px;border:1.5px solid var(--ink);text-decoration:none}
footer a.f2{color:#fff;background:var(--secondary);padding:1px 6px;border-radius:5px;border:1.5px solid var(--ink);text-decoration:none}"""

FOOTER = """  <footer class="pop">
    Проект каналов <a class="f1" href="https://t.me/newezha" target="_blank" rel="noopener">Невежда</a>
    и <a class="f2" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener">Шаппелл позвонит</a>.<br>
    Считаются только агрегаты; полные тексты выступлений не публикуются.
  </footer>"""


def page(title, body, head_extra=""):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
{head_extra}
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
    body = f"""  <div class="topbar pop">
    <div class="brand">СТЕНДАП<span class="s">·</span>ЛЕКСИКОН</div>
    <div class="chips">
      <a class="chip nav" href="index.html">← Рейтинг</a>
      <a class="chip nav" href="method.html">Как мы это считаем →</a>
      <a class="chip c1" href="https://t.me/newezha" target="_blank" rel="noopener"><span class="d"></span>Невежда</a>
      <a class="chip c2" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener"><span class="d"></span>Шаппелл позвонит</a>
    </div>
  </div>

  <header class="pop" style="animation-delay:.05s">
    <h1>Кто на кого <mark>похож</mark>: родственные комики</h1>
    <p class="sub">Для каждого комика — три самых близких по четырём независимым метрикам.
      Считаем только среди <b>{m['sim_pool']} комиков</b> с корпусом от {m['min_sim']:,} слов
      (иначе соседи случайны). Переключай способ похожести кнопками ниже, а
      <a href="method.html" style="color:var(--secondary);font-weight:800">как это устроено — на отдельной странице</a>.</p>
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
function esc(s){{return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}}
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


MATHJAX = r"""<script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['$$','$$']]},chtml:{scale:1.0}};</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>"""


def build_method(feat):
    m = feat["meta"]
    body = r"""  <div class="topbar pop">
    <div class="brand">СТЕНДАП<span class="s">·</span>ЛЕКСИКОН</div>
    <div class="chips">
      <a class="chip nav" href="similar.html">← Похожие комики</a>
      <a class="chip nav" href="index.html">Рейтинг</a>
      <a class="chip c1" href="https://t.me/newezha" target="_blank" rel="noopener"><span class="d"></span>Невежда</a>
      <a class="chip c2" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener"><span class="d"></span>Шаппелл позвонит</a>
    </div>
  </div>

  <header class="pop" style="animation-delay:.05s">
    <h1>Как мы считаем <mark>похожесть</mark></h1>
    <p class="sub">Близость двух комиков мы меряем <b>четырьмя независимыми способами</b>: по темам,
      по характерным словам, по манере речи и по буквосочетаниям. Каждый ловит свою ось сходства,
      поэтому и соседи у них разные. Ниже — вся математика и ссылки на код.</p>
  </header>

  <h2 class="msec pop"><span class="tag">00</span>Данные и подготовка</h2>
  <div class="prose pop">
    <p>Корпус комика — склеенные очищенные субтитры всех его концертов. Оставляем только
      <b>кириллические</b> токены (в нижнем регистре), лемматизируем через <code>pymorphy3</code>.
      В расчёт похожести берём только комиков с корпусом <b>от %MINSIM% слов</b> (%POOL% комиков):
      на меньшем объёме оценки частот слишком шумные и соседи получаются случайными.</p>
    <p>Три из четырёх метрик — это <b>косинусная близость</b> векторов. Для векторов
      \(\mathbf{a}\) и \(\mathbf{b}\):</p>
    <div class="fbox">$$\operatorname{sim}(\mathbf{a},\mathbf{b})=\cos\theta=\frac{\mathbf{a}\cdot\mathbf{b}}{\lVert\mathbf{a}\rVert\,\lVert\mathbf{b}\rVert}.$$</div>
    <p class="dim">Оценки разных способов не сравнимы между собой по величине (у «букв» косинусы
      около 0.98, у «лексики» — около 0.1): важен только порядок соседей внутри одного способа.</p>
  </div>

  <h2 class="msec pop"><span class="tag">01</span>Смысл — LSA (о чём шутит)</h2>
  <div class="prose pop">
    <p>Строим матрицу <b>tf-idf</b> по содержательным леммам (комики \(\times\) слова). Для комика
      \(c\) и леммы \(w\):</p>
    <div class="fbox">$$\mathrm{tf}_{c,w}=\frac{n_{c,w}}{\sum_v n_{c,v}},\qquad
      \mathrm{idf}_w=\ln\frac{N+1}{\mathrm{df}_w+1}+1,\qquad
      x_{c,w}=\mathrm{tf}_{c,w}\cdot\mathrm{idf}_w,$$</div>
    <p>где \(n_{c,w}\) — сколько раз лемма встретилась у комика, \(\mathrm{df}_w\) — у скольких комиков
      она есть, \(N\) — число комиков. Строки \(L_2\)-нормируем, затем понижаем размерность
      <b>усечённым сингулярным разложением</b> (LSA, Deerwester и др. 1990):</p>
    <div class="fbox">$$X\approx U_k\,\Sigma_k\,V_k^{\top},\qquad \mathbf{d}_c=\big(U_k\Sigma_k\big)_{c},\qquad k=%LSA%.$$</div>
    <p>Слова сворачиваются в %LSA% латентных «тем», и близость — косинус векторов \(\mathbf{d}_c\)
      в этом пространстве. Так ловится сходство <b>тематики</b>, а не отдельных слов.</p>
  </div>

  <h2 class="msec pop"><span class="tag">02</span>Лексика — weighted log-odds (какими словами выделяется)</h2>
  <div class="prose pop">
    <p>«Стилевой отпечаток» комика — это слова, которыми он выделяется на фоне всех остальных.
      Меряем выделенность <b>weighted log-odds-ratio с приором Дирихле</b> (Monroe, Colaresi &amp;
      Quinn 2008). Пусть \(y_w^i\) — частота леммы \(w\) у комика \(i\), \(n_i=\sum_w y_w^i\),
      а группа \(j\) — весь остальной корпус. Приор берём от фонового распределения:
      \(\alpha_w=\alpha_0\,y_w^{\text{corpus}}/N\), \(\alpha_0=500\). Тогда</p>
    <div class="fbox">$$\delta_w=\ln\frac{y_w^{i}+\alpha_w}{n_i+\alpha_0-y_w^{i}-\alpha_w}
      -\ln\frac{y_w^{j}+\alpha_w}{n_j+\alpha_0-y_w^{j}-\alpha_w},$$</div>
    <div class="fbox">$$\widehat{\sigma}^2(\delta_w)\approx\frac{1}{y_w^{i}+\alpha_w}+\frac{1}{y_w^{j}+\alpha_w},
      \qquad \zeta_w=\frac{\delta_w}{\sqrt{\widehat{\sigma}^2(\delta_w)}}.$$</div>
    <p>Отпечаток — вектор из z-оценок \(\zeta_w\) по нарицательным словам с \(\zeta_w>1\)
      (имена, топонимы и организации отбрасываем, чтобы получить <b>манеру</b>, а не темы;
      берём топ-120). Близость комиков — косинус их отпечатков. Это ключевой фикс против
      «хаб-эффекта»: сравниваем <b>характерность</b> слов, а не объём корпуса, поэтому
      плодовитые комики не оказываются соседями всем подряд.</p>
  </div>

  <h2 class="msec pop"><span class="tag">03</span>Манера — Cosine Delta (как строит речь)</h2>
  <div class="prose pop">
    <p>Классическая стилометрия (Burrows 2002; Argamon 2008). Берём \(M=%MFW%\) самых частых
      слов корпуса — это в основном <b>служебные</b> слова (предлоги, союзы, частицы), которые
      автор не выбирает осознанно, поэтому они выдают манеру. Для каждого слова считаем его долю
      \(f_{c,w}\) у комика и <b>z-нормируем по столбцу</b> (по всем комикам):</p>
    <div class="fbox">$$z_{c,w}=\frac{f_{c,w}-\mu_w}{\sigma_w}.$$</div>
    <p>Cosine Delta (Smith &amp; Aldridge 2011) — косинус этих z-векторов. Чем ближе к 1,
      тем более похоже комики распределяют служебную лексику.</p>
  </div>

  <h2 class="msec pop"><span class="tag">04</span>Буквы — символьные 3-граммы</h2>
  <div class="prose pop">
    <p>Самый «низкоуровневый» след: разбиваем слова на символьные <b>триграммы</b> с границами
      (например, <code>_ко</code>, <code>кот</code>, <code>от_</code>), строим tf-idf-профиль
      триграмм и берём косинус. Ловит фонетико-орфографические привычки, но на одном языке
      профили близки почти у всех — эту метрику держим для полноты картины.</p>
  </div>

  <h2 class="msec pop"><span class="tag">05</span>Код</h2>
  <div class="prose pop">
    <p>Всё считается локально, без внешних моделей и без обращений к API. Скрипты открыты:</p>
    <div class="gh">
      <a href="%REPO%/blob/master/scripts/compute_features.py" target="_blank" rel="noopener">▸ compute_features.py</a>
      <a href="%REPO%/blob/master/scripts/build_features.py" target="_blank" rel="noopener">▸ build_features.py</a>
      <a href="%REPO%" target="_blank" rel="noopener">▸ репозиторий целиком</a>
    </div>
  </div>

  <h2 class="msec pop"><span class="tag">06</span>Источники</h2>
  <div class="prose pop">
    <ul class="refs">
      <li>Monroe B., Colaresi M., Quinn K. (2008). Fightin' Words: Lexical Feature Selection and Evaluation for Identifying the Content of Political Conflict. <i>Political Analysis</i> 16(4).</li>
      <li>Burrows J. (2002). 'Delta': a Measure of Stylistic Difference and a Guide to Likely Authorship. <i>LLC</i> 17(3).</li>
      <li>Argamon S. (2008). Interpreting Burrows's Delta: Geometric and Probabilistic Foundations. <i>LLC</i> 23(2).</li>
      <li>Smith P., Aldridge W. (2011). Improving Authorship Attribution: Optimizing Burrows' Delta Method. <i>JQL</i> 18(1).</li>
      <li>Deerwester S. и др. (1990). Indexing by Latent Semantic Analysis. <i>JASIS</i> 41(6).</li>
      <li>Метод «уникальных лемм на 25 000 слов» — по исследованию рэперов Ильи Иноземцева.</li>
    </ul>
  </div>

""" + FOOTER
    body = (body.replace("%MINSIM%", f"{m['min_sim']:,}")
                .replace("%POOL%", str(m["sim_pool"]))
                .replace("%LSA%", str(m["lsa_dim"]))
                .replace("%MFW%", str(m["mfw"]))
                .replace("%REPO%", REPO))
    return page("Как мы считаем похожесть — Стендап·Лексикон", body,
                head_extra=MATHJAX)


def main():
    feat = json.loads((ROOT / "features.json").read_text(encoding="utf-8"))
    DOCS.mkdir(exist_ok=True)
    (DOCS / "similar.html").write_text(build_similar(feat), encoding="utf-8")
    (DOCS / "method.html").write_text(build_method(feat), encoding="utf-8")
    print(f"wrote {DOCS/'similar.html'} and {DOCS/'method.html'}")
    print(f"similar={len(feat['similar'])} comics")


if __name__ == "__main__":
    main()
