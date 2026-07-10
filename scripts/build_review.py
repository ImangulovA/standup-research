"""Render expansion/candidates.json into a self-contained review page.

The page lets you curate discovered concerts BEFORE they enter the corpus:
each candidate shows the monologue/conversation verdict (markers/min), its
duration, channel and a YouTube link. You approve or reject each one; the
detector's verdict is the default. Decisions persist in localStorage, and an
"Export approved" button copies a JSON list you feed back to the ingest step.

Comics are grouped and annotated with how many words they still need to reach
the 25k reliability threshold, so you can prioritise.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXP = ROOT / "expansion"
CAND = EXP / "candidates.json"
REVIEWED = EXP / "reviewed.json"     # video_ids already curated by a human
REPORT = ROOT / "report.json"
OUT = EXP / "review.html"

THRESHOLD = 25000


def main():
    cand = json.loads(CAND.read_text())
    report = {r["artist"]: r for r in json.loads(REPORT.read_text())}
    reviewed = set(json.loads(REVIEWED.read_text())) if REVIEWED.exists() else set()

    by_artist = {}
    for c in cand.values():
        if c["video_id"] in reviewed:
            continue  # already handled in an earlier review session
        by_artist.setdefault(c["artist"], []).append(c)

    groups = []
    for artist in sorted(by_artist):
        items = sorted(by_artist[artist],
                       key=lambda c: (c["verdict"] != "keep",
                                      c.get("markers_per_min") or 0))
        words = report.get(artist, {}).get("total_words", 0)
        need = max(0, THRESHOLD - words)
        groups.append({"artist": artist, "words": words, "need": need,
                       "reliable": words >= THRESHOLD, "items": items})
    groups.sort(key=lambda g: (g["reliable"], g["need"]))

    payload = json.dumps(groups, ensure_ascii=False)
    html = _TEMPLATE.replace("__DATA__", payload)
    OUT.write_text(html, encoding="utf-8")
    n = sum(len(g["items"]) for g in groups)
    print(f"wrote {OUT}  ({len(groups)} comics, {n} candidates)")


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stand-up Research — ревью новых концертов</title>
<style>
:root{--bg:#f4efe6;--ink:#1a1a1a;--line:#1a1a1a;--keep:#2e7d32;--review:#c77d00;
--reject:#b23b3b;--indigo:#3b3bb2;--card:#fffdf8;--chip:#ffe066;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:24px}
h1{margin:0 0 4px;font-size:28px}
.sub{color:#555;margin-bottom:18px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:12px 0;
border-bottom:3px solid var(--line);display:flex;gap:10px;flex-wrap:wrap;align-items:center}
button{font:inherit;font-weight:700;padding:8px 14px;border:2px solid var(--line);
background:var(--chip);border-radius:10px;cursor:pointer;box-shadow:3px 3px 0 var(--line)}
button:active{transform:translate(2px,2px);box-shadow:1px 1px 0 var(--line)}
.counts{margin-left:auto;font-weight:700}
.filters label{margin-right:10px;font-size:14px}
.comic{border:3px solid var(--line);border-radius:14px;background:var(--card);
margin:16px 0;padding:14px;box-shadow:5px 5px 0 var(--line)}
.comic h2{margin:0 0 2px;font-size:20px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.need{font-size:13px;font-weight:700;padding:2px 8px;border:2px solid var(--line);border-radius:20px}
.need.ok{background:#cdeccd}.need.gap{background:#ffe0b3}
.row{display:flex;gap:10px;align-items:center;padding:8px 6px;border-top:1px dashed #bbb}
.row:first-of-type{border-top:none}
.v{font-size:12px;font-weight:800;padding:2px 8px;border-radius:8px;border:2px solid var(--line);min-width:64px;text-align:center}
.v.keep{background:#cdeccd;color:var(--keep)}
.v.review{background:#ffe7bf;color:var(--review)}
.v.reject{background:#f4cccc;color:var(--reject)}
.meta{flex:1;min-width:0}
.meta .t{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.meta .m{font-size:12px;color:#666}
.mpm{font-variant-numeric:tabular-nums;font-weight:700;min-width:70px;text-align:right}
a{color:var(--indigo)}
.dec{display:flex;gap:4px}
.dec button{padding:4px 10px;box-shadow:none;background:#eee;font-size:13px}
.dec button.on-approve{background:var(--keep);color:#fff;border-color:var(--keep)}
.dec button.on-reject{background:var(--reject);color:#fff;border-color:var(--reject)}
.hidden{display:none}
dialog{border:3px solid var(--line);border-radius:14px;max-width:640px;width:90%}
textarea{width:100%;height:260px;font:13px/1.4 monospace}
</style></head>
<body>
<h1>Ревью новых концертов</h1>
<div class="sub">Детектор монолог/разговор по маркерам смены говорящего (<b>&gt;&gt;</b> в авто-субтитрах).
Порог: ≤5/мин концерт, 5–15 ревью, &gt;15 разговор. Решение можно переопределить вручную.</div>

<div class="bar">
  <button onclick="setAll('approve')">✓ Принять все «keep»</button>
  <button onclick="setAll('reject')">✗ Отклонить все «reject»</button>
  <span class="filters">
    <label><input type="checkbox" id="f-keep" checked onchange="render()"> keep</label>
    <label><input type="checkbox" id="f-review" checked onchange="render()"> review</label>
    <label><input type="checkbox" id="f-reject" onchange="render()"> reject</label>
  </span>
  <button onclick="exportApproved()">⬇ Экспорт принятых</button>
  <span class="counts" id="counts"></span>
</div>

<div id="list"></div>

<dialog id="dlg">
  <h3>Экспорт отбора</h3>
  <p><b>approved</b> — принятые концерты (в <code>expansion/approved.json</code>);
     <b>reviewed</b> — все разобранные id (в <code>expansion/reviewed.json</code>,
     чтобы не всплывали снова). Отдай оба Клоду или сохрани файлами.</p>
  <textarea id="dlg-txt" readonly></textarea>
  <div style="margin-top:10px;display:flex;gap:8px">
    <button onclick="copyTxt()">Копировать</button>
    <button onclick="dlg.close()">Закрыть</button>
  </div>
</dialog>

<script>
const DATA = __DATA__;
const KEY = "standup_review_decisions_v2";
let decisions = JSON.parse(localStorage.getItem(KEY) || "{}");

function save(){ localStorage.setItem(KEY, JSON.stringify(decisions)); }
function decisionFor(c){
  if(decisions[c.video_id]) return decisions[c.video_id];
  return "reject";  // default everything to reject: click ✓ only on keepers
}
function setDecision(id, d){ decisions[id]=d; save(); render(); }
function setAll(kind){
  const target = kind==="approve" ? "keep" : "reject";
  for(const g of DATA) for(const c of g.items)
    if(c.verdict===target) decisions[c.video_id] = (kind==="approve"?"approve":"reject");
  save(); render();
}
function fmtDur(s){ if(!s) return "?"; const m=Math.floor(s/60); return m+"м"; }

function render(){
  const show = {keep:f("f-keep"),review:f("f-review"),reject:f("f-reject")};
  const list = document.getElementById("list"); list.innerHTML="";
  let approved=0, total=0;
  for(const g of DATA){
    const vis = g.items.filter(c=>show[c.verdict]);
    if(!vis.length) continue;
    const div=document.createElement("div"); div.className="comic";
    const needCls = g.reliable ? "ok":"gap";
    const needTxt = g.reliable ? "надёжный ("+g.words.toLocaleString("ru")+" слов)"
                               : "нужно +"+g.need.toLocaleString("ru")+" слов до 25k";
    div.innerHTML=`<h2>${g.artist}<span class="need ${needCls}">${needTxt}</span></h2>`;
    for(const c of vis){
      total++;
      const d=decisionFor(c); if(d==="approve") approved++;
      const row=document.createElement("div"); row.className="row";
      row.innerHTML=`
        <span class="v ${c.verdict}">${c.verdict}</span>
        <span class="mpm">${c.markers_per_min==null?"—":c.markers_per_min+"/м"}</span>
        <div class="meta">
          <div class="t">${esc(c.title)}</div>
          <div class="m">${fmtDur(c.duration_sec)} · ${esc(c.channel||"")} ${c.reasons&&c.reasons.length?"· "+esc(c.reasons.join(", ")):""}
            · <a href="https://youtu.be/${c.video_id}" target="_blank">открыть</a></div>
        </div>
        <div class="dec">
          <button class="${d==='approve'?'on-approve':''}" onclick="setDecision('${c.video_id}','approve')">✓</button>
          <button class="${d==='reject'?'on-reject':''}" onclick="setDecision('${c.video_id}','reject')">✗</button>
        </div>`;
      div.appendChild(row);
    }
    list.appendChild(div);
  }
  document.getElementById("counts").textContent = `принято ${approved} / показано ${total}`;
}
function f(id){ return document.getElementById(id).checked; }
function esc(s){ return (s||"").replace(/[&<>"]/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m])); }

const dlg=document.getElementById("dlg");
function exportApproved(){
  const approved=[], reviewed=[];
  for(const g of DATA) for(const c of g.items){
    const d=decisionFor(c);
    if(d==="approve"){ approved.push({video_id:c.video_id, artist:c.artist, title:c.title}); reviewed.push(c.video_id); }
    else if(d==="reject"){ reviewed.push(c.video_id); }
  }
  document.getElementById("dlg-txt").value=JSON.stringify({approved, reviewed}, null, 2);
  dlg.showModal();
}
function copyTxt(){ const t=document.getElementById("dlg-txt"); t.select(); document.execCommand("copy"); }
render();
</script>
</body></html>
"""

if __name__ == "__main__":
    main()
