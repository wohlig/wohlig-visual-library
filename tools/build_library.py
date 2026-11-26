#!/usr/bin/env python3
"""Rebuild catalog.json, thumbnails and index.html for the Wohlig visual library.

Run from anywhere:  python3 tools/build_library.py
- Every image under the category folders is picked up.
- Metadata (prompt, source, tags) is kept from catalog.json when an entry already exists;
  new files get an entry with tags inferred from the folder and file name.
"""
import json, os, re, html
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = ['heroes', 'illustrations', 'backgrounds', 'motifs', 'photography', 'objects',
        'icons', 'icon-sets', 'ui-mockups', 'brand', 'client-logos', 'slide-bookends']
LABEL = {
    'heroes': 'Hero art', 'illustrations': 'Illustrations', 'backgrounds': 'Backgrounds',
    'motifs': 'Motifs', 'photography': 'Photography', 'objects': 'Objects',
    'icons': 'Icons', 'icon-sets': 'Icon sheets', 'ui-mockups': 'UI mockups',
    'brand': 'Brand', 'client-logos': 'Client logos', 'slide-bookends': 'Slide bookends',
}
USE = {
    'heroes': 'Full-bleed or half-bleed slide art, covers, section dividers, web banners.',
    'illustrations': 'Scene illustrations for concepts, industries, services and case studies.',
    'backgrounds': 'Quiet textures and gradients behind text: slides, docs, video-call backgrounds.',
    'motifs': 'Line motifs (flower, arches, dot grid) for corners, watermarks and dividers.',
    'photography': 'Warm photographic scenes and still lifes for people, places and metaphors.',
    'objects': 'Single photographic objects on cream, for cards and callouts.',
    'icons': 'Transparent PNG papercraft icons for cards, lists and diagrams.',
    'icon-sets': 'Original sprite sheets the sliced tile icons came from.',
    'ui-mockups': 'Illustrative product screens for the Wohlig AI platform (sample data).',
    'brand': 'Wohlig logos, partner badges and brand mockups.',
    'client-logos': 'Client logos for case studies only (third-party trademarks).',
    'slide-bookends': 'Artwork used by the standard Wohlig intro and closing slides.',
}
EXT = ('.png', '.jpg', '.jpeg', '.webp')

def tags_for(path):
    words = re.findall(r'[a-z]+', os.path.basename(path).lower().rsplit('.', 1)[0])
    stop = {'png', 'jpg', 'the', 'and', 'with', 'tile', 'icon'}
    return sorted({w for w in words if len(w) > 2 and w not in stop})

def main():
    old = {}
    cp = os.path.join(ROOT, 'catalog.json')
    if os.path.exists(cp):
        for e in json.load(open(cp)):
            old[e['file']] = e
    os.makedirs(os.path.join(ROOT, 'thumbs'), exist_ok=True)
    items = []
    for cat in CATS:
        base = os.path.join(ROOT, cat)
        if not os.path.isdir(base):
            continue
        for dp, _, fs in os.walk(base):
            for f in sorted(fs):
                if not f.lower().endswith(EXT):
                    continue
                rel = os.path.relpath(os.path.join(dp, f), ROOT)
                im = Image.open(os.path.join(ROOT, rel))
                e = dict(old.get(rel, {}))
                e.update(file=rel, category=cat, id=e.get('id') or f.rsplit('.', 1)[0],
                         width=im.width, height=im.height,
                         transparent=im.mode in ('RGBA', 'LA'),
                         tags=sorted(set(e.get('tags', [])) | set(tags_for(rel))))
                sub = os.path.relpath(dp, base)
                if sub != '.':
                    e['subcategory'] = sub
                th = os.path.join('thumbs', rel.replace('/', '__').rsplit('.', 1)[0] + ('.png' if e['transparent'] else '.jpg'))
                tp = os.path.join(ROOT, th)
                if not os.path.exists(tp) or os.path.getmtime(tp) < os.path.getmtime(os.path.join(ROOT, rel)):
                    t = im.copy()
                    t.thumbnail((480, 480))
                    (t if e['transparent'] else t.convert('RGB')).save(tp, **({} if e['transparent'] else {'quality': 82}))
                e['thumb'] = th
                items.append(e)
    # drop thumbnails whose source image no longer exists
    keep = {e['thumb'] for e in items}
    for f in os.listdir(os.path.join(ROOT, 'thumbs')):
        if os.path.join('thumbs', f) not in keep:
            os.remove(os.path.join(ROOT, 'thumbs', f))
    json.dump(items, open(cp, 'w'), indent=1, ensure_ascii=False)
    write_gallery(items)
    counts = {}
    for e in items:
        counts[e['category']] = counts.get(e['category'], 0) + 1
    print(len(items), 'assets', counts)

