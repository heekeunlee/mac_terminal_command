import re, sys, pathlib
import pdfplumber
from pypdf import PdfReader, PdfWriter
from playwright.sync_api import sync_playwright
import html as _html
from content_data import INDEX
from walkthrough import STEPS
from cases import CASES

HERE = pathlib.Path(__file__).parent
SRC = (HERE / "book.html").read_text(encoding="utf-8")
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "terminal-book.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

from chapters import CHAPTERS as _CH
CHAPTERS = [(n, title, cmds) for n, title, _chip, _desc, cmds in _CH]

PDF_OPTS = dict(width="152mm", height="225mm", print_background=True,
                margin={"top": "18mm", "bottom": "17mm", "left": "16mm", "right": "16mm"})
import base64
_FONT = base64.b64encode((HERE / "jbm-latin-400.woff2").read_bytes()).decode()
FOOTER = ('<style>@font-face{font-family:PN;src:url(data:font/woff2;base64,' + _FONT + ') format("woff2");}</style>'
          '<div style="width:100%;font-family:PN;'
          'font-size:7.5pt;color:#8A9892;text-align:center;letter-spacing:0.08em;">'
          '<span class="pageNumber"></span></div>')

TOGGLE_CSS = """
body.only-cover > section:not(.cover), body.only-cover > footer{display:none !important;}
body.no-cover > .cover{display:none !important;}
"""


def toc_html(pages):
    def row(cls_title, title_html, page):
        return (f'<div class="{cls_title}">{title_html}<span class="toc-leader"></span>'
                f'<span class="toc-page">{page}</span></div>')
    part_row = lambda no, title, key: (f'<div class="toc-part-row"><span class="toc-part-no">{no}</span>'
                                       f'<span class="toc-part-title">{title}</span><span class="toc-leader"></span>'
                                       f'<span class="toc-page">{pages.get(key, "")}</span></div>')
    parts = [part_row("1부", "두 글자 사전", "PM_PART_1")]
    parts += [row("toc-chapter-row", '<span class="toc-chapter-title">터미널이 처음이라면</span>',
                 pages.get("PM_BASICS", "")).replace('class="toc-chapter-row"',
                 'class="toc-chapter-row" style="margin-bottom:12pt;"')]
    for num, title, cmds in CHAPTERS:
        head = row("toc-chapter-row",
                   f'<span class="toc-num">{num}</span><span class="toc-chapter-title">{title}</span>',
                   pages.get(f"PM_CH_{num}", ""))
        cmd_rows = "".join(row("toc-cmd-row", f"<code>{c}</code>", pages.get(f"PM_CMD_{c}", ""))
                           for c in cmds)
        cmd_rows += row("toc-cmd-row", '<span class="toc-qr">빠른 참조</span>', pages.get(f"PM_QR_{num}", ""))
        parts.append(f'<div class="toc-chapter">{head}<div class="toc-commands">{cmd_rows}</div></div>')
    parts.append(part_row("2부", "두 글자로 문제 풀기", "PM_PART_2"))
    step_rows = "".join(row("toc-cmd-row", f'<span>STEP {st["n"]} · {st["title"]}</span>', pages.get(f"PM_ST_{st['n']}", ""))
                        for st in STEPS)
    step_rows += row("toc-cmd-row", '<span class="toc-qr">오늘 쓴 명령어 정리</span>', pages.get("PM_WRAP", ""))
    head13 = row("toc-chapter-row", '<span class="toc-num">13</span><span class="toc-chapter-title">따라 하기: 프로젝트 하나를 처음부터 끝까지</span>',
                 pages.get("PM_CH_13", ""))
    parts.append(f'<div class="toc-chapter">{head13}<div class="toc-commands">{step_rows}</div></div>')
    case_rows = "".join(row("toc-cmd-row", f'<span>CASE {c["n"]} · {c["title"]}</span>', pages.get(f"PM_CASE_{c['n']}", ""))
                        for c in CASES)
    head14 = row("toc-chapter-row", '<span class="toc-num">14</span><span class="toc-chapter-title">문제 해결 사례집: 증상에서 해결까지</span>',
                 pages.get("PM_CH_14", ""))
    parts.append(f'<div class="toc-chapter">{head14}<div class="toc-commands">{case_rows}</div></div>')
    parts.append(f'<div style="height:8pt"></div>')
    parts.append(row("toc-chapter-row", '<span class="toc-chapter-title">찾아보기 · 하고 싶은 일로 찾기</span>',
                     pages.get("PM_INDEX", "")))
    return "\n".join(parts)


