#!/usr/bin/env python3
"""Build the illustrated, annotated A4 complete edition."""
import ast, html, re, subprocess
from pathlib import Path
import markdown

ROOT = Path(__file__).resolve().parent
CHAPTERS = sorted(ROOT.glob("[0-9][0-9]-*.md"))
COVER = ROOT / "assets/genji-complete-cover.png"
HTML_OUT = ROOT / "겐지 이야기 완역본.html"
PDF_OUT = ROOT / "겐지 이야기 완역본.pdf"
ILLUSTRATIONS = {
  12:("assets/12-suma-generated.png","스마의 바닷가에서 도성을 그리는 겐지"),
  34:("assets/34-wakana-generated.png","봄빛 속 로쿠조원의 연회와 춤"),
  45:("assets/45-hashihime-generated.png","우지강 안개 너머로 엿본 두 공주와 거문고"),
  51:("assets/51-ukifune-generated.png","새벽 안개 속 우지강에 떠 있는 우키후네"),
}

def legacy_notes():
    tree=ast.parse((ROOT.parent/"build_genji_pdf.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="FOOTNOTES" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("FOOTNOTES not found")

CURATED=legacy_notes()
def title(path): return path.read_text(encoding="utf-8").splitlines()[0].removeprefix("# ").strip()

def clean(text):
    defs={}; lines=[]
    for line in text.splitlines():
        m=re.match(r"^\[\^([^]]+)\]:\s*(.+)$",line)
        if m: defs[m.group(1)]=m.group(2)
        else: lines.append(line)
    if lines and lines[0].startswith("# "): lines=lines[1:]
    lines=[x for x in lines if not re.match(r"^>\s*(번역 상태|대조 상태|저본 대조)",x)]
    lines=[x for x in lines if not re.match(r"^\*\*(대조 저본|저본 대조)[:：]\*\*",x)]
    audit=re.compile(r"^#{2,}\s*(번역[·ㆍ ]?대조 기록|저본[·ㆍ ]?대조 기록|저본과 대조 자료)")
    for i,line in enumerate(lines):
        if audit.match(line): lines=lines[:i]; break
    lines=[x for x in lines if not re.match(r"^#{2,}\s*원문 와카 대조 보완",x)]
    return "\n".join(lines).strip(),defs

def add_notes(text,defs,filename):
    count=0
    for key,note in defs.items():
        marker=f"[^{key}]"
        if marker in text:
            rendered=markdown.markdown(note,extensions=["extra"]).removeprefix("<p>").removesuffix("</p>")
            text=text.replace(marker,f'<span class="footnote">{rendered}</span>',1); count+=1
    for needle,note in CURATED.get(filename,[]):
        if needle not in text: raise ValueError(f"Missing note anchor: {filename}: {needle}")
        text=text.replace(needle,needle+f'<span class="footnote">{html.escape(note)}</span>',1); count+=1
    return text,count

titles=[title(p) for p in CHAPTERS]
toc="".join(f'<li><a href="#c{i:02d}"><b>{i:02d}</b><span>{html.escape(t)}</span></a></li>' for i,t in enumerate(titles,1))
parts={1:("제1부","빛나는 겐지","탄생과 사랑, 영광의 계절"),34:("제2부","덧없는 영화","만년의 사랑과 상실"),42:("제3부","우지 십첩","강물과 안개 속에 이어지는 인연")}
renderer=markdown.Markdown(extensions=["extra","sane_lists"],output_format="html5")
sections=[]; note_count=0
for n,path in enumerate(CHAPTERS,1):
    if n in parts:
        a,b,c=parts[n]; sections.append(f'<section class="part"><i>源氏物語</i><p>{a}</p><h1>{b}</h1><em>✿</em><h2>{c}</h2></section>')
    source,defs=clean(path.read_text(encoding="utf-8")); source,count=add_notes(source,defs,path.name); note_count+=count
    body=renderer.reset().convert(source)
    local=ROOT/f"assets/{n:02d}-{path.stem.split('-',1)[1]}.jpg"
    if local.exists(): body=re.sub(r'(<img\s+src=")[^"]+("[^>]*>)',rf'\1{local.as_uri()}\2',body,count=1)
    if n in ILLUSTRATIONS:
        rel,cap=ILLUSTRATIONS[n]; uri=(ROOT/rel).resolve().as_uri()
        body=f'<figure><img src="{uri}" alt="{cap}"><figcaption>{cap} · 이 판본을 위해 제작한 삽화</figcaption></figure>'+body
    sections.append(f'<section class="chapter" id="c{n:02d}"><header><b>{n:02d}</b><h1>{html.escape(titles[n-1])}</h1></header><div class="body" data-title="{html.escape(titles[n-1])}">{body}</div></section>')

css=r'''
@page{size:A4;margin:18mm 17mm 20mm;background:#e7dac2;@top-center{content:string(chapter);font:8pt "Noto Serif KR";color:#6b5e50}@bottom-center{content:counter(page);font:8pt "Noto Serif KR";color:#6b5e50}@footnote{border-top:.35mm solid #aa9364;padding:2.5mm 5mm 0;margin-top:3mm;background:#f7f1e6}}
@page cover{margin:0;background:#241e21;@top-center{content:none}@bottom-center{content:none}}
@page front{background:#f6f0e4;@top-center{content:none}}
*{box-sizing:border-box}html{font-family:"Noto Serif KR","Nanum Myeongjo",AppleMyungjo,serif;font-size:10.5pt;line-height:1.82;color:#29231e}body{margin:0}
.cover{page:cover;width:210mm;height:297mm;position:relative;overflow:hidden;break-after:page;color:#fff8e8}.cover>img{position:absolute;width:210mm;height:297mm;object-fit:cover}.cover:after{content:"";position:absolute;top:0;right:0;bottom:0;left:0;background:linear-gradient(rgba(12,13,22,.12),rgba(12,9,10,.05) 55%,rgba(12,9,10,.32));border:4mm solid #b8924d66}.cover-title{position:absolute;z-index:2;top:22mm;left:24mm;padding:12mm 10mm 11mm;background:#1d191fc7;border-top:1.2mm solid #c8a85e;border-bottom:.4mm solid #c8a85e;letter-spacing:.16em}.cover-title .jp{font-size:9pt;letter-spacing:.38em;color:#d8c17f;margin-bottom:4mm}.cover-title h1{margin:0;font-size:31pt}.cover-title p{margin:4mm 0 0;font-size:12pt;letter-spacing:.28em}.author{position:absolute;z-index:2;right:18mm;bottom:19mm;padding:4mm 6mm;background:#1d191fb3;border-left:.7mm solid #b99a50;letter-spacing:.18em}
.half,.preface,.toc{page:front;break-after:page}.half{height:245mm;display:flex;align-items:center;justify-content:center;text-align:center;border:.35mm solid #b69b61;outline:.15mm solid #d9cda8;outline-offset:-4mm}.seal{width:20mm;height:20mm;margin:0 auto 12mm;padding-top:2mm;color:#f6e8ce;background:#8f3029;font:18pt GungSeo}.half h1{font-size:30pt;margin:0 0 5mm;letter-spacing:.18em}.half h2{font-size:13pt;font-weight:400;color:#75644e;letter-spacing:.25em}.orn{text-align:center;color:#aa8744;letter-spacing:1em;margin:9mm}.preface,.toc{padding:9mm 10mm;background:#fbf8f0}.preface h1,.toc h1{font-size:22pt;letter-spacing:.14em;border-bottom:.5mm solid #9c7a3e;padding-bottom:5mm}.preface p{text-indent:1em}.edition{margin-top:16mm;padding:7mm;border:.25mm solid #c4ae7d;background:#f2e9d7;font-size:9.5pt}.toc ol{columns:2;column-gap:14mm;list-style:none;padding:0}.toc li{break-inside:avoid;border-bottom:.2mm dotted #c0b39b;padding:1.4mm 0;font-size:9pt}.toc a{display:flex;gap:3mm;color:inherit;text-decoration:none}.toc b{color:#9b3b32}.toc a:after{content:target-counter(attr(href),page);margin-left:auto;color:#8a7b66}
.part{break-before:page;break-after:page;height:250mm;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;background:#f8f2e6;border-top:.4mm solid #a88a50;border-bottom:.4mm solid #a88a50}.part i{letter-spacing:.35em;color:#a13c31;font-size:12pt;margin-bottom:12mm}.part p{letter-spacing:.5em;color:#8c6f3d;margin:0}.part h1{font-size:28pt;letter-spacing:.2em;margin:5mm}.part h2{font-size:11pt;font-weight:400;letter-spacing:.2em;color:#74695b}.part em{color:#b89b57;font-size:21pt}
.chapter{break-before:page}.chapter>header{height:248mm;padding:76mm 14mm 0;text-align:center;background:#f8f2e6;break-after:page;string-set:chapter "";border:.3mm solid #c1aa78}.chapter>header b{display:block;width:16mm;height:16mm;margin:0 auto 10mm;padding-top:3.2mm;border-radius:50%;background:#96362e;color:#f8ead2;font:9pt sans-serif}.chapter>header h1{font-size:28pt;line-height:1.45;letter-spacing:.08em;margin:0}.body{string-set:chapter attr(data-title);background:#fbf8f0;padding:9mm 12mm;box-decoration-break:clone}.body p{margin:0 0 4mm;text-align:justify;text-indent:1em;overflow-wrap:break-word;orphans:2;widows:2}.body blockquote{margin:5mm 8mm;padding:3mm 6mm;border-left:.7mm solid #aa8a50;color:#5a4b3d;background:#f2eadb;break-inside:avoid}.body blockquote p{margin:1mm 0;text-indent:0;text-align:left}.body h2,.body h3{margin:8mm 0 5mm;padding-bottom:2mm;border-bottom:.25mm solid #b49e74;color:#514438;break-after:avoid}.body img{display:block;max-width:100%;max-height:165mm;margin:6mm auto 2mm;object-fit:contain}.body p[align=center]{text-indent:0;text-align:center}.body sub{display:block;font-size:7.7pt;line-height:1.45;color:#746b63}figure{margin:0 0 10mm;break-inside:avoid}figure img{width:100%;max-height:150mm;border:.3mm solid #b89e68}figcaption{text-align:center;font-size:8pt;color:#776a5a;margin-top:2mm}
.footnote{float:footnote;footnote-policy:block;font-size:7.8pt;line-height:1.42;color:#4f4841}.footnote::footnote-call{content:counter(footnote);font-size:6.7pt;vertical-align:super;line-height:0;color:#8f3c34}.footnote::footnote-marker{content:counter(footnote) ". ";color:#8f3c34;font-weight:700}a{color:#77483d;text-decoration:none}hr{border:0;border-top:.3mm solid #baa678;margin:10mm 25%}
'''
doc=f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>겐지 이야기 완역본</title><style>{css}</style></head><body><section class="cover"><img src="{COVER.as_uri()}"><div class="cover-title"><div class="jp">源氏物語 · 全五十四帖</div><h1>겐지 이야기</h1><p>현대 한국어 완역본</p></div><div class="author">무라사키 시키부</div></section><section class="half"><div><div class="seal">源</div><h1>겐지 이야기</h1><h2>현대 한국어 완역본 · 전 54첩</h2><div class="orn">◆ ◇ ◆</div><p>무라사키 시키부</p></div></section><section class="preface"><h1>책을 열며</h1><div class="orn">— 源氏物語 —</div><p>천 년 전 헤이안 궁정에서 태어난 『겐지 이야기』는 빛나는 황자의 사랑과 영광, 그리고 그 뒤를 잇는 사람들의 그리움과 상실을 쉰네 편의 이야기로 펼쳐 보인다. 계절의 미묘한 변화, 옷깃에 밴 향, 발 너머로 전해지는 기척과 짧은 노래 한 수가 인물의 마음을 대신한다.</p><p>이 책은 원문의 장면과 대화, 편지와 와카를 가능한 한 온전히 살리면서 오늘의 한국어 독자가 자연스럽게 읽을 수 있도록 옮긴 완역본이다. 첫 첩 「기리쓰보」에서 시작된 빛과 그림자는 겐지의 영화와 쇠락을 지나 우지의 안개 낀 강가까지 이어진다.</p><div class="edition"><b>이 판본에 대하여</b><br>54첩 전체를 한 권으로 합본하고, 용어 설명은 해당 페이지 아래 각주로 배치했다. 표지와 후반부 삽화는 헤이안 시대 야마토에와 금박 병풍을 모티프로 제작했다.</div></section><section class="toc"><h1>차례</h1><ol>{toc}</ol></section>{''.join(sections)}</body></html>'''
HTML_OUT.write_text(doc,encoding="utf-8")
subprocess.run(["weasyprint",str(HTML_OUT),str(PDF_OUT)],check=True,cwd=ROOT)
print(f"Wrote {PDF_OUT} ({PDF_OUT.stat().st_size:,} bytes, {note_count} page footnotes)")