def write_gallery(items):
    data = [{k: e.get(k) for k in ('id', 'file', 'thumb', 'category', 'subcategory', 'width', 'height', 'transparent', 'tags', 'prompt', 'source')} for e in items]
    cats = [c for c in CATS if any(e['category'] == c for e in items)]
    chips = ''.join(f'<button class="chip" data-cat="{c}">{LABEL[c]} <span>{sum(1 for e in items if e["category"] == c)}</span></button>' for c in cats)
    page = TEMPLATE.replace('__CHIPS__', chips).replace('__COUNT__', str(len(items))).replace(
        '__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')).replace(
        '__USE__', json.dumps(USE)).replace('__LABEL__', json.dumps(LABEL))
    open(os.path.join(ROOT, 'index.html'), 'w').write(page)

TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wohlig Visual Library</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@600;700&family=Lato:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{--maroon:#800d35;--orange:#f7781d;--terracotta:#c85f44;--tt:#b4523a;--olive:#76775a;--beige:#ead9c2;--paper:#fff7e9;--sand:#f4e8d6;--card:#fbf1e2;--ink:#2b1a1e;--body:#5b4a47;--muted:#7a6560;--hair:#e6d6c1}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--body);font:16px/1.5 Lato,Arial,sans-serif}
header{padding:40px 24px 16px;max-width:1400px;margin:auto}
h1{font:700 44px/1.1 'Source Serif 4',Georgia,serif;color:var(--maroon);margin:0}
.eyebrow{font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--tt);font-size:13px;margin:0 0 8px}
.lead{max-width:760px;margin:12px 0 0}
.bar{position:sticky;top:0;background:var(--paper);z-index:5;border-bottom:1px solid var(--hair)}
.bar>div{max-width:1400px;margin:auto;padding:12px 24px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
input{flex:1 1 220px;min-width:180px;padding:10px 14px;border:1px solid var(--hair);border-radius:999px;background:var(--card);font:inherit;color:var(--ink)}
.chip{border:1px solid var(--hair);background:var(--card);color:var(--maroon);border-radius:999px;padding:8px 14px;font:700 14px Lato,sans-serif;cursor:pointer}
.chip span{color:var(--muted);font-weight:400}.chip.on{background:var(--maroon);color:var(--paper);border-color:var(--maroon)}.chip.on span{color:#f3d9c8}
.note{max-width:1400px;margin:8px auto 0;padding:0 24px;color:var(--muted);font-size:14px}
main{max-width:1400px;margin:auto;padding:16px 24px 64px;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px}
.tile{background:var(--card);border-radius:14px;overflow:hidden;box-shadow:0 2px 6px rgba(94,10,39,.06);cursor:pointer;border:1px solid var(--hair)}
.tile .im{aspect-ratio:16/10;display:flex;align-items:center;justify-content:center;background:var(--sand)}
.tile.tr .im{background:repeating-conic-gradient(#f4e8d6 0 25%,#fbf1e2 0 50%) 0 0/20px 20px}
.tile img{width:100%;height:100%;object-fit:cover}.tile.tr img,.tile.logo img{object-fit:contain;padding:10px}
.tile p{margin:0;padding:8px 12px 10px;font-size:13px;color:var(--ink);overflow-wrap:anywhere}
.tile small{display:block;color:var(--muted)}
dialog{border:none;border-radius:18px;padding:0;max-width:min(1100px,94vw);background:var(--paper);box-shadow:0 30px 80px rgba(43,26,30,.35)}
dialog::backdrop{background:rgba(43,26,30,.55)}
.dv{display:grid;grid-template-columns:minmax(0,2fr) minmax(260px,1fr)}
.dv .big{background:var(--sand);display:flex;align-items:center;justify-content:center;min-height:320px}
.dv .big img{max-width:100%;max-height:78vh;display:block}
.dv .meta{padding:22px;overflow:auto;max-height:80vh}
.dv h2{font:700 22px/1.2 'Source Serif 4',serif;color:var(--maroon);margin:0 0 6px;overflow-wrap:anywhere}
.dv code{background:var(--card);padding:2px 6px;border-radius:6px;font-size:13px;overflow-wrap:anywhere}
.btn{display:inline-block;margin:10px 8px 0 0;padding:9px 14px;border-radius:10px;border:none;background:var(--maroon);color:var(--paper);font:700 14px Lato;cursor:pointer;text-decoration:none}
.btn.alt{background:var(--beige);color:var(--maroon)}
.prompt{font-size:13px;color:var(--muted);white-space:pre-wrap}
@media (max-width:760px){.dv{grid-template-columns:1fr}h1{font-size:34px}}
</style></head><body>
<header><p class="eyebrow">Wohlig Earthy Brand System 2026</p><h1>Wohlig Visual Library</h1>
<p class="lead">__COUNT__ images, icons, backgrounds and brand assets for Wohlig presentations, documents and web pages. Papercraft art made with Codex in the earthy palette: maroon, terracotta, sunset orange, ivory, beige and olive.</p></header>
<div class="bar"><div><input id="q" placeholder="Search: arch, shield, cloud, team, finance…"><button class="chip on" data-cat="">All <span>__COUNT__</span></button>__CHIPS__</div></div>
<p class="note" id="use"></p>
<main id="grid"></main>
<dialog id="dlg"><div class="dv"><div class="big"><img id="dimg" alt=""></div><div class="meta"><h2 id="dt"></h2><p id="dc"></p><p><code id="dp"></code></p><button class="btn" id="copy">Copy path</button><a class="btn alt" id="open" target="_blank">Open full size</a><button class="btn alt" id="close">Close</button><p class="prompt" id="dpr"></p></div></div></dialog>
<script>
const D=__DATA__, USE=__USE__, LABEL=__LABEL__;
let cat='', q='';
const grid=document.getElementById('grid');
function render(){
  const t=q.toLowerCase().split(/\s+/).filter(Boolean);
  const list=D.filter(e=>(!cat||e.category===cat)&&t.every(w=>(e.id+' '+(e.tags||[]).join(' ')+' '+(e.prompt||'')+' '+e.category).toLowerCase().includes(w)));
  document.getElementById('use').textContent=cat?USE[cat]:'Click any image for its path, size and the prompt that made it.';
  grid.innerHTML=list.map((e,i)=>`<div class="tile ${e.transparent?'tr':''} ${e.category==='client-logos'?'logo':''}" data-i="${D.indexOf(e)}"><div class="im"><img loading="lazy" src="${e.thumb}" alt="${e.id}"></div><p>${e.id}<small>${LABEL[e.category]}${e.subcategory?' · '+e.subcategory:''} · ${e.width}×${e.height}</small></p></div>`).join('')||'<p>No matches.</p>';
}
document.querySelectorAll('.chip').forEach(b=>b.onclick=()=>{document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));b.classList.add('on');cat=b.dataset.cat;render();});
document.getElementById('q').oninput=ev=>{q=ev.target.value;render();};
const dlg=document.getElementById('dlg');
grid.onclick=ev=>{const t=ev.target.closest('.tile');if(!t)return;const e=D[t.dataset.i];
  document.getElementById('dimg').src=e.file;document.getElementById('dt').textContent=e.id;
  document.getElementById('dc').textContent=`${LABEL[e.category]} · ${e.width}×${e.height}${e.transparent?' · transparent PNG':''}${e.source?' · '+e.source:''}`;
  document.getElementById('dp').textContent=e.file;document.getElementById('open').href=e.file;
  document.getElementById('dpr').textContent=e.prompt?('Prompt: '+e.prompt):'';dlg.showModal();};
document.getElementById('close').onclick=()=>dlg.close();
dlg.onclick=ev=>{if(ev.target===dlg)dlg.close();};
document.getElementById('copy').onclick=()=>{try{navigator.clipboard.writeText(document.getElementById('dp').textContent)}catch(e){}};
render();
</script></body></html>
'''

if __name__ == '__main__':
    main()
