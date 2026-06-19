#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a single book-style PDF from liquor.md (중국 술의 역사 · 외전).

Title page + dotted TOC with real page numbers + running headers + page
numbers, rendered with WeasyPrint. Headings are shifted up one level so the
document's top-level '##' sections become book chapters.
"""
import re
from pathlib import Path
import markdown
from weasyprint import HTML

BASE = Path(__file__).resolve().parent
SRC = BASE / "liquor.md"
OUT = BASE / "중국 술의 역사.pdf"

md = markdown.Markdown(extensions=["extra", "sane_lists"], output_format="html5")
HEADING_RE = re.compile(r"<h([1-4])>(.*?)</h\1>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def prepare(text: str) -> str:
    """Drop the '# ' title, drop the in-file '## 목차' block, and shift every
    remaining heading up by one level (## -> #, ### -> ##, #### -> ###)."""
    lines = text.split("\n")
    out, i, n = [], 0, len(lines)
    dropped_title = False
    while i < n:
        ln = lines[i]
        if not dropped_title and ln.startswith("# ") and not ln.startswith("## "):
            dropped_title = True
            i += 1
            continue
        if ln.startswith("## 목차"):
            i += 1
            while i < n and not lines[i].startswith("## "):
                i += 1
            continue
        m = re.match(r"^(#{2,6}) (.*)$", ln)
        if m:
            ln = "#" * (len(m.group(1)) - 1) + " " + m.group(2)
        out.append(ln)
        i += 1
    return "\n".join(out)


toc_entries = []
counter = 0


def assign_ids(html: str) -> str:
    def repl(m):
        global counter
        level, inner = int(m.group(1)), m.group(2)
        counter += 1
        hid = f"h{counter:04d}"
        if level in (1, 2):
            toc_entries.append((level, hid, TAG_RE.sub("", inner).strip()))
        return f'<h{level} id="{hid}">{inner}</h{level}>'
    return HEADING_RE.sub(repl, html)


body = assign_ids(md.convert(prepare(SRC.read_text(encoding="utf-8"))))

toc_li = "".join(
    f'<li class="lvl{lvl}"><a href="#{hid}">{txt}</a></li>'
    for lvl, hid, txt in toc_entries
)
toc_html = (
    '<section class="toc" id="toc"><h1 class="front-title">차례</h1>'
    f'<ul class="toc-list">{toc_li}</ul></section>'
)

title_html = (
    '<section class="titlepage">'
    '<div class="title-han">中國酒史</div>'
    '<div class="title-kor">중국 술의 역사</div>'
    '<div class="title-rule"></div>'
    '<div class="title-sub">곡물 · 누룩 · 시(詩)로 빚은 9천 년</div>'
    '<div class="title-vols">신석기 발효 음료에서 백주(白酒)까지</div>'
    '<div class="title-foot">동아시아사 자료 모음 — 외전(外傳)</div>'
    "</section>"
)

CSS = """
@page {
  size: 176mm 250mm;
  margin: 20mm 18mm 20mm 18mm;
  @bottom-center { content: counter(page); font-family:"Noto Serif KR",serif;
                   font-size: 8.5pt; color:#444; }
  @top-center { content: string(runhead); font-family:"Noto Serif KR",serif;
                font-size: 8pt; color:#777; padding-bottom: 2mm; }
}
@page :first { @bottom-center{content:none;} @top-center{content:none;} }
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

table { width:100%; border-collapse: collapse; margin:.7em 0; font-size: 8.6pt; }
th,td { border:1px solid #b9b9b9; padding:3px 5px; vertical-align: top;
        text-align: left; word-break: keep-all; overflow-wrap: anywhere; }
th { background:#efeae6; font-weight:700; }
tr { break-inside: avoid; }

hr { border:0; border-top:1px solid #ccc; margin:1.2em 4em; }
code { font-family:"Songti SC",monospace; font-size:.9em; background:#f0f0f0;
       padding:0 2px; border-radius:2px; }
strong { font-weight:700; } em { font-style: normal; }

.titlepage { page: front; break-after: page; text-align:center; padding-top: 48mm; }
.title-han { font-size: 52pt; font-weight:700; letter-spacing:.10em; color:#222; }
.title-kor { font-size: 21pt; margin-top: 6mm; color:#444; letter-spacing:.25em; }
.title-rule { width: 46mm; height:2px; background:#8a4b8f; margin: 12mm auto; }
.title-sub  { font-size: 13pt; color:#555; }
.title-vols { font-size: 10.5pt; color:#777; margin-top: 4mm; }
.title-foot { font-size: 10pt; color:#999; margin-top: 42mm; }

.toc { page: front; break-after: page; }
.front-title { border:0; font-size: 22pt; text-align:center; margin-bottom: 1.2em;
               break-before: avoid; string-set: runhead ""; }
.toc-list { list-style:none; padding:0; margin:0; }
.toc-list li a { display:block; }
.toc-list li a::after { content: leader('.') target-counter(attr(href), page);
                        color:#555; }
.toc-list li.lvl1 { margin: .9em 0 .25em; font-weight:700; font-size: 12pt; }
.toc-list li.lvl1 a::after { font-weight:400; }
.toc-list li.lvl2 { margin:.08em 0 .08em 1.6em; font-size: 9.6pt; color:#444; }
"""

full = ("<!DOCTYPE html><html lang='ko'><head><meta charset='utf-8'>"
        f"<style>{CSS}</style></head><body>"
        + title_html + toc_html + f'<section class="vol-body">{body}</section>'
        + "</body></html>")

print(f"[build] HTML assembled: {len(full):,} bytes, {len(toc_entries)} TOC entries")
HTML(string=full, base_url=str(BASE)).write_pdf(str(OUT))
print(f"[build] wrote {OUT}  ({OUT.stat().st_size:,} bytes)")
