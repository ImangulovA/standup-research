"""Build the "manually added concerts" page (docs/added.html) from
expansion/approved.json.

These are performances that were NOT in Ilya Yakyamsev's smeshno.xyz list: the
neural net suggested extra videos, and we hand-picked the ones that fit the study
(short sets and stories — yes; podcasts and streams — no). This page just lists
them, grouped by comic, each linking to the source video on YouTube.

Only public metadata is embedded (comic, title, YouTube id) — no transcripts.
Design mirrors docs/index.html (light neobrutalism).
"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
APPROVED = ROOT / "expansion" / "approved.json"


def main():
    items = json.loads(APPROVED.read_text(encoding="utf-8"))

    by_artist = defaultdict(list)
    for it in items:
        by_artist[it["artist"]].append(it)

    # artists alphabetically; within an artist, keep source order
    groups = sorted(by_artist.items(), key=lambda kv: kv[0].casefold())

    meta = {
        "performances": len(items),
        "artists": len(by_artist),
    }

    payload = [
        {"artist": a, "items": [{"video_id": x["video_id"], "title": x["title"]} for x in its]}
        for a, its in groups
    ]

    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    html = html.replace("__META__", json.dumps(meta, ensure_ascii=False))

    DOCS.mkdir(exist_ok=True)
    (DOCS / "added.html").write_text(html, encoding="utf-8")
    print(f"wrote {DOCS/'added.html'}  ({len(html):,} bytes)")
    print(f"performances={meta['performances']} artists={meta['artists']}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Концерты, добавленные вручную — Словарный запас стендап-комиков</title>
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
.chip.nav{background:var(--secondary-soft);color:var(--ink)}
.chip .d{width:9px;height:9px;border-radius:50%;border:1.5px solid var(--ink)}

header h1{font-size:clamp(24px,4.2vw,40px);line-height:1.06;font-weight:900;letter-spacing:-.02em;margin:0 0 14px;max-width:900px}
header h1 mark{background:var(--primary);padding:0 8px;border:var(--bd2);border-radius:8px;box-shadow:var(--sh-sm)}
.sub{color:var(--muted);font-size:16px;line-height:1.55;max-width:760px;font-weight:500}
.sub b{color:var(--ink);background:var(--primary-soft);padding:0 5px;border-radius:5px}

.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin:28px 0 34px}
.tile{border:var(--bd);border-radius:var(--r);padding:16px 18px;box-shadow:var(--sh)}
.tile .n{font-family:var(--mono);font-size:30px;font-weight:700;line-height:1;letter-spacing:-.02em}
.tile .l{font-size:12.5px;font-weight:700;margin-top:8px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}
.tile.t1{background:var(--primary)} .tile.t1 .l{color:#7a5c00}
.tile.t2{background:var(--secondary);color:#fff} .tile.t2 .n,.tile.t2 .l{color:#fff}

.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:stretch;margin:0 0 22px}
.search{flex:1;min-width:210px;padding:12px 15px;border:var(--bd2);border-radius:10px;background:var(--paper);
  font-family:var(--font);font-weight:600;font-size:15px;color:var(--ink);outline:none;box-shadow:var(--sh-sm)}
.search:focus{box-shadow:var(--sh)} .search::placeholder{color:var(--faint)}

.grp{background:var(--paper);border:var(--bd);border-radius:var(--r);padding:18px 20px;box-shadow:var(--sh);margin-bottom:18px}
.grp h2{font-size:18px;font-weight:900;letter-spacing:-.01em;display:flex;align-items:center;gap:10px;margin-bottom:12px}
.grp .cnt{font-family:var(--mono);font-size:12px;font-weight:700;color:var(--muted);background:var(--secondary-soft);
  border:1.5px solid var(--ink);border-radius:999px;padding:1px 9px}
.plist{list-style:none;display:flex;flex-direction:column;gap:2px}
.plist li{border-top:2px solid #eceae4}
.plist li:first-child{border-top:0}
.plink{display:flex;align-items:center;gap:10px;padding:9px 6px;text-decoration:none;font-weight:600;
  font-size:14.5px;color:var(--ink);border-radius:8px}
.plink:hover{background:var(--primary-soft)}
.plink .yt{flex:0 0 auto;font-family:var(--mono);font-size:10px;font-weight:800;color:var(--danger);
  border:1.5px solid var(--danger);border-radius:5px;padding:1px 6px}
.plink .t{flex:1}
.plink .ext{color:var(--faint);font-size:13px}
.empty{color:var(--faint);font-weight:700;padding:20px 4px;font-size:15px}

.callout{background:var(--primary);border:var(--bd);border-radius:var(--r);padding:20px 24px;box-shadow:var(--sh);margin:34px 0 8px}
.callout h3{font-size:17px;font-weight:900;margin-bottom:8px;display:flex;align-items:center;gap:10px}
.callout p{font-size:15px;line-height:1.6;font-weight:500}
.callout a{font-weight:800;color:var(--ink);background:#fff;padding:1px 6px;border-radius:5px;border:1.5px solid var(--ink);text-decoration:none}

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
      <a class="chip nav" href="index.html">← Рейтинг</a>
      <a class="chip nav" href="similar.html">Похожие →</a>
      <a class="chip nav" href="phrases.html">Обороты →</a>
      <a class="chip c1" href="https://t.me/newezha" target="_blank" rel="noopener"><span class="d"></span>Невежда</a>
    </div>
  </div>

  <header class="pop" style="animation-delay:.05s">
    <h1>Концерты, добавленные <mark>вручную</mark></h1>
    <p class="sub">Помимо списка с сайта Ильи Якямсева, нейросеть предложила ещё несколько видео
      стендап-комиков. Из них мы <b>вручную отобрали</b> те, что подходят для исследования:
      небольшие выступления и истории — да, подкасты и стримы — нет. Вот полный список.
      Каждая строка ведёт на источник на YouTube.</p>
  </header>

  <div class="tiles pop" id="tiles" style="animation-delay:.1s"></div>

  <div class="controls pop" style="animation-delay:.12s">
    <input type="search" id="q" class="search" placeholder="Найти комика или концерт…" autocomplete="off">
  </div>

  <div id="list" class="pop" style="animation-delay:.14s"></div>

  <div class="callout pop" style="animation-delay:.16s">
    <h3>&#9993;&#65039; ваш концерт в списке?</h3>
    <p>Хотите, чтобы мы добавили или убрали ваш концерт на ютьюбе из списка?
      <a href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener">Напишите нам в телеграме!</a></p>
  </div>

  <footer class="pop">
    Проект каналов <a class="f1" href="https://t.me/newezha" target="_blank" rel="noopener">Невежда</a>
    и <a class="f2" href="https://t.me/Chappellepozvonit" target="_blank" rel="noopener">Шаппелл позвонит</a>.<br>
    Базовый каталог концертов: <a class="plain" href="https://smeshno.xyz/youtube/full/" target="_blank" rel="noopener">смешно.xyz</a> (Илья Якямсев).
    На этой странице — только дополнения, отобранные вручную поверх него.
  </footer>
</div>

<script>
const DATA=__DATA__, META=__META__;
const fmt=n=>n.toLocaleString('ru-RU');

const tiles=[
  [fmt(META.performances),'концертов вручную','t1'],
  [fmt(META.artists),'комиков','t2'],
];
document.getElementById('tiles').innerHTML=tiles.map(t=>
  `<div class="tile ${t[2]}"><div class="n">${t[0]}</div><div class="l">${t[1]}</div></div>`).join('');

function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function render(filter){
  const f=(filter||'').trim().toLowerCase();
  let shown=0;
  const html=DATA.map(g=>{
    const artistHit=g.artist.toLowerCase().includes(f);
    const items=f&&!artistHit?g.items.filter(x=>x.title.toLowerCase().includes(f)):g.items;
    if(!items.length) return '';
    shown+=items.length;
    const lis=items.map(x=>
      `<li><a class="plink" href="https://www.youtube.com/watch?v=${encodeURIComponent(x.video_id)}" `+
      `target="_blank" rel="noopener"><span class="yt">▶ YT</span>`+
      `<span class="t">${esc(x.title)}</span><span class="ext">↗</span></a></li>`).join('');
    return `<div class="grp"><h2>${esc(g.artist)} <span class="cnt">${items.length}</span></h2>`+
      `<ul class="plist">${lis}</ul></div>`;
  }).join('');
  document.getElementById('list').innerHTML=html||`<div class="empty">Ничего не найдено.</div>`;
}
document.getElementById('q').addEventListener('input',e=>render(e.target.value));
render('');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
