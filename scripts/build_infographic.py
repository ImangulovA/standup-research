"""Build a self-contained cyberpunk infographic (docs/index.html) from report.json.

Only aggregate data (comic name + lemma counts) is embedded — safe to publish.
Design: cyberpunk-frontend-design-skill tokens (cyan primary, dark terminal),
adapted to a static page. Cyrillic renders in JetBrains Mono; Press Start 2P is
used only for Latin accents (it has no Cyrillic glyphs).
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
<title>СТЕНДАП :: словарный запас комиков</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=JetBrains+Mono:wght@400;700&family=Noto+Sans+JP:wght@700;900&display=swap" rel="stylesheet">
<style>
:root{
  --cyan:#00f0ff; --pink:#ff003c; --yellow:#fcee0a; --green:#39ff14;
  --bg-deep:#05050a; --bg-surface:rgba(10,10,15,.8); --bg-surface-faint:rgba(10,10,15,.4);
  --bg-input:rgba(0,240,255,.03); --bg-input-focus:rgba(0,240,255,.05); --bg-panel:#0a0a0f;
  --text-primary:#fff; --text-secondary:rgba(255,255,255,.8); --text-muted:rgba(255,255,255,.55);
  --text-faint:rgba(255,255,255,.45); --text-ghost:rgba(255,255,255,.35);
  --border-structural:rgba(255,255,255,.06); --border-subtle:rgba(255,255,255,.08); --border-medium:rgba(255,255,255,.15);
  --cyan-05:rgba(0,240,255,.05); --cyan-08:rgba(0,240,255,.08); --cyan-10:rgba(0,240,255,.1);
  --cyan-15:rgba(0,240,255,.15); --cyan-30:rgba(0,240,255,.3); --cyan-40:rgba(0,240,255,.4);
  --pink-08:rgba(255,0,60,.08); --yellow-08:rgba(252,238,10,.08);
  --font-pixel:'Press Start 2P',cursive; --font-mono:'JetBrains Mono',monospace; --font-jp:'Noto Sans JP',sans-serif;
  --tracking-wide:.12em; --tracking-wider:.15em; --tracking-widest:.2em;
  --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px; --space-6:24px; --space-8:32px;
  --shadow-glow-cyan:0 0 10px rgba(0,240,255,.2); --shadow-hover-cyan:0 0 20px rgba(0,240,255,.4);
  --shadow-dropdown:0 8px 32px rgba(0,0,0,.6);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--bg-deep);color:var(--text-primary);font-family:var(--font-mono);overflow-x:hidden}
::selection{background:var(--pink);color:#fff}
a{color:inherit;text-decoration:none}

@keyframes gridScroll{0%{background-position:0 0}100%{background-position:0 60px}}
@keyframes glitchTop{0%,90%,100%{transform:translate(0)}92%{transform:translate(-2px,-1px)}94%{transform:translate(2px,1px)}96%{transform:translate(-1px,2px)}98%{transform:translate(1px,-1px)}}
@keyframes glitchBottom{0%,88%,100%{transform:translate(0)}90%{transform:translate(2px,1px)}93%{transform:translate(-2px,-2px)}95%{transform:translate(1px,2px)}97%{transform:translate(-1px,-1px)}}
@keyframes crtFlicker{0%{opacity:.9}100%{opacity:1}}
@keyframes pulse{0%,80%,100%{opacity:.3;transform:scale(.8)}40%{opacity:1;transform:scale(1.25)}}
@keyframes fadeUp{to{opacity:1;transform:translateY(0)}}

.cyber-grid{position:fixed;top:50%;left:50%;width:200vw;height:200vh;
  transform:translate(-50%,-30%) perspective(500px) rotateX(60deg);
  background:linear-gradient(var(--cyan-05) 1px,transparent 1px),linear-gradient(90deg,var(--cyan-05) 1px,transparent 1px);
  background-size:60px 60px;animation:gridScroll 20s linear infinite;z-index:0;pointer-events:none}
.jp-bg{position:fixed;writing-mode:vertical-rl;font-family:var(--font-jp);font-weight:900;font-size:4rem;
  letter-spacing:1rem;opacity:.04;color:var(--cyan);z-index:0;pointer-events:none;top:0;height:100vh;line-height:1;user-select:none}
.jp-bg.l{left:14px} .jp-bg.r{right:14px}

.wrap{position:relative;z-index:1;max-width:1024px;margin:0 auto;padding:20px 20px 90px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;
  padding:12px 0 18px;border-bottom:1px solid var(--border-structural);margin-bottom:34px}
.brand{font-family:var(--font-pixel);font-size:.6rem;color:var(--text-muted);letter-spacing:.05em;line-height:1.8}
.brand b{color:var(--cyan)} .brand i{color:var(--pink);font-style:normal}
.chips{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.chip{display:inline-flex;align-items:center;gap:7px;padding:7px 13px;border:1px solid var(--cyan-30);
  background:var(--bg-input);font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:var(--tracking-wider);
  color:var(--text-secondary);transition:all .2s ease}
.chip:hover{border-color:var(--cyan);color:var(--cyan);box-shadow:var(--shadow-glow-cyan)}
.chip .d{width:7px;height:7px;border-radius:50%;animation:pulse 1.6s ease infinite}
.chip.v{border-color:var(--border-medium);color:var(--text-faint);pointer-events:none}

.hero{margin-bottom:34px}
.kicker{font-family:var(--font-pixel);font-size:.6rem;color:var(--pink);letter-spacing:.1em;margin-bottom:16px}
.glitch{position:relative;display:inline-block;font-family:var(--font-pixel);font-size:clamp(1rem,3.4vw,1.9rem);
  color:var(--text-primary);line-height:1.35;animation:crtFlicker .18s infinite alternate}
.glitch::before,.glitch::after{content:attr(data-text);position:absolute;top:0;left:0;width:100%;height:100%;overflow:hidden}
.glitch::before{animation:glitchTop 5s linear infinite;clip-path:inset(0 0 55% 0);text-shadow:-2px 0 var(--cyan)}
.glitch::after{animation:glitchBottom 6s linear infinite;clip-path:inset(55% 0 0 0);text-shadow:2px 0 var(--pink)}
h1.ru{font-family:var(--font-mono);font-weight:700;font-size:clamp(1.15rem,2.4vw,1.7rem);line-height:1.25;
  margin:20px 0 12px;max-width:820px;letter-spacing:-.01em}
.sub{color:var(--text-secondary);font-size:.9rem;line-height:1.7;max-width:720px}
.sub b{color:var(--cyan);font-weight:700}

.sec{font-family:var(--font-mono);font-weight:700;text-transform:uppercase;letter-spacing:var(--tracking-wide);
  font-size:.9rem;display:flex;align-items:center;gap:14px;margin-bottom:18px}
.sec .tag{font-family:var(--font-pixel);font-size:.62rem;color:var(--cyan)}
.sec::after{content:'';flex:1;height:1px;background:linear-gradient(to right,var(--cyan),transparent)}
.sec.pink .tag{color:var(--pink)} .sec.pink::after{background:linear-gradient(to right,var(--pink),transparent)}
.sec.yellow .tag{color:var(--yellow)} .sec.yellow::after{background:linear-gradient(to right,var(--yellow),transparent)}

.stat-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:38px}
.stat-cell{background:var(--bg-surface-faint);border:1px solid var(--border-subtle);padding:16px 18px}
.stat-value{font-family:var(--font-mono);font-weight:700;font-size:1.5rem;line-height:1.1}
.stat-label{font-size:.68rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:var(--tracking-wide);margin-top:6px}
.c-cyan{color:var(--cyan)} .c-pink{color:var(--pink)} .c-yellow{color:var(--yellow)} .c-green{color:var(--green)}

.cyber-card{position:relative;background:var(--bg-surface);backdrop-filter:blur(5px);border:1px solid var(--cyan);
  box-shadow:var(--shadow-glow-cyan);padding:26px;margin-bottom:38px}
.cyber-card::before{content:'';position:absolute;top:-1px;left:-1px;width:20px;height:20px;border-top:2px solid var(--pink);border-left:2px solid var(--pink)}
.cyber-card::after{content:'';position:absolute;bottom:-1px;right:-1px;width:20px;height:20px;border-bottom:2px solid var(--pink);border-right:2px solid var(--pink)}
.quiet-card{background:var(--bg-surface-faint);border:1px solid var(--border-subtle);padding:22px;margin-bottom:38px}
.hint{color:var(--text-faint);font-size:.75rem;margin:-6px 0 16px;letter-spacing:.02em}

#chart{width:100%;height:auto;display:block}
.axis text{fill:var(--text-ghost);font-family:var(--font-mono);font-size:10px}
.axis line{stroke:var(--border-subtle)}
.land line{stroke:var(--text-ghost);stroke-dasharray:3 4;opacity:.5}
.land text{fill:var(--text-muted);font-family:var(--font-mono);font-size:9.5px;text-transform:uppercase;letter-spacing:.08em}
.dot{cursor:pointer;transition:opacity .12s}
.dot:hover{stroke:#fff;stroke-width:1.5}

.cyber-alert{padding:18px 22px;border-left:3px solid var(--yellow);background:var(--yellow-08);margin-bottom:38px}
.cyber-alert .alert-title{font-family:var(--font-mono);font-weight:700;text-transform:uppercase;letter-spacing:.1em;
  font-size:.8rem;color:var(--yellow);margin-bottom:10px;display:flex;align-items:center;gap:8px}
.cyber-alert p{font-size:.86rem;color:var(--text-secondary);line-height:1.7;margin-bottom:8px}
.cyber-alert p:last-child{margin-bottom:0} .cyber-alert b{color:var(--text-primary)}

.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-bottom:20px}
.cyber-input{flex:1;min-width:200px;padding:12px 15px;background:var(--bg-input);border:1px solid var(--cyan-30);
  color:var(--text-primary);font-family:var(--font-mono);font-size:.85rem;outline:none;transition:all .2s ease}
.cyber-input:focus{background:var(--bg-input-focus);border-color:var(--cyan);box-shadow:var(--shadow-glow-cyan)}
.cyber-input::placeholder{color:var(--text-muted)}
.cyber-tabs{display:flex;border-bottom:1px solid var(--border-medium)}
.cyber-tab{padding:11px 20px;font-family:var(--font-mono);font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;
  color:var(--text-secondary);border:0;border-bottom:2px solid transparent;background:none;cursor:pointer;transition:all .2s ease}
.cyber-tab:hover{color:var(--cyan);background:var(--cyan-05);border-bottom-color:var(--cyan-40)}
.cyber-tab.active{color:var(--cyan);border-bottom-color:var(--cyan)}

table{width:100%;border-collapse:collapse;font-family:var(--font-mono);font-size:.82rem}
thead th{text-align:left;padding:13px 12px;color:var(--cyan);text-transform:uppercase;font-weight:700;
  font-size:.72rem;letter-spacing:.08em;border-bottom:1px solid var(--cyan-30)}
tbody td{padding:12px;border-bottom:1px solid var(--cyan-10);color:var(--text-primary)}
tbody tr{transition:background .2s ease} tbody tr:hover{background:var(--cyan-05)}
tr.pale td{color:var(--text-faint)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.rank{width:38px;color:var(--text-ghost)}
.bar{height:7px;background:var(--cyan);box-shadow:0 0 6px var(--cyan-40)}
tr.pale .bar{background:var(--text-ghost);box-shadow:none}
.cyber-badge{display:inline-block;padding:2px 7px;font-family:var(--font-mono);font-size:.6rem;font-weight:700;
  text-transform:uppercase;letter-spacing:.1em;border:1px solid var(--yellow);color:var(--yellow)}

.method{font-size:.84rem;color:var(--text-secondary);line-height:1.75}
.method b{color:var(--text-primary)} .method p{margin-bottom:10px} .method p:last-child{margin-bottom:0}
.method .dim{color:var(--text-faint)}

.tt{position:fixed;pointer-events:none;background:var(--bg-panel);border:1px solid var(--cyan-30);
  box-shadow:var(--shadow-dropdown),0 0 14px var(--cyan-10);padding:10px 12px;font-size:.75rem;
  opacity:0;transition:opacity .1s;z-index:500;max-width:240px;font-family:var(--font-mono)}
.tt .n{color:var(--cyan);font-weight:700;font-size:.82rem;margin-bottom:3px}
.tt .m{color:var(--text-muted);font-size:.68rem}

footer{color:var(--text-faint);font-size:.72rem;margin-top:40px;line-height:1.8;
  border-top:1px solid var(--border-structural);padding-top:20px}
footer a{color:var(--text-muted)} footer a:hover{color:var(--cyan)}

.fade{opacity:0;transform:translateY(16px);animation:fadeUp .6s ease forwards}
</style>
</head>
<body>
<div class="cyber-grid"></div>
<div class="jp-bg l">スタンダップ言語解析</div>
<div class="jp-bg r">語彙の多様性コーパス</div>

<div class="wrap">
  <div class="topbar fade">
    <div class="brand"><b>NEVEZHDA</b> // <i>CHAPPELLE_POZVONIT</i></div>
    <div class="chips">
      <a class="chip" href="https://t.me/newezha" target="_blank" rel="noopener"><span class="d" style="background:var(--cyan)"></span>Невежда</a>
      <a class="chip" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener"><span class="d" style="background:var(--pink)"></span>Шаппелл позвонит</a>
      <span class="chip v">v1.0</span>
    </div>
  </div>

  <div class="hero fade" style="animation-delay:.05s">
    <div class="kicker">&gt;_ STANDUP_LEXICON // CORPUS_ANALYSIS</div>
    <span class="glitch" data-text="VOCAB.SCAN">VOCAB.SCAN</span>
    <h1 class="ru">У кого из стендап-комиков богаче словарный запас?</h1>
    <p class="sub">Корпусный анализ русскоязычного стендапа. Считаем, сколько разных лемм
      встречается в первых <b id="win"></b> словах очищенного корпуса выступлений комика.
      Чем правее на шкале — тем разнообразнее лексика.</p>
  </div>

  <div class="stat-row fade" id="tiles" style="animation-delay:.1s"></div>

  <h2 class="sec fade" style="animation-delay:.15s"><span class="tag">01</span>Шкала разнообразия лексики</h2>
  <div class="cyber-card fade" style="animation-delay:.15s">
    <p class="hint">Каждый маркер — комик. Бледные — корпус меньше <span class="winw"></span> слов
      (ниже надёжность). Наведи на маркер или найди комика ниже.</p>
    <svg id="chart"></svg>
  </div>

  <h2 class="sec yellow fade"><span class="tag">02</span>Оговорка</h2>
  <div class="cyber-alert fade">
    <div class="alert-title">&#9888; стендап не песни</div>
    <p>Идея Иноземцева — обрубать корпус на первых <b>25 000 слов</b> ради чистоты сравнения:
      так неважно, сто у тебя минут материала или тысяча, все меряются на одинаковом объёме,
      и мы смотрим на число уникальных лемм. Для песен это работает хорошо.</p>
    <p>Для концертов — хуже. Восемь тысяч уникальных лемм в песнях представить сильно проще,
      чем восемь тысяч в концерте: в стендапе много повторяющихся заходов, подводок и
      коллбэков, формулировки часто похожи, поэтому уникальных лемм набирается меньше.
      Напрямую сравнивать комиков с рэперской шкалой не стоит.</p>
    <p>Скорее всего, для стендапа мы <b>расширим окно первых слов</b>; пока просто держим
      эту разницу в голове.</p>
  </div>

  <h2 class="sec pink fade"><span class="tag">03</span>Рейтинг комиков</h2>
  <div class="quiet-card fade">
    <div class="controls">
      <input type="search" id="q" class="cyber-input" placeholder="> Найти комика..." autocomplete="off">
      <div class="cyber-tabs">
        <button class="cyber-tab active" data-sort="rating">По рейтингу</button>
        <button class="cyber-tab" data-sort="alpha">По алфавиту</button>
      </div>
    </div>
    <div style="overflow-x:auto">
    <table>
      <thead><tr>
        <th class="rank">#</th><th>Комик</th>
        <th class="num">Леммы / 25k</th><th class="num">Выст.</th><th class="num">Слов</th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
    </div>
  </div>

  <h2 class="sec fade"><span class="tag">04</span>Методология</h2>
  <div class="quiet-card method fade">
    <p>Транскрипты (субтитры) выступлений очищаются, точные повторы строк удаляются, слова
      приводятся к леммам (<b>razdel + pymorphy3</b>). Основная метрика — число уникальных
      лемм в первых <b>25 000 слов</b> очищенного корпуса. Считаем <b>только русские
      (кириллические)</b> слова. Комики с корпусом меньше 25 000 слов помечены как бледные:
      их результат менее надёжен.</p>
    <p class="dim">Ориентиры («дошкольник», «иностранец», «филолог») — грубый контекст по
      экспертным оценкам словаря, а не корпусный подсчёт. Это не оценка активного словаря человека.</p>
  </div>

  <footer>
    Проект каналов <a href="https://t.me/newezha" target="_blank">Невежда</a> и
    <a href="https://t.me/Chappellepozvonit" target="_blank">Шаппелл позвонит</a>.
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
  [fmt(META.comics),'комиков',' c-cyan'],
  [fmt(META.concerts),'выступлений',' c-green'],
  [fmt(META.words),'слов обработано',' c-cyan'],
  [META.richest?fmt(META.richest.unique_lemmas_25k):'—','богаче всех: '+(META.richest?META.richest.artist:'—'),' c-yellow'],
  [fmt(META.median),'медиана (надёжные)',' c-pink'],
];
document.getElementById('tiles').innerHTML=tiles.map(t=>
  `<div class="stat-cell"><div class="stat-value${t[2]}">${t[0]}</div><div class="stat-label">${t[1]}</div></div>`).join('');

const tt=document.getElementById('tt');
function showTT(h,x,y){tt.innerHTML=h;tt.style.opacity=1;
  tt.style.left=Math.min(x+14,window.innerWidth-250)+'px';tt.style.top=(y+14)+'px';}
function hideTT(){tt.style.opacity=0;}
const LAND=[{v:2000,t:'дошкольник'},{v:4000,t:'иностранец'},{v:9000,t:'филолог'}];

function drawChart(hl){
  const svg=document.getElementById('chart');
  const W=svg.clientWidth||960,padL=14,padR=14,padB=34,padT=24;
  const vals=DATA.map(d=>d.unique_lemmas_25k);
  const maxV=Math.max(...vals,9200),minV=Math.min(...vals,1800);
  const lo=Math.floor((minV-200)/1000)*1000,hi=Math.ceil((maxV+200)/1000)*1000;
  const x=v=>padL+(v-lo)/(hi-lo)*(W-padL-padR);
  const r=6, midY=padT+118;
  const pts=DATA.map(d=>({d,cx:x(d.unique_lemmas_25k),cy:0})).sort((a,b)=>a.cx-b.cx);
  for(const p of pts){let y=midY,dir=1,s=0;
    const hit=yy=>pts.some(q=>q!==p&&q.cy!==0&&Math.hypot(q.cx-p.cx,q.cy-yy)<r*2+1);
    while(hit(y)){s++;y=midY+dir*s*(r*1.4);dir*=-1;} p.cy=y;}
  const H=298; svg.setAttribute('viewBox',`0 0 ${W} ${H}`); svg.setAttribute('height',H);
  let s='';
  for(const l of LAND){if(l.v<lo||l.v>hi)continue;
    s+=`<g class="land"><line x1="${x(l.v)}" y1="${padT-4}" x2="${x(l.v)}" y2="${H-padB}"/>`+
       `<text x="${x(l.v)+4}" y="${padT+2}">${l.t} ~${fmt(l.v)}</text></g>`;}
  s+=`<g class="axis"><line x1="${padL}" y1="${H-padB}" x2="${W-padR}" y2="${H-padB}"/>`;
  for(let v=lo;v<=hi;v+=1000){s+=`<text x="${x(v)}" y="${H-padB+16}" text-anchor="middle">${fmt(v)}</text>`;}
  s+=`</g>`;
  for(const p of pts){
    const rel=p.d.reliable,hot=hl&&p.d.artist===hl;
    const fill=rel?(hot?'var(--yellow)':'var(--cyan)'):'none';
    const stroke=rel?'none':'var(--text-ghost)';
    const op=hl?(hot?1:.22):(rel?.9:.55);
    const glow=hot?'filter="drop-shadow(0 0 6px var(--yellow))"':(rel?'filter="drop-shadow(0 0 3px var(--cyan-40))"':'');
    s+=`<circle class="dot" data-a="${encodeURIComponent(p.d.artist)}" cx="${p.cx}" cy="${p.cy}" r="${hot?r+2:r}" `+
       `fill="${fill}" stroke="${stroke}" stroke-width="1.5" opacity="${op}" ${glow}/>`;}
  svg.innerHTML=s;
  svg.querySelectorAll('.dot').forEach(c=>{
    c.addEventListener('mousemove',e=>{const d=DATA.find(x=>x.artist===decodeURIComponent(c.dataset.a));
      showTT(`<div class="n">${d.artist}</div><div>${fmt(d.unique_lemmas_25k)} лемм / 25k</div>`+
        `<div class="m">${d.concerts} выст. · ${fmt(d.total_words)} слов`+(d.reliable?'':' · бледный')+`</div>`,e.clientX,e.clientY);});
    c.addEventListener('mouseleave',hideTT);});
}

let sortMode='rating';
function firstMatch(q){q=q.trim().toLowerCase();const m=DATA.find(d=>d.artist.toLowerCase().includes(q));return m?m.artist:null;}
function drawTable(filter){
  let rows=DATA.slice();
  if(sortMode==='alpha')rows.sort((a,b)=>a.artist.localeCompare(b.artist,'ru'));
  else rows.sort((a,b)=>b.unique_lemmas_25k-a.unique_lemmas_25k);
  const f=(filter||'').trim().toLowerCase();
  if(f)rows=rows.filter(r=>r.artist.toLowerCase().includes(f));
  const maxL=Math.max(...DATA.map(d=>d.unique_lemmas_25k));
  document.getElementById('rows').innerHTML=rows.map((r,i)=>{
    const w=Math.round(r.unique_lemmas_25k/maxL*84);
    return `<tr class="${r.reliable?'':'pale'}" data-a="${encodeURIComponent(r.artist)}">`+
      `<td class="rank">${sortMode==='rating'?i+1:''}</td>`+
      `<td>${r.artist} ${r.reliable?'':'<span class="cyber-badge">&lt;25k</span>'}</td>`+
      `<td class="num"><div style="display:flex;align-items:center;gap:8px;justify-content:flex-end">`+
        `<div class="bar" style="width:${w}px"></div><span>${fmt(r.unique_lemmas_25k)}</span></div></td>`+
      `<td class="num">${r.concerts}</td><td class="num">${fmt(r.total_words)}</td></tr>`;}).join('');
  document.querySelectorAll('#rows tr').forEach(tr=>{
    tr.addEventListener('mouseenter',()=>drawChart(decodeURIComponent(tr.dataset.a)));
    tr.addEventListener('mouseleave',()=>drawChart(firstMatch(document.getElementById('q').value)));});
}
document.getElementById('q').addEventListener('input',e=>{drawTable(e.target.value);drawChart(firstMatch(e.target.value));});
document.querySelectorAll('.cyber-tab').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.cyber-tab').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');sortMode=b.dataset.sort;drawTable(document.getElementById('q').value);}));

drawChart(null);drawTable('');
window.addEventListener('resize',()=>drawChart(firstMatch(document.getElementById('q').value)));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
