#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a single book-style PDF of Chinese history from the markdown volumes.

Combines ancient.md / medieval.md / early-modern.md into one PDF with a title
page, a table of contents with real page numbers, volume dividers, running
headers and page numbers. Rendered with WeasyPrint.
"""
import re
from pathlib import Path
import markdown
from weasyprint import HTML

BASE = Path(__file__).resolve().parent
OUT = BASE / "중국사.pdf"

# (volume label, name, subtitle/period, source file)
VOLUMES = [
    ("제1권", "고대", "신석기 · 하상주 · 춘추전국 · 진한 · 위진남북조", "ancient.md"),
    ("제2권", "중세", "오대십국 · 송 · 요 · 금 · 원", "medieval.md"),
    ("제3권", "근세", "명 · 청", "early-modern.md"),
]

md = markdown.Markdown(
    extensions=["extra", "sane_lists"],
    output_format="html5",
)

HEADING_RE = re.compile(r"<h([1-4])>(.*?)</h\1>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def strip_first_title(text: str) -> str:
    """Drop the file's own top-level title line (first '# ...')."""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            del lines[i]
            break
    return "\n".join(lines)


toc_entries = []   # (level, anchor_id, plain_text)  level 0=volume,1=h1,2=h2
body_parts = []
counter = 0


def assign_ids(html: str) -> str:
    """Give every h1-h4 a stable id; record h1/h2 for the TOC."""
    def repl(m):
        global counter
        level = int(m.group(1))
        inner = m.group(2)
        counter += 1
        hid = f"h{counter:04d}"
        if level in (1, 2):
            plain = TAG_RE.sub("", inner).strip()
            toc_entries.append((level, hid, plain))
        return f'<h{level} id="{hid}">{inner}</h{level}>'
    return HEADING_RE.sub(repl, html)


for vi, (vlabel, vname, vsub, fname) in enumerate(VOLUMES, start=1):
    raw = (BASE / fname).read_text(encoding="utf-8")
    raw = strip_first_title(raw)
    html = md.reset().convert(raw)
    vid = f"vol{vi}"
    toc_entries.append((0, vid, f"{vlabel}  {vname}"))
    html = assign_ids(html)
    divider = (
        f'<section class="volume" id="{vid}">'
        f'<div class="vol-label">{vlabel}</div>'
        f'<div class="vol-name">{vname}</div>'
        f'<div class="vol-sub">{vsub}</div>'
        f"</section>"
    )
    body_parts.append(divider + f'<section class="vol-body">{html}</section>')

# ---- table of contents ----
toc_li = []
for level, hid, text in toc_entries:
    toc_li.append(f'<li class="lvl{level}"><a href="#{hid}">{text}</a></li>')
toc_html = (
    '<section class="toc" id="toc">'
    '<h1 class="front-title">차례</h1>'
    '<ul class="toc-list">' + "".join(toc_li) + "</ul>"
    "</section>"
)

# ---- title page ----
title_html = (
    '<section class="titlepage">'
    '<div class="title-han">中國史</div>'
    '<div class="title-kor">중국 통사</div>'
    '<div class="title-rule"></div>'
    '<div class="title-sub">신석기 문명에서 청 제국까지</div>'
    '<div class="title-vols">제1권 고대 · 제2권 중세 · 제3권 근세</div>'
    '<div class="title-foot">동아시아사 자료 모음</div>'
    "</section>"
)