def index_html(pages):
    out = []
    for group, rows in INDEX:
        items = []
        for sit, refs in rows:
            r = "".join(f'<span class="ix-ref"><b>{_html.escape(lbl)}</b> {pages.get(key, "")}</span>'
                        for lbl, key in refs)
            items.append(f'<div class="ix-row"><span class="sit">{_html.escape(sit)}</span>'
                         f'<span class="toc-leader"></span><span class="ix-refs">{r}</span></div>')
        out.append(f'<div class="ix-group"><h4>{_html.escape(group)}</h4>{"".join(items)}</div>')
    return "\n".join(out)


def fill_refs(html, pages):
    return re.sub(r"\{\{P:(\w+)\}\}", lambda m: str(pages.get(m.group(1), "")), html)


def render(page, html, path, mode, footer):
    tmp = HERE / "_render.html"
    tmp.write_text(html.replace("</style>", TOGGLE_CSS + "</style>", 1), encoding="utf-8")
    page.goto(tmp.as_uri(), wait_until="networkidle")
    page.evaluate(f"document.body.className = '{mode}'")
    page.evaluate("document.fonts.ready")
    opts = dict(PDF_OPTS, path=str(path))
    if footer:
        opts.update(display_header_footer=True, header_template="<div></div>", footer_template=FOOTER)
    page.pdf(**opts)


