"""Build a self-contained infographic (docs/index.html) from report.json.

Only aggregate data (comic name + lemma counts) is embedded — safe to publish.
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
<style>
  :root{
    --bg:#0d0e12; --panel:#161822; --panel2:#1e2130; --line:#2a2e3f;
    --text:#e9ebf2; --muted:#9aa0b4; --dim:#6b7186;
    --accent:#ff5d5d; --accent2:#b98bff; --gold:#ffcf5c; --pale:#4b5168;
    --ok:#5ad0a0;
  }
  *{box-sizing:border-box}
  html,body{margin:0;background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  a{color:inherit}
  .wrap{max-width:1080px;margin:0 auto;padding:28px 18px 80px}
  header h1{font-size:30px;line-height:1.15;margin:0 0 8px;font-weight:800;letter-spacing:-.02em}
  header p.sub{color:var(--muted);margin:0 0 18px;max-width:720px;font-size:15px;line-height:1.5}
  .brands{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 24px}
  .chip{display:inline-flex;align-items:center;gap:7px;padding:7px 13px;border-radius:999px;
    background:var(--panel2);border:1px solid var(--line);font-size:13px;font-weight:600;
    text-decoration:none;transition:.15s}
  .chip:hover{border-color:var(--accent);transform:translateY(-1px)}
  .chip .d{width:8px;height:8px;border-radius:50%}
  .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:0 0 26px}
  .tile{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:15px 16px}
  .tile .n{font-size:26px;font-weight:800;letter-spacing:-.02em}
  .tile .l{color:var(--muted);font-size:12px;margin-top:3px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px;margin:0 0 22px}
  .card h2{margin:0 0 4px;font-size:17px}
  .card .hint{color:var(--dim);font-size:12.5px;margin:0 0 14px}
  .controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:0 0 16px}
  input[type=search]{flex:1;min-width:200px;background:var(--panel2);border:1px solid var(--line);
    color:var(--text);border-radius:10px;padding:10px 13px;font-size:14px;outline:none}
  input[type=search]:focus{border-color:var(--accent)}
  .seg{display:inline-flex;border:1px solid var(--line);border-radius:10px;overflow:hidden}
  .seg button{background:var(--panel2);color:var(--muted);border:0;padding:9px 14px;font-size:13px;
    cursor:pointer;font-weight:600}
  .seg button.on{background:var(--accent);color:#1a0000}
  #chart{width:100%;height:auto;display:block}
  .dot{cursor:pointer;transition:opacity .12s}
  .dot:hover{stroke:#fff;stroke-width:1.5}
  .axis text{fill:var(--dim);font-size:11px}
  .axis line{stroke:var(--line)}
  .land line{stroke:var(--dim);stroke-dasharray:3 4;opacity:.55}
  .land text{fill:var(--dim);font-size:10.5px}
  table{width:100%;border-collapse:collapse;font-size:14px}
  th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}
  th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em;cursor:pointer}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  tr.pale td{color:var(--dim)}
  .badge{display:inline-block;font-size:11px;padding:2px 7px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
  .rank{color:var(--dim);width:34px}
  .bar{height:7px;border-radius:6px;background:linear-gradient(90deg,var(--accent),var(--accent2))}
  .tt{position:fixed;pointer-events:none;background:#0a0b0f;border:1px solid var(--line);
    border-radius:10px;padding:9px 11px;font-size:12.5px;opacity:0;transition:opacity .1s;z-index:9;max-width:240px}
  .tt b{font-size:13px}
  footer{color:var(--dim);font-size:12px;margin-top:26px;line-height:1.6}
  .method{color:var(--muted);font-size:13px;line-height:1.6}
  .method b{color:var(--text)}
  .note{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--gold);
    border-radius:14px;padding:16px 18px;margin:0 0 22px}
  .note h2{margin:0 0 8px;font-size:16px}
  .note p{color:var(--muted);font-size:13.5px;line-height:1.65;margin:0 0 8px}
  .note p:last-child{margin-bottom:0}
  .note b{color:var(--text)}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>У кого из стендап-комиков богаче словарный запас?</h1>
    <p class="sub">Корпусное исследование русскоязычного стендапа. Считаем, сколько разных
      лемм (словарных форм) встречается в первых <b id="win"></b> словах очищенного корпуса
      выступлений комика. Чем правее — тем разнообразнее лексика.</p>
    <div class="brands">
      <a class="chip" href="https://t.me/newezha" target="_blank" rel="noopener">
        <span class="d" style="background:var(--accent)"></span>Невежда</a>
      <a class="chip" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener">
        <span class="d" style="background:var(--accent2)"></span>Шаппелл позвонит</a>
    </div>
  </header>

  <div class="tiles" id="tiles"></div>

  <div class="card">
    <h2>Шкала разнообразия лексики</h2>
    <p class="hint">Каждый кружок — комик. Бледные — корпус меньше <span class="winw"></span> слов
      (ниже надёжность). Наведи на кружок или найди комика ниже.</p>
    <svg id="chart"></svg>
  </div>

  <div class="card">
    <div class="controls">
      <input type="search" id="q" placeholder="Найти комика…" autocomplete="off">
      <div class="seg">
        <button data-sort="rating" class="on">По рейтингу</button>
        <button data-sort="alpha">По алфавиту</button>
      </div>
    </div>
    <table>
      <thead><tr>
        <th class="rank">#</th><th>Комик</th>
        <th class="num" data-k="unique_lemmas_25k">Леммы / 25k</th>
        <th class="num" data-k="concerts">Выступл.</th>
        <th class="num" data-k="total_words">Слов</th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
  </div>

  <div class="note">
    <h2>Важная оговорка: стендап не песни</h2>
    <p>Идея Иноземцева — обрубать корпус на первых <b>25 000 слов</b> ради чистоты
    сравнения: так неважно, сто у тебя минут материала или тысяча, все меряются на
    одинаковом объёме, и мы смотрим на число уникальных лемм. Для песен это работает
    хорошо.</p>
    <p>Для концертов — хуже. Восемь тысяч уникальных лемм в песнях представить сильно
    проще, чем восемь тысяч в концерте. В стендапе много повторяющихся заходов,
    подводок и коллбэков, формулировки часто похожи, поэтому уникальных лемм
    набирается меньше. Поэтому напрямую сравнивать комиков с рэперской шкалой не
    стоит.</p>
    <p>Скорее всего, для стендапа мы <b>расширим окно первых слов</b>; пока просто
    держим эту разницу в голове.</p>
  </div>

  <div class="card method">
    <h2 style="margin-bottom:8px">Методология</h2>
    <p>Транскрипты (субтитры) выступлений очищаются, точные повторы строк удаляются, слова
    приводятся к леммам (<b>razdel + pymorphy3</b>). Основная метрика — число уникальных лемм
    в первых <b>25 000 слов</b> очищенного корпуса: так честно сравнивать комиков с разным
    объёмом материала. Считаем <b>только русские (кириллические)</b> слова. Комики с корпусом
    меньше 25 000 слов показаны бледными: их результат менее надёжен.</p>
    <p style="color:var(--dim)">Ориентиры («дошкольник», «иностранец», «филолог») — грубый
    контекст по экспертным оценкам словаря, а не корпусный подсчёт. Это не оценка активного
    словаря человека.</p>
  </div>

  <footer>
    Проект каналов <a href="https://t.me/newezha" target="_blank">Невежда</a> и
    <a href="https://t.me/Chappellepozvonit" target="_blank">Шаппелл позвонит</a>.
    Методика вдохновлена исследованием рэперов Ильи Иноземцева. Показываем только
    агрегированные цифры; сами тексты выступлений не публикуются.
  </footer>
</div>

<div class="tt" id="tt"></div>

<script>
const DATA = __DATA__;
const META = __META__;
const fmt = n => n.toLocaleString('ru-RU');

document.getElementById('win').textContent = fmt(META.window);
document.querySelectorAll('.winw').forEach(e=>e.textContent=fmt(META.window));

// ---- tiles ----
const tiles = [
  [fmt(META.comics), 'комиков проанализировано'],
  [fmt(META.concerts), 'выступлений обработано'],
  [fmt(META.words), 'слов в текстах'],
  [META.richest ? META.richest.unique_lemmas_25k : '—',
    'богаче всех: ' + (META.richest ? META.richest.artist : '—')],
  [fmt(META.median), 'медиана (надёжные)'],
];
document.getElementById('tiles').innerHTML = tiles.map(t=>
  `<div class="tile"><div class="n">${t[0]}</div><div class="l">${t[1]}</div></div>`).join('');

// ---- beeswarm chart ----
const tt = document.getElementById('tt');
function showTT(html,x,y){tt.innerHTML=html;tt.style.opacity=1;
  tt.style.left=Math.min(x+14,window.innerWidth-250)+'px';tt.style.top=(y+14)+'px';}
function hideTT(){tt.style.opacity=0;}

const LAND = [
  {v:2000,t:'дошкольник'},
  {v:4000,t:'иностранец'},
  {v:9000,t:'филолог'},
];

function drawChart(highlight){
  const svg = document.getElementById('chart');
  const W = svg.clientWidth || 1000, padL=16, padR=16, padT=26, padB=34;
  const vals = DATA.map(d=>d.unique_lemmas_25k);
  const maxV = Math.max(...vals, 9200), minV = Math.min(...vals, 1800);
  const lo = Math.floor((minV-200)/1000)*1000, hi = Math.ceil((maxV+200)/1000)*1000;
  const x = v => padL + (v-lo)/(hi-lo)*(W-padL-padR);
  const r = 6;
  // beeswarm dodge
  const pts = DATA.map(d=>({d, cx:x(d.unique_lemmas_25k), cy:0}))
                  .sort((a,b)=>a.cx-b.cx);
  const midY = padT + 120;
  for(const p of pts){
    let y=midY, dir=1, step=0;
    const collide = yy => pts.some(q=>q!==p && q.cy!==0 &&
      Math.hypot(q.cx-p.cx, q.cy-yy) < r*2+1);
    while(collide(y)){ step++; y = midY + dir*step*(r*1.4); dir*=-1; }
    p.cy = y;
  }
  const H = 300;
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
  svg.setAttribute('height',H);
  let s = '';
  // landmarks
  for(const l of LAND){ if(l.v<lo||l.v>hi) continue;
    s += `<g class="land"><line x1="${x(l.v)}" y1="${padT-6}" x2="${x(l.v)}" y2="${H-padB}"/>`+
         `<text x="${x(l.v)+4}" y="${padT+2}">${l.t} ~${fmt(l.v)}</text></g>`;
  }
  // axis
  s += `<g class="axis"><line x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}"/>`;
  for(let v=lo; v<=hi; v+=1000){ s += `<text x="${x(v)}" y="${H-padB+16}" text-anchor="middle">${fmt(v)}</text>`; }
  s += `</g>`;
  // dots
  for(const p of pts){
    const rel = p.d.reliable;
    const hot = highlight && p.d.artist===highlight;
    const fill = rel ? (hot?'var(--gold)':'var(--accent)') : 'none';
    const stroke = rel ? 'none' : 'var(--pale)';
    const op = highlight ? (hot?1:.28) : (rel?.92:.6);
    s += `<circle class="dot" data-a="${encodeURIComponent(p.d.artist)}" cx="${p.cx}" cy="${p.cy}" r="${hot?r+2:r}" `+
         `fill="${fill}" stroke="${stroke}" stroke-width="1.5" opacity="${op}"/>`;
  }
  svg.innerHTML = s;
  svg.querySelectorAll('.dot').forEach(c=>{
    c.addEventListener('mousemove',e=>{
      const d = DATA.find(x=>x.artist===decodeURIComponent(c.dataset.a));
      showTT(`<b>${d.artist}</b><br>${fmt(d.unique_lemmas_25k)} лемм / 25k`+
        `<br><span style="color:var(--dim)">${d.concerts} выступл. · ${fmt(d.total_words)} слов`+
        (d.reliable?'':' · бледный круг')+`</span>`, e.clientX, e.clientY);
    });
    c.addEventListener('mouseleave',hideTT);
  });
}

// ---- table ----
let sortMode='rating';
function drawTable(filter){
  let rows = DATA.slice();
  if(sortMode==='alpha') rows.sort((a,b)=>a.artist.localeCompare(b.artist,'ru'));
  else rows.sort((a,b)=>b.unique_lemmas_25k-a.unique_lemmas_25k);
  const f = (filter||'').trim().toLowerCase();
  if(f) rows = rows.filter(r=>r.artist.toLowerCase().includes(f));
  const maxL = Math.max(...DATA.map(d=>d.unique_lemmas_25k));
  const body = document.getElementById('rows');
  body.innerHTML = rows.map((r,i)=>{
    const w = Math.round(r.unique_lemmas_25k/maxL*90);
    return `<tr class="${r.reliable?'':'pale'}" data-a="${encodeURIComponent(r.artist)}">`+
      `<td class="rank">${sortMode==='rating'?i+1:''}</td>`+
      `<td>${r.artist} ${r.reliable?'':'<span class="badge">&lt;25k</span>'}</td>`+
      `<td class="num"><div style="display:flex;align-items:center;gap:8px;justify-content:flex-end">`+
        `<div class="bar" style="width:${w}px"></div><span>${fmt(r.unique_lemmas_25k)}</span></div></td>`+
      `<td class="num">${r.concerts}</td>`+
      `<td class="num">${fmt(r.total_words)}</td></tr>`;
  }).join('');
  body.querySelectorAll('tr').forEach(tr=>{
    tr.addEventListener('mouseenter',()=>drawChart(decodeURIComponent(tr.dataset.a)));
    tr.addEventListener('mouseleave',()=>drawChart(document.getElementById('q').value.trim()?
      firstMatch(document.getElementById('q').value):null));
  });
}
function firstMatch(q){ q=q.trim().toLowerCase(); const m=DATA.find(d=>d.artist.toLowerCase().includes(q)); return m?m.artist:null; }

document.getElementById('q').addEventListener('input',e=>{
  drawTable(e.target.value);
  drawChart(firstMatch(e.target.value));
});
document.querySelectorAll('.seg button').forEach(b=>{
  b.addEventListener('click',()=>{
    document.querySelectorAll('.seg button').forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); sortMode=b.dataset.sort; drawTable(document.getElementById('q').value);
  });
});

function boot(){ drawChart(null); drawTable(''); }
boot();
window.addEventListener('resize',()=>drawChart(firstMatch(document.getElementById('q').value)));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