CSS = """
@page {
  size: 176mm 250mm;            /* B5 trim */
  margin: 20mm 18mm 20mm 18mm;
  @bottom-center { content: counter(page); font-family:"Noto Serif KR",serif;
                   font-size: 8.5pt; color:#444; }
  @top-center { content: string(runhead); font-family:"Noto Serif KR",serif;
                font-size: 8pt; color:#777; padding-bottom: 2mm; }
}
@page :first { @bottom-center{content:none;} @top-center{content:none;} }
@page volume { @top-center{content:none;} }
@page front  { @top-center{content:none;} }

html { font-family:"Noto Serif KR","Songti SC","Apple SD Gothic Neo",serif;
       font-size: 10.3pt; line-height: 1.62; color:#1a1a1a; }
body { margin:0; }
p { margin: 0 0 .55em 0; text-align: justify; word-break: keep-all;
    overflow-wrap: break-word; }

h1,h2,h3,h4 { font-weight:700; line-height:1.3; word-break:keep-all;
              break-after: avoid; }
h1 { string-set: runhead content(text); break-before: page;
     font-size: 17pt; margin: 0 0 .8em 0; padding-bottom:.3em;
     border-bottom: 2px solid #333; }
h2 { font-size: 13.5pt; margin: 1.4em 0 .5em; color:#222; }
h3 { font-size: 11.6pt; margin: 1.1em 0 .4em; color:#333; }
h4 { font-size: 10.6pt; margin: .9em 0 .3em; color:#444; }

a { color: inherit; text-decoration: none; }

ul,ol { margin:.3em 0 .7em 0; padding-left: 1.3em; }
li { margin: .12em 0; text-align: justify; word-break: keep-all; }

blockquote { margin: .7em 0; padding: .35em .8em; background:#f6f3f8;
             border-left: 3px solid #8a4b8f; font-size: 9.6pt; color:#2a2230; }
blockquote p { margin:.25em 0; }

table { width:100%; border-collapse: collapse; margin:.7em 0;
        font-size: 8.6pt; }
th,td { border:1px solid #b9b9b9; padding:3px 5px; vertical-align: top;
        text-align: left; word-break: keep-all; overflow-wrap: anywhere; }
th { background:#efeae6; font-weight:700; }
tr { break-inside: avoid; }

hr { border:0; border-top:1px solid #ccc; margin:1.2em 4em; }
code { font-family:"Songti SC",monospace; font-size:.9em;
       background:#f0f0f0; padding:0 2px; border-radius:2px; }
strong { font-weight:700; }
em { font-style: normal; }   /* 한글 이탤릭 회피 */

/* ---- title page ---- */
.titlepage { page: front; break-after: page; text-align:center;
             padding-top: 48mm; }
.title-han { font-size: 58pt; font-weight:700; letter-spacing:.12em;
             color:#222; }
.title-kor { font-size: 22pt; margin-top: 6mm; color:#444; letter-spacing:.25em; }
.title-rule { width: 46mm; height:2px; background:#8a4b8f; margin: 12mm auto; }
.title-sub  { font-size: 13pt; color:#555; }
.title-vols { font-size: 10.5pt; color:#777; margin-top: 4mm; }
.title-foot { font-size: 10pt; color:#999; margin-top: 42mm; }

/* ---- toc ---- */
.toc { page: front; break-after: page; }
.front-title { border:0; font-size: 22pt; text-align:center; margin-bottom: 1.2em;
               break-before: avoid; }
.toc-list { list-style:none; padding:0; margin:0; }
.toc-list li a { display:block; }
.toc-list li a::after { content: leader('.') target-counter(attr(href), page);
                        color:#555; }
.toc-list li.lvl0 { margin: 1.0em 0 .3em; font-weight:700; font-size: 12.5pt; }
.toc-list li.lvl0 a::after { font-weight:400; }
.toc-list li.lvl1 { margin:.18em 0 .18em 1.2em; font-size: 10.2pt; }
.toc-list li.lvl2 { margin:.05em 0 .05em 2.6em; font-size: 9.2pt; color:#444; }

/* ---- volume divider ---- */
.volume { page: volume; break-before: page; text-align:center;
          padding-top: 78mm; string-set: runhead ""; }
.vol-label { font-size: 15pt; color:#8a4b8f; letter-spacing:.4em; }
.vol-name  { font-size: 46pt; font-weight:700; margin: 6mm 0; color:#222; }
.vol-sub   { font-size: 11pt; color:#666; }
.vol-body  { }
"""

full = (
    "<!DOCTYPE html><html lang='ko'><head><meta charset='utf-8'>"
    f"<style>{CSS}</style></head><body>"
    + title_html + toc_html + "".join(body_parts) +
    "</body></html>"
)

tmp_html = BASE / "_book_tmp.html"
tmp_html.write_text(full, encoding="utf-8")
print(f"[build] HTML assembled: {len(full):,} bytes, {len(toc_entries)} TOC entries")
print("[build] rendering PDF (this may take a while)...")
HTML(string=full, base_url=str(BASE)).write_pdf(str(OUT))
print(f"[build] wrote {OUT}  ({OUT.stat().st_size:,} bytes)")
