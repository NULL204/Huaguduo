#!/usr/bin/env python3
"""nai_sheet.py -- turn assets/nai/jobs.jsonl into assets/nai/sheet.html, a local page for generating the images by
hand on novelai.net (the trial key needs the site's reCAPTCHA, so the API cannot run these jobs).

Each job becomes a card: what it is for, size / seed / steps / guidance, the prompt and the negative prompt with copy
buttons, and a "done" tick (remembered in the browser). Save every image into assets/nai_raw/ -- no renaming needed,
tools/nai_import.py matches files to jobs by the seed NovelAI writes into the PNG.

  python tools/nai_sheet.py                 # all batches
  python tools/nai_sheet.py --batch 1       # only batch 1
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "assets" / "nai" / "jobs.jsonl"
OUT = ROOT / "assets" / "nai" / "sheet.html"
RAW = ROOT / "assets" / "nai_raw"

CSS = """
:root{--ink:#1A1D26;--muted:#5d6675;--line:#d9e1ea;--paper:#f6f8fb;--card:#fff;--car:#C8183C;--ice:#D7E3EE}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 18px 60px}
h1{font-size:24px;margin:0 0 4px;letter-spacing:.02em}h1 span{color:var(--car)}
.sub{color:var(--muted);margin:0 0 20px}
.box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:0 0 18px}
.box h2{font-size:15px;margin:0 0 10px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.settings{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:6px 18px}
.settings b{display:inline-block;min-width:112px;color:var(--muted);font-weight:500}
.path{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.path code{background:var(--paper);border:1px solid var(--line);
padding:6px 10px;border-radius:6px;font-size:13px;word-break:break-all;flex:1}
.card{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--ice);border-radius:10px;padding:16px 18px;margin:0 0 16px}
.card.done{border-left-color:var(--car);opacity:.62}
.head{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap}
.head h3{margin:0;font-size:18px}.head h3 small{color:var(--muted);font-weight:400;font-size:13px;margin-left:8px}
.note{margin:4px 0 10px;color:var(--muted)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 10px}.chip{background:var(--paper);border:1px solid var(--line);border-radius:99px;
padding:2px 10px;font-size:13px}.chip b{color:var(--car);font-weight:600}
label.f{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:10px 0 4px}
.row{display:flex;gap:8px;align-items:stretch}textarea{flex:1;min-height:92px;resize:vertical;font:13px/1.45 ui-monospace,Consolas,monospace;
border:1px solid var(--line);border-radius:6px;padding:8px;background:#fbfcfe;color:var(--ink)}
button{border:1px solid var(--ink);background:var(--ink);color:#fff;border-radius:6px;padding:0 14px;font:600 13px system-ui,sans-serif;cursor:pointer;min-width:84px}
button.ok{background:var(--car);border-color:var(--car)}.tick{display:flex;gap:6px;align-items:center;font-size:14px;color:var(--muted);cursor:pointer}
.batch{font-size:14px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin:26px 0 10px}
@media (max-width:560px){.row{flex-direction:column}button{min-height:36px}}
"""

JS = """
function copyText(id, btn){const t=document.getElementById(id);const v=t.value;
 const done=()=>{const o=btn.textContent;btn.textContent='Copied';btn.classList.add('ok');setTimeout(()=>{btn.textContent=o;btn.classList.remove('ok')},1100)};
 if(navigator.clipboard&&window.isSecureContext!==false){navigator.clipboard.writeText(v).then(done,()=>{t.select();document.execCommand('copy');done()})}
 else{t.select();document.execCommand('copy');done()}}
function key(id){return 'hgd-nai-done-'+id}
function setDone(id,on){const c=document.getElementById('card-'+id);if(c)c.classList.toggle('done',on);try{localStorage.setItem(key(id),on?'1':'')}catch(e){}}
window.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('input[data-job]').forEach(cb=>{let on=false;
 try{on=localStorage.getItem(key(cb.dataset.job))==='1'}catch(e){} cb.checked=on;setDone(cb.dataset.job,on);
 cb.addEventListener('change',()=>setDone(cb.dataset.job,cb.checked))})});
"""


def card(j: dict) -> str:
    e = html.escape
    orient = "portrait" if j["height"] > j["width"] else "landscape"
    kind = "cut-out (green background)" if j.get("cutout") else "full frame"
    return f"""
<section class="card" id="card-{e(j['id'])}">
  <div class="head"><h3>{e(j['id'])}<small>{e(kind)}</small></h3>
    <label class="tick"><input type="checkbox" data-job="{e(j['id'])}"> done</label></div>
  <p class="note">{e(j.get('note', ''))}</p>
  <div class="chips"><span class="chip">size <b>{j['width']}×{j['height']}</b> ({orient})</span>
    <span class="chip">seed <b>{j['seed']}</b></span><span class="chip">steps <b>{j.get('steps', 28)}</b></span>
    <span class="chip">guidance <b>{j.get('scale', 5.5)}</b></span></div>
  <label class="f" for="p-{e(j['id'])}">Prompt</label>
  <div class="row"><textarea id="p-{e(j['id'])}" readonly>{e(j['prompt'])}</textarea>
    <button onclick="copyText('p-{e(j['id'])}',this)">Copy</button></div>
  <label class="f" for="n-{e(j['id'])}">Undesired content (negative)</label>
  <div class="row"><textarea id="n-{e(j['id'])}" readonly>{e(j.get('negative', ''))}</textarea>
    <button onclick="copyText('n-{e(j['id'])}',this)">Copy</button></div>
</section>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=0)
    a = ap.parse_args()
    jobs = [json.loads(l) for l in JOBS.read_text(encoding="utf-8").splitlines() if l.strip()]
    if a.batch:
        jobs = [j for j in jobs if j.get("batch") == a.batch]
    batches: dict[int, list[dict]] = {}
    for j in jobs:
        batches.setdefault(j.get("batch", 0), []).append(j)
    raw = str(RAW).replace("/", "\\")
    body = "".join(f'<div class="batch">Batch {b} · {len(js)} image{"s" if len(js) != 1 else ""}</div>' + "".join(card(j) for j in js)
                   for b, js in sorted(batches.items()))
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>花骨朵 · NovelAI prompt sheet</title><style>{CSS}</style></head><body><main>
<h1>花骨朵 <span>·</span> NovelAI prompt sheet</h1>
<p class="sub">Generate each card once on novelai.net, then tick it. {len(jobs)} image{"s" if len(jobs) != 1 else ""} on this sheet; 30 in the whole budget.</p>
<div class="box"><h2>Settings for every card</h2><div class="settings">
<div><b>Model</b> NAI Diffusion V4.5 Full</div><div><b>Steps</b> 28 (or the default if locked)</div>
<div><b>Prompt guidance</b> 5.5</div><div><b>Sampler</b> Euler Ancestral</div><div><b>Noise schedule</b> karras</div>
<div><b>Quality tags</b> on</div><div><b>UC preset</b> Heavy</div><div><b>Images per run</b> 1</div>
<div><b>Seed</b> the card's seed</div><div><b>Size</b> the card's width × height</div></div></div>
<div class="box"><h2>Save the images here (no renaming needed)</h2><div class="path"><code id="rawpath">{html.escape(raw)}</code>
<button onclick="copyText2()">Copy</button></div></div>
{body}
</main><textarea id="rawpath-t" style="position:absolute;left:-9999px">{html.escape(raw)}</textarea>
<script>{JS}
function copyText2(){{copyText('rawpath-t', event.target)}}</script></body></html>"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(jobs)} jobs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
