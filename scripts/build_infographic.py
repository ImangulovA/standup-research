"""Build a self-contained neobrutalism infographic (docs/index.html) from report.json.

Only aggregate data (comic name + lemma counts + one representative concert URL)
is embedded — safe to publish. Comic names link to a parsed concert on YouTube.
Design: light neobrutalism (bold borders, hard offset shadows, vivid accents).
Branding: Невежда (t.me/newezha) + Шаппелл позвонит (t.me/Chappellepozvonit).
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
WINDOW = 25000


def main():
    rows = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    rows.sort(key=lambda r: r["unique_lemmas_25k"], reverse=True)
    # Density: unique lemmas per 100 words, measured over the same window the
    # lemmas were counted in (min(total_words, WINDOW)). For reliable comics the
    # denominator is fixed at WINDOW, so this is a linear rescale of the lemma
    # count; for short (pale) corpora fewer repeats inflate it, so it is only
    # comparable among reliable comics.
    for r in rows:
        denom = min(r["total_words"], WINDOW)
        r["lemmas_per_100"] = round(r["unique_lemmas_25k"] / denom * 100, 1)
    reliable = [r for r in rows if r["reliable"]]

    meta = {
        "comics": len(rows),
        "concerts": sum(r["concerts"] for r in rows),
        "words": sum(r["total_words"] for r in rows),
        "reliable": len(reliable),
        "richest": reliable[0] if reliable else (rows[0] if rows else None),
        "median": int(statistics.median(r["unique_lemmas_25k"] for r in reliable)) if reliable else 0,
        "window": WINDOW,
    }

    html = TEMPLATE.replace("__DATA__", json.dumps(rows, ensure_ascii=False))
    html = html.replace("__META__", json.dumps(meta, ensure_ascii=False))

    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"wrote {DOCS/'index.html'}  ({len(html):,} bytes)")
    print(f"comics={meta['comics']} reliable={meta['reliable']} "
          f"richest={meta['richest']['artist']} median={meta['median']}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Словарный запас стендап-комиков</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
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
.chip .d{width:9px;height:9px;border-radius:50%;border:1.5px solid var(--ink)}
.chip.c2 .d{border-color:#fff}
.chip.v{background:var(--paper);color:var(--muted);box-shadow:none;font-weight:700}
.chip.nav{background:var(--secondary-soft);color:var(--ink)}

header h1{font-size:clamp(26px,4.6vw,44px);line-height:1.05;font-weight:900;letter-spacing:-.02em;margin:0 0 14px;max-width:900px}
header h1 mark{background:var(--primary);padding:0 8px;border:var(--bd2);border-radius:8px;box-shadow:var(--sh-sm)}
.sub{color:var(--muted);font-size:16px;line-height:1.55;max-width:720px;font-weight:500}
.sub b{color:var(--ink);background:var(--primary-soft);padding:0 5px;border-radius:5px}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin:28px 0 36px}
.tile{border:var(--bd);border-radius:var(--r);padding:16px 18px;box-shadow:var(--sh)}
.tile .n{font-family:var(--mono);font-size:30px;font-weight:700;line-height:1;letter-spacing:-.02em}
.tile .l{font-size:12.5px;font-weight:700;margin-top:8px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}
.tile.t1{background:var(--primary)} .tile.t1 .l{color:#7a5c00}
.tile.t2{background:var(--secondary);color:#fff} .tile.t2 .n,.tile.t2 .l{color:#fff}
.tile.t3{background:var(--paper)}
.tile.t4{background:var(--primary-soft)}
.tile.t5{background:var(--secondary-soft)}

.sec{display:flex;align-items:center;gap:12px;margin:0 0 16px;font-weight:900;font-size:13px;
  text-transform:uppercase;letter-spacing:.08em}
.sec .tag{font-family:var(--mono);background:var(--ink);color:var(--bg);padding:3px 9px;border-radius:6px;font-size:12px}
.sec::after{content:'';flex:1;height:3px;background:var(--ink);border-radius:3px}

.card{background:var(--paper);border:var(--bd);border-radius:var(--r);padding:24px;box-shadow:var(--sh-lg);margin-bottom:36px}
.card .hint{color:var(--faint);font-size:13px;margin:-4px 0 16px;font-weight:600}
.card .hint b{color:var(--secondary)}
#chart{width:100%;height:auto;display:block}
.axis text{fill:var(--muted);font-family:var(--mono);font-size:11px;font-weight:500}
.axis line{stroke:var(--ink);stroke-width:2}
.land line{stroke:var(--faint);stroke-dasharray:4 4}
.land text{fill:var(--muted);font-family:var(--mono);font-size:9.5px;font-weight:500}
.dot{cursor:pointer}

.callout{background:var(--primary);border:var(--bd);border-radius:var(--r);padding:22px 24px;box-shadow:var(--sh);margin-bottom:36px}
.callout h3{font-size:18px;font-weight:900;margin-bottom:12px;display:flex;align-items:center;gap:10px}
.callout p{font-size:15px;line-height:1.6;margin-bottom:10px;font-weight:500}
.callout p:last-child{margin-bottom:0} .callout b{background:#fff;padding:0 5px;border-radius:5px;border:1.5px solid var(--ink)}

.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:stretch;margin-bottom:20px}
.search{flex:1;min-width:210px;padding:12px 15px;border:var(--bd2);border-radius:10px;background:var(--paper);
  font-family:var(--font);font-weight:600;font-size:15px;color:var(--ink);outline:none;box-shadow:var(--sh-sm)}
.search:focus{box-shadow:var(--sh)} .search::placeholder{color:var(--faint)}
.seg{display:inline-flex;border:var(--bd2);border-radius:10px;overflow:hidden;box-shadow:var(--sh-sm)}
.seg button{background:var(--paper);color:var(--muted);border:0;padding:10px 16px;font-family:var(--font);
  font-weight:800;font-size:13px;cursor:pointer;text-transform:uppercase;letter-spacing:.03em}
.seg button+button{border-left:var(--bd2)}
.seg button.on{background:var(--secondary);color:#fff}

.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14.5px}
thead th{text-align:left;padding:11px 12px;font-weight:800;font-size:12px;text-transform:uppercase;
  letter-spacing:.04em;color:var(--muted);border-bottom:var(--bd2)}
tbody td{padding:11px 12px;border-bottom:2px solid #eceae4;font-weight:600;vertical-align:middle}
tbody tr:hover{background:var(--primary-soft)}
tr.pale td{color:var(--faint)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;font-family:var(--mono)}
.rank{width:40px;font-family:var(--mono);font-weight:700;color:var(--faint)}
.clink{color:var(--secondary);font-weight:800;text-decoration:none;border-bottom:2px solid transparent}
.clink:hover{border-bottom-color:var(--secondary)}
.clink .ext{font-size:11px;opacity:.6}
.bar{height:9px;border-radius:4px;background:var(--secondary);border:1.5px solid var(--ink)}
tr.pale .bar{background:#cfd3da}
.badge{display:inline-block;font-family:var(--mono);font-size:10px;font-weight:700;padding:1px 6px;
  border:1.5px solid var(--warning);border-radius:5px;color:var(--warning);margin-left:6px}

.method{background:var(--paper);border:var(--bd2);border-radius:var(--r);padding:22px;box-shadow:var(--sh-sm);
  font-size:14.5px;line-height:1.65;color:var(--muted);font-weight:500;margin-bottom:36px}
.method b{color:var(--ink)} .method p{margin-bottom:10px} .method p:last-child{margin-bottom:0}
.method .dim{color:var(--faint);font-size:13.5px}

.tt{position:fixed;pointer-events:none;background:var(--ink);color:#fff;border-radius:10px;padding:9px 12px;
  font-size:13px;opacity:0;transition:opacity .1s;z-index:9;max-width:250px;box-shadow:var(--sh-sm);font-weight:600}
.tt .n{font-weight:800;margin-bottom:3px}
.tt .m{color:#b9c1d1;font-size:11.5px;font-weight:500}
.tt .go{color:var(--primary);font-size:11px;margin-top:4px}

footer{margin-top:40px;border-top:var(--bd2);padding-top:20px;color:var(--muted);font-size:13px;line-height:1.8;font-weight:500}
footer a{color:var(--muted);font-weight:700}
footer a.f1{color:var(--ink);background:var(--primary);padding:1px 6px;border-radius:5px;border:1.5px solid var(--ink);text-decoration:none}
footer a.f2{color:#fff;background:var(--secondary);padding:1px 6px;border-radius:5px;border:1.5px solid var(--ink);text-decoration:none}
footer a.plain{text-decoration:underline}
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar pop">
    <div class="brand">СТЕНДАП<span class="s">·</span>ЛЕКСИКОН</div>
    <div class="chips">
      <a class="chip c1" href="https://t.me/newezha" target="_blank" rel="noopener"><span class="d"></span>Невежда</a>
      <a class="chip c2" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener"><span class="d"></span>Шаппелл позвонит</a>
      <a class="chip nav" href="added.html">Концерты, добавленные вручную →</a>
      <span class="chip v">v1.1</span>
    </div>
  </div>

  <header class="pop" style="animation-delay:.05s">
    <h1>У кого из стендап-комиков <mark>богаче</mark> словарный запас?</h1>
    <p class="sub">Мы провели исследование словарного запаса русскоязычных комиков, основываясь
      на материале их стендап-концертов. Считаем, сколько разных лемм встречается в первых
      <b id="win"></b> словах очищенного корпуса выступлений. Имя комика ведёт на один из его концертов.</p>
  </header>

  <div class="tiles pop" id="tiles" style="animation-delay:.1s"></div>

  <h2 class="sec pop" style="animation-delay:.15s"><span class="tag">01</span>Шкала разнообразия лексики</h2>
  <div class="card pop" style="animation-delay:.15s">
    <p class="hint">Каждый маркер — комик. Бледные — корпус меньше <span class="winw"></span> слов
      (ниже надёжность). Наведи на маркер, а <b>клик открывает концерт</b>.</p>
    <svg id="chart"></svg>
  </div>

  <h2 class="sec pop"><span class="tag">02</span>Методология</h2>
  <div class="method pop">
    <p>Мы взяли тексты всех концертов из списка на сайте Ильи Якямсева, всего получилось
      <b>321 выступление</b>. Затем мы загрузили их в нейросеть, чтобы она оценила
      разнообразие слов, используемых комиком на сцене.</p>
    <p>Потом нейросеть предложила ещё несколько видео стендап-комиков, упомянутых на сайте
      Ильи, и из них мы <b>вручную отобрали</b> те, что подходят для нашего исследования
      (небольшие выступления и истории – да, подкасты и стримы – нет).</p>
    <p>Для анализа использовался метод <b>Ильи Иноземцева</b>, который делал аналогичное
      исследование словарного запаса российских рэперов. У каждого комика мы взяли текстовый
      массив из <b>25 000 слов</b>. Это было сделано для объективности: чтобы комики, которые
      выпустили больше концертов, не получали преимущество. Хотя они, несомненно, молодцы.</p>
    <p>В каждом из этих массивов мы посчитали количество <b>уникальных лемм</b>. Лемма — это
      словарная, или начальная, форма слова. Все грамматические формы одного и того же слова
      сводятся к одной лемме. То есть, если комик рассказывает про простату, слова «простата»,
      «простаты», «простате», «простату» и так далее будут относиться к одной лемме.</p>
    <p class="dim">Технически: субтитры очищаются, точные повторы строк удаляются, слова
      приводятся к леммам (razdel + pymorphy3), считаются только кириллические слова. Комики
      с корпусом меньше 25 000 слов помечены <b>бледным</b> — на неполном окне метрика менее
      надёжна. Подписи на шкале («когда-нибудь замечали?», «еда в самолётах?» и т.д.) —
      шуточные стендап-заходы для ориентира, а не реальные бенчмарки.</p>
  </div>

  <div class="callout pop">
    <h3>&#9888;&#65039; важная оговорка</h3>
    <p>Разумеется, словарный запас не является исчерпывающей оценкой мастерства комика.
      Он не учитывает качество шуток, построение текста, подачу, отыгрыши и другие особенности
      стендапа. Исследование посвящено исключительно <b>лексическому разнообразию речи</b>.</p>
  </div>

  <h2 class="sec pop"><span class="tag">03</span>Рейтинг комиков</h2>
  <div class="card pop">
    <div class="controls">
      <input type="search" id="q" class="search" placeholder="Найти комика…" autocomplete="off">
      <div class="seg">
        <button data-sort="rating" class="on">По леммам</button>
        <button data-sort="density">По плотности</button>
        <button data-sort="alpha">По алфавиту</button>
      </div>
    </div>
    <p class="hint">«Лемм / 100 слов» — плотность лексики. У надёжных комиков окно фиксировано
      на <span class="winw"></span> словах, так что этот столбец повторяет порядок по леммам;
      у <b>бледных</b> корпус короче, и меньшее число повторов завышает плотность, поэтому
      сравнивать её честно можно только среди надёжных.</p>
    <div class="tbl-wrap">
      <table>
        <thead><tr>
          <th class="rank">#</th><th>Комик</th>
          <th class="num">Леммы / 25k</th><th class="num">Лемм / 100 слов</th>
          <th class="num">Выст.</th><th class="num">Слов</th>
        </tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
  </div>

  <footer class="pop">
    Проект каналов <a class="f1" href="https://t.me/newezha" target="_blank" rel="noopener">Невежда</a>
    и <a class="f2" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener">Шаппелл позвонит</a>.<br>
    Каталог концертов: <a class="plain" href="https://smeshno.xyz/youtube/full/" target="_blank" rel="noopener">смешно.xyz</a> (Илья Якямсев).
    Методика вдохновлена исследованием рэперов Ильи Иноземцева. Публикуются только
    агрегированные цифры; тексты выступлений не показываются.
  </footer>
</div>

<div class="tt" id="tt"></div>

<script>
const DATA=__DATA__, META=__META__;
const fmt=n=>n.toLocaleString('ru-RU');
document.getElementById('win').textContent=fmt(META.window);
document.querySelectorAll('.winw').forEach(e=>e.textContent=fmt(META.window));

const tiles=[
  [fmt(META.comics),'комиков','t1'],
  [fmt(META.concerts),'выступлений','t2'],
  [fmt(META.words),'слов обработано','t3'],
  [META.richest?fmt(META.richest.unique_lemmas_25k):'—','богаче всех: '+(META.richest?META.richest.artist:'—'),'t4'],
  [fmt(META.median),'медиана (надёжные)','t5'],
];
document.getElementById('tiles').innerHTML=tiles.map(t=>
  `<div class="tile ${t[2]}"><div class="n">${t[0]}</div><div class="l">${t[1]}</div></div>`).join('');

const tt=document.getElementById('tt');
function showTT(h,x,y){tt.innerHTML=h;tt.style.opacity=1;
  tt.style.left=Math.min(x+14,window.innerWidth-260)+'px';tt.style.top=(y+14)+'px';}
function hideTT(){tt.style.opacity=0;}
const LAND=[
  {v:1000,t:'«когда-нибудь замечали?»'},
  {v:2000,t:'«женщины странные»'},
  {v:3000,t:'«смешные имена таксистов»'},
  {v:4000,t:'«еда в самолётах?»'},
  {v:5000,t:'«7 / 7 грязных слов»'},
];

function drawChart(hl){
  const svg=document.getElementById('chart');
  const W=svg.clientWidth||980,padL=14,padR=14,padB=34,padT=82;
  const lo=0,hi=5000;
  const x=v=>padL+(v-lo)/(hi-lo)*(W-padL-padR);
  const r=6.5, midY=padT+96;
  const pts=DATA.map(d=>({d,cx:x(d.unique_lemmas_25k),cy:0})).sort((a,b)=>a.cx-b.cx);
  for(const p of pts){let y=midY,dir=1,s=0;
    const hit=yy=>pts.some(q=>q!==p&&q.cy!==0&&Math.hypot(q.cx-p.cx,q.cy-yy)<r*2+1);
    while(hit(y)){s++;y=midY+dir*s*(r*1.45);dir*=-1;} p.cy=y;}
  const H=300; svg.setAttribute('viewBox',`0 0 ${W} ${H}`); svg.setAttribute('height',H);
  let s='';
  // landmarks: horizontal labels, staggered by row to avoid overlap
  LAND.forEach((l,i)=>{ if(l.v<lo||l.v>hi) return;
    const ly=13+i*11, endAnchor=x(l.v)>W*0.6;
    const tx=endAnchor?x(l.v)-5:x(l.v)+5, anc=endAnchor?'end':'start';
    s+=`<g class="land"><line x1="${x(l.v)}" y1="${padT-8}" x2="${x(l.v)}" y2="${H-padB}"/>`+
       `<text x="${tx}" y="${ly}" text-anchor="${anc}">${fmt(l.v)} · ${l.t}</text></g>`;});
  // axis
  s+=`<g class="axis"><line x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}"/>`;
  for(let v=lo;v<=hi;v+=1000){s+=`<text x="${x(v)}" y="${H-padB+18}" text-anchor="middle">${fmt(v)}</text>`;}
  s+=`</g>`;
  // dots
  for(const p of pts){
    const rel=p.d.reliable,hot=hl&&p.d.artist===hl;
    const fill=hot?'var(--primary)':(rel?'var(--secondary)':'var(--paper)');
    const stroke=hot?'var(--ink)':(rel?'var(--ink)':'var(--warning)');
    const sw=hot?2.5:(rel?1.6:2);
    const op=hl?(hot?1:.3):1;
    s+=`<circle class="dot" data-a="${encodeURIComponent(p.d.artist)}" cx="${p.cx}" cy="${p.cy}" r="${hot?r+2.5:r}" `+
       `fill="${fill}" stroke="${stroke}" stroke-width="${sw}" opacity="${op}"/>`;}
  svg.innerHTML=s;
  svg.querySelectorAll('.dot').forEach(c=>{
    const d=DATA.find(x=>x.artist===decodeURIComponent(c.dataset.a));
    c.addEventListener('mousemove',e=>showTT(
      `<div class="n">${d.artist}</div><div>${fmt(d.unique_lemmas_25k)} лемм / 25k</div>`+
      `<div class="m">${d.concerts} выст. · ${fmt(d.total_words)} слов`+(d.reliable?'':' · бледный')+`</div>`+
      (d.url?`<div class="go">▶ клик — открыть концерт</div>`:''),e.clientX,e.clientY));
    c.addEventListener('mouseleave',hideTT);
    if(d.url) c.addEventListener('click',()=>window.open(d.url,'_blank','noopener'));
  });
}

let sortMode='rating';
function firstMatch(q){q=q.trim().toLowerCase();const m=DATA.find(d=>d.artist.toLowerCase().includes(q));return m?m.artist:null;}
function esc(s){return s.replace(/"/g,'&quot;');}
function drawTable(filter){
  let rows=DATA.slice();
  if(sortMode==='alpha')rows.sort((a,b)=>a.artist.localeCompare(b.artist,'ru'));
  else if(sortMode==='density')rows.sort((a,b)=>b.lemmas_per_100-a.lemmas_per_100);
  else rows.sort((a,b)=>b.unique_lemmas_25k-a.unique_lemmas_25k);
  const f=(filter||'').trim().toLowerCase();
  if(f)rows=rows.filter(r=>r.artist.toLowerCase().includes(f));
  const maxL=Math.max(...DATA.map(d=>d.unique_lemmas_25k));
  document.getElementById('rows').innerHTML=rows.map((r,i)=>{
    const w=Math.round(r.unique_lemmas_25k/maxL*88);
    const name=r.url?`<a class="clink" href="${esc(r.url)}" target="_blank" rel="noopener">${r.artist} <span class="ext">↗</span></a>`:r.artist;
    const showRank=sortMode==='rating'||sortMode==='density';
    return `<tr class="${r.reliable?'':'pale'}" data-a="${encodeURIComponent(r.artist)}">`+
      `<td class="rank">${showRank?i+1:''}</td>`+
      `<td>${name}${r.reliable?'':'<span class="badge">&lt;25k</span>'}</td>`+
      `<td class="num"><div style="display:flex;align-items:center;gap:8px;justify-content:flex-end">`+
        `<div class="bar" style="width:${w}px"></div><span>${fmt(r.unique_lemmas_25k)}</span></div></td>`+
      `<td class="num">${r.lemmas_per_100.toFixed(1)}</td>`+
      `<td class="num">${r.concerts}</td><td class="num">${fmt(r.total_words)}</td></tr>`;}).join('');
  document.querySelectorAll('#rows tr').forEach(tr=>{
    tr.addEventListener('mouseenter',()=>drawChart(decodeURIComponent(tr.dataset.a)));
    tr.addEventListener('mouseleave',()=>drawChart(firstMatch(document.getElementById('q').value)));});
}
document.getElementById('q').addEventListener('input',e=>{drawTable(e.target.value);drawChart(firstMatch(e.target.value));});
document.querySelectorAll('.seg button').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.seg button').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');sortMode=b.dataset.sort;drawTable(document.getElementById('q').value);}));

drawChart(null);drawTable('');
window.addEventListener('resize',()=>drawChart(firstMatch(document.getElementById('q').value)));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