def marker_pages(pdf_path):
    found = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, pg in enumerate(pdf.pages, start=1):
            for m in re.findall(r"PM_[A-Za-z0-9_]+", pg.extract_text() or ""):
                found.setdefault(m, i)
    return found


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=CHROME, headless=True)
    page = browser.new_page()

    cover_pdf = HERE / "_cover.pdf"
    body_pdf = HERE / "_body.pdf"
    render(page, fill_refs(SRC.replace("{{TOC_BODY}}", "").replace("{{INDEX_BODY}}", ""), {}), cover_pdf, "only-cover", footer=False)

    pages = {}
    for attempt in range(4):
        html = fill_refs(SRC.replace("{{TOC_BODY}}", toc_html(pages)).replace("{{INDEX_BODY}}", index_html(pages)), pages)
        render(page, html, body_pdf, "no-cover", footer=False)
        new_pages = marker_pages(body_pdf)
        if new_pages == pages:
            break
        pages = new_pages
    else:
        raise SystemExit("page numbers did not converge")

    def page_texts(pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            return [re.sub(r"PM_[A-Za-z0-9_]+", "", pg.extract_text() or "").split() for pg in pdf.pages]
    with_markers = page_texts(body_pdf)
    clean_html = html.replace("</style>", ".pm{visibility:hidden !important;}</style>", 1)
    render(page, clean_html, body_pdf, "no-cover", footer=False)
    if page_texts(body_pdf) != with_markers:
        raise SystemExit("layout changed after removing markers")
    browser.close()

expected = {"PM_BASICS", "PM_TOC", "PM_INDEX", "PM_CH_13", "PM_WRAP", "PM_PART_1", "PM_PART_2", "PM_CH_14"} | {f"PM_CASE_{c['n']}" for c in CASES} | {f"PM_ST_{st['n']}" for st in STEPS} | {f"PM_CH_{n}" for n, _, _ in CHAPTERS} | \
           {f"PM_QR_{n}" for n, _, _ in CHAPTERS} | \
           {f"PM_CMD_{c}" for _, _, cs in CHAPTERS for c in cs}
missing = expected - pages.keys()
if missing:
    raise SystemExit(f"markers not found: {sorted(missing)}")

writer = PdfWriter()
for src in (cover_pdf, body_pdf):
    for pg in PdfReader(src).pages:
        writer.add_page(pg)

offset = len(PdfReader(cover_pdf).pages)

# page numbers: stamped with an embedded OFL font, 10mm above the trim edge
import io
from reportlab.pdfgen import canvas as _canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
pdfmetrics.registerFont(TTFont("PN", str(HERE / "JetBrainsMono-Regular.ttf")))
no_number = {pages["PM_PART_1"], pages["PM_PART_2"]}
w0, h0 = float(writer.pages[offset].mediabox.width), float(writer.pages[offset].mediabox.height)
buf = io.BytesIO()
c = _canvas.Canvas(buf, pagesize=(w0, h0), initialFontName="PN", initialFontSize=7.5)
targets = [i for i in range(offset, len(writer.pages)) if (i - offset + 1) not in no_number]
for i in targets:
    c.setFont("PN", 7.5)
    c.setFillColorRGB(0x8A / 255, 0x98 / 255, 0x92 / 255)
    c.drawCentredString(w0 / 2, 10 * mm, str(i - offset + 1))
    c.showPage()
c.save()
buf.seek(0)
stamps = PdfReader(buf)
for k, i in enumerate(targets):
    writer.pages[i].merge_page(stamps.pages[k])

if len(writer.pages) % 2:
    writer.add_blank_page()
idx = lambda key: pages[key] - 1 + offset
writer.add_outline_item("표지", 0)
writer.add_outline_item("목차", idx("PM_TOC"))
p1 = writer.add_outline_item("1부 · 두 글자 사전", idx("PM_PART_1"))
writer.add_outline_item("터미널이 처음이라면", idx("PM_BASICS"), parent=p1)
for num, title, cmds in CHAPTERS:
    parent = writer.add_outline_item(f"{num}  {title}", idx(f"PM_CH_{num}"), parent=p1)
    for c in cmds:
        writer.add_outline_item(c, idx(f"PM_CMD_{c}"), parent=parent)
    writer.add_outline_item("빠른 참조", idx(f"PM_QR_{num}"), parent=parent)
p2 = writer.add_outline_item("2부 · 두 글자로 문제 풀기", idx("PM_PART_2"))
ch13 = writer.add_outline_item("13  따라 하기: 프로젝트 하나를 처음부터 끝까지", idx("PM_CH_13"), parent=p2)
for st in STEPS:
    writer.add_outline_item(f"STEP {st['n']} · {st['title']}", idx(f"PM_ST_{st['n']}"), parent=ch13)
writer.add_outline_item("오늘 쓴 명령어 정리", idx("PM_WRAP"), parent=ch13)
ch14 = writer.add_outline_item("14  문제 해결 사례집: 증상에서 해결까지", idx("PM_CH_14"), parent=p2)
for c in CASES:
    writer.add_outline_item(f"CASE {c['n']} · {c['title']}", idx(f"PM_CASE_{c['n']}"), parent=ch14)
writer.add_outline_item("찾아보기", idx("PM_INDEX"))

writer.add_metadata({"/Title": "두 글자로 말하는 사람들", "/Subject": "맥 터미널, 50개의 단어로 컴퓨터와 대화하는 법",
                     "/Keywords": "macOS, Terminal, zsh, 터미널, 명령어"})
writer.page_mode = "/UseOutlines"
for _pg in writer.pages:
    _pg.compress_content_streams()
writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
with open(OUT, "wb") as f:
    writer.write(f)

for tmp in (cover_pdf, body_pdf, HERE / "_render.html"):
    tmp.unlink(missing_ok=True)

print(f"converged after {attempt + 1} render(s)")
print(f"pages: {offset + len(PdfReader(OUT).pages) - offset} total -> {OUT}")
print({k: v for k, v in sorted(pages.items(), key=lambda kv: kv[1])})
