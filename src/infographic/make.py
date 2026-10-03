import html, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
esc = html.escape

# abbr: list of (text, highlighted?) pieces; term: (kind, text) with kind cmd/out/arrow
PAGES = [
 dict(theme="이동하고 둘러보기", sub="터미널을 열면 가장 먼저 쓰는 다섯 단어", color="#1F6F5C", tint="#E6F1EC", cmds=[
  dict(name="pwd", abbr=[("p", 1), ("rint ", 0), ("w", 1), ("orking ", 0), ("d", 1), ("irectory", 0)],
       mean="지금 내가 있는 폴더 위치를 알려준다",
       term=[("cmd", "pwd"), ("out", "/Users/me/Documents")],
       origin="결과가 종이에 인쇄되던 텔레타이프 시절의 흔적이라 화면 출력인데도 'print'라고 부른다.",
       opts=[("-P", "실제 경로")]),
  dict(name="cd", abbr=[("c", 1), ("hange ", 0), ("d", 1), ("irectory", 0)],
       mean="다른 폴더로 이동한다",
       term=[("cmd", "cd Documents"), ("arrow", "프롬프트가 ~/Documents 로 바뀜"), ("cmd", "cd .."), ("arrow", "한 단계 위 폴더로")],
       origin="초기 유닉스에서는 chdir였다. 가장 많이 치는 명령이라 두 글자로 줄었다.",
       opts=[("~", "홈 폴더"), ("..", "위 폴더"), ("-", "직전 폴더")]),
  dict(name="ls", abbr=[("l", 1), ("i", 0), ("s", 1), ("t", 0)],
       mean="폴더 안에 무엇이 있는지 보여준다",
       term=[("cmd", "ls -la"), ("out", "drwxr-xr-x  5 me  staff  160 notes"), ("out", "-rw-r--r--  1 me  staff   52 .env")],
       origin="점(.)으로 시작하는 '숨김 파일'은 ls가 .과 ..을 감추려던 코드의 부작용에서 생겨난 관례다.",
       opts=[("-l", "long 자세히"), ("-a", "all 숨김까지"), ("-h", "읽기 쉬운 단위")]),
  dict(name="cat", abbr=[("c", 1), ("on", 0), ("cat", 1), ("enate", 0)],
       mean="파일 내용을 화면에 그대로 보여준다",
       term=[("cmd", "cat memo.txt"), ("out", "오늘 할 일: 강의 자료 정리")],
       origin="고양이와는 무관하다. '사슬처럼 이어 붙이다'라는 뜻으로, 원래 여러 파일을 이어 붙이는 명령이었다.",
       opts=[("-n", "줄 번호"), ("a b > c", "두 파일 합치기")]),
  dict(name="man", abbr=[("man", 1), ("ual", 0)],
       mean="명령어의 공식 설명서를 연다",
       term=[("cmd", "man ls"), ("out", "LS(1)   General Commands Manual"), ("arrow", "q 를 누르면 닫힘")],
       origin="1971년 첫 유닉스 설명서 형식이 지금까지 그대로 이어진다. 모르는 명령은 man부터.",
       opts=[("-k 단어", "관련 명령 찾기"), ("/단어", "설명서 안 검색")]),
 ]),
 dict(theme="파일과 폴더 다루기", sub="만들고, 복사하고, 옮기고, 지우기", color="#A85A22", tint="#F8EDE3", cmds=[
  dict(name="mkdir", abbr=[("m", 1), ("a", 0), ("k", 1), ("e ", 0), ("dir", 1), ("ectory", 0)],
       mean="새 폴더를 만든다",
       term=[("cmd", "mkdir -p 2026/10/notes"), ("arrow", "중간 폴더까지 한 번에 생성")],
       origin="유닉스 명령은 성공하면 아무 말도 하지 않는다. 조용하다면 잘 된 것이다.",
       opts=[("-p", "parents 중간 폴더도")]),
  dict(name="touch", abbr=[("touch", 1), (" · 살짝 건드리다", 0)],
       mean="빈 파일을 만든다",
       term=[("cmd", "touch index.html"), ("arrow", "크기 0짜리 새 파일 생성")],
       origin="원래는 파일을 '살짝 건드려' 수정 시각만 바꾸는 명령이었다. 새 파일이 생기는 부수 효과가 더 유명해졌다.",
       opts=[("a{1..3}.md", "번호 붙여 여러 개")]),
  dict(name="cp", abbr=[("c", 1), ("o", 0), ("p", 1), ("y", 0)],
       mean="복사본을 만든다. 원본은 그대로",
       term=[("cmd", "cp report.txt backup.txt"), ("cmd", "cp -R project/ project_bak/"), ("arrow", "폴더째 복사")],
       origin="대상 파일이 이미 있으면 묻지 않고 덮어쓴다. 중요한 파일은 -i를 붙이는 습관을.",
       opts=[("-R", "Recursive 폴더째"), ("-i", "interactive 묻기"), ("-n", "덮어쓰지 않기")]),
  dict(name="mv", abbr=[("m", 1), ("o", 0), ("v", 1), ("e", 0)],
       mean="옮기거나 이름을 바꾼다. 원본은 사라진다",
       term=[("cmd", "mv old.txt new.txt"), ("arrow", "이름만 바뀜"), ("cmd", "mv *.pdf ~/Documents/"), ("arrow", "PDF 전부 이동")],
       origin="같은 디스크 안에서는 실제로 복사하지 않고 목차만 바꿔서, 수십 GB도 순식간에 '이동'한다.",
       opts=[("-i", "덮어쓰기 전 묻기"), ("-n", "있으면 그대로")]),
  dict(name="rm", abbr=[("r", 1), ("e", 0), ("m", 1), ("ove", 0)],
       mean="휴지통 없이 바로 지운다",
       term=[("cmd", "rm -i draft.txt"), ("out", "remove draft.txt? y"), ("cmd", "rm -r old_project/")],
       origin="2015년 한 게임 플랫폼의 스크립트에서 변수 하나가 비면서 rm -rf가 사용자 파일을 통째로 지운 사고가 있었다.",
       opts=[("-r", "recursive 폴더째"), ("-i", "하나씩 확인"), ("-f", "force 강제")]),
 ]),
 dict(theme="찾고, 쓰고, 권한 주기", sub="원하는 것을 찾아내고 다루는 법", color="#4F4A8C", tint="#ECEBF5", cmds=[
  dict(name="grep", abbr=[("g", 1), ("lobal ", 0), ("re", 1), ("gular expression ", 0), ("p", 1), ("rint", 0)],
       mean="파일 속에서 글자를 찾아낸다",
       term=[("cmd", 'grep -rn "TODO" src/'), ("out", "src/App.tsx:42:// TODO: 3장 추가")],
       origin="옛 편집기 ed의 명령 g/re/p에서 왔다. 켄 톰슨이 하룻밤 만에 독립 프로그램으로 만들었다는 일화가 있다.",
       opts=[("-r", "하위 폴더까지"), ("-i", "대소문자 무시"), ("-n", "줄 번호")]),
  dict(name="find", abbr=[("find", 1), (" · 찾다", 0)],
       mean="조건에 맞는 파일을 찾아낸다",
       term=[("cmd", "find ~ -size +1G"), ("out", "/Users/me/Movies/lecture.mov"), ("cmd", 'find . -name "*.pdf"')],
       origin="find는 파일을, grep은 내용을 찾는다. 이 한 문장으로 둘을 구분하면 헷갈리지 않는다.",
       opts=[("-name", "이름으로"), ("-type d", "폴더만"), ("-mtime -7", "7일 이내 수정")]),
  dict(name="echo", abbr=[("echo", 1), (" · 메아리", 0)],
       mean="입력한 말을 그대로 되돌려준다",
       term=[("cmd", "echo $HOME"), ("out", "/Users/me"), ("cmd", 'echo "한 줄" >> note.txt')],
       origin="외친 말을 돌려주는 메아리처럼 글자를 출력한다. 변수 확인과 파일 쓰기에 매일 쓰인다.",
       opts=[(">", "덮어쓰기"), (">>", "덧붙이기")]),
  dict(name="chmod", abbr=[("ch", 1), ("ange ", 0), ("mod", 1), ("e", 0)],
       mean="누가 읽고 쓰고 실행할지 정한다",
       term=[("cmd", "chmod +x run.sh"), ("arrow", "실행할 수 있게 됨"), ("cmd", "chmod 755 run.sh")],
       origin="읽기 r=4, 쓰기 w=2, 실행 x=1은 2진수 자리값이다. 더하면 권한 숫자가 된다. 4+2+1=7.",
       opts=[("+x", "실행 권한 추가"), ("755", "나 전부, 남 읽기·실행"), ("-R", "폴더 전체")]),
  dict(name="sudo", abbr=[("su", 1), ("peruser ", 0), ("do", 1)],
       mean="이 명령 하나만 관리자 권한으로 실행한다",
       term=[("cmd", "sudo !!"), ("out", "Password:"), ("arrow", "입력해도 안 보이는 게 정상")],
       origin="1980년 미국 뉴욕주립대 버펄로에서 탄생. 웹툰 xkcd의 'sudo 샌드위치 만들어 줘' 농담으로 유명하다.",
       opts=[("!!", "직전 명령을 관리자로"), ("-k", "다음엔 다시 묻기")]),
 ]),
 dict(theme="프로그램과 인터넷", sub="실행 중인 것을 다루고, 밖과 연결하기", color="#A33B3B", tint="#F6E9E8", cmds=[
  dict(name="ps", abbr=[("p", 1), ("rocess ", 0), ("s", 1), ("tatus", 0)],
       mean="지금 실행 중인 프로그램을 보여준다",
       term=[("cmd", "ps aux | grep node"), ("out", "me  4821  98.2  node server.js")],
       origin="두 번째 칸의 숫자(PID)가 프로그램의 고유 번호다. 멈출 때 이 번호가 필요하다.",
       opts=[("aux", "모든 프로그램 자세히"), ("-r", "CPU 많이 쓰는 순")]),
  dict(name="kill", abbr=[("kill", 1), (" · 신호를 보내다", 0)],
       mean="프로그램에 신호를 보내 멈추게 한다",
       term=[("cmd", "kill 4821"), ("arrow", "정리하고 끝내 달라는 요청"), ("cmd", "kill -9 4821"), ("arrow", "거부할 수 없는 강제 종료")],
       origin="이름은 '죽이다'지만 실제로는 신호를 보내는 명령이다. -9만 프로그램이 거부할 수 없다.",
       opts=[("-9", "강제 종료"), ("killall 앱", "이름으로 종료")]),
  dict(name="curl", abbr=[("c", 1), ("lient ", 0), ("URL", 1)],
       mean="인터넷 주소와 데이터를 주고받는다",
       term=[("cmd", "curl -O https://example.com/a.zip"), ("cmd", "curl wttr.in/Seoul"), ("arrow", "터미널에 서울 날씨가 그림으로")],
       origin="1996년 스웨덴의 다니엘 스텐베리가 만든 httpget이 urlget을 거쳐 curl이 되었다.",
       opts=[("-O", "원래 이름으로 저장"), ("-L", "옮긴 주소 따라가기"), ("-I", "응답 정보만")]),
  dict(name="ssh", abbr=[("s", 1), ("ecure ", 0), ("sh", 1), ("ell", 0)],
       mean="다른 컴퓨터에 안전하게 접속한다",
       term=[("cmd", "ssh me@myserver.com"), ("out", "me@myserver:~$"), ("arrow", "서버를 내 맥처럼 조작")],
       origin="1995년 핀란드의 타투 윌로넨이 대학 네트워크에서 비밀번호를 도둑맞은 뒤 직접 만든 암호화 접속 도구다.",
       opts=[("-p", "port 포트 번호"), ("-i", "identity 키 파일"), ("exit", "접속 끝내기")]),
  dict(name="tar", abbr=[("t", 1), ("ape ", 0), ("ar", 1), ("chive", 0)],
       mean="여러 파일을 하나로 묶고 푼다",
       term=[("cmd", "tar -czvf backup.tar.gz docs/"), ("arrow", "docs 폴더를 하나로 압축"), ("cmd", "tar -xzvf backup.tar.gz")],
       origin="1970년대 자기 테이프에 파일을 이어 기록하던 시절의 이름이다. 묶인 파일을 '타볼(tarball)'이라 부른다.",
       opts=[("c / x", "create 묶기 · extract 풀기"), ("z", "gzip 압축"), ("f", "file 파일 이름")]),
 ]),
]

TIPS = [("Tab", "이름 자동완성"), ("↑", "방금 쓴 명령 다시"), ("Control + C", "실행 중단"),
        ("Control + R", "지난 명령 검색"), ("Cmd + K", "화면 지우기")]


def term_html(lines):
    out = []
    for kind, text in lines:
        if kind == "cmd":
            out.append(f'<div class="ln"><span class="pr">%</span> {esc(text)}</div>')
        elif kind == "arrow":
            out.append(f'<div class="ln out"><span class="ar">→</span> {esc(text)}</div>')
        else:
            out.append(f'<div class="ln out">{esc(text)}</div>')
    return "".join(out)


def card(n, c):
    abbr = "".join(f'<b>{esc(t)}</b>' if hi else esc(t) for t, hi in c["abbr"])
    opts = "".join(f'<span class="opt"><code>{esc(f)}</code>{esc(d)}</span>' for f, d in c["opts"])
    return f"""
    <article class="card">
      <div class="c-id">
        <span class="no">{n:02d}</span>
        <h3>{esc(c["name"])}</h3>
        <p class="abbr">{abbr}</p>
        <p class="mean">{esc(c["mean"])}</p>
      </div>
      <div class="c-term"><div class="dots"><i></i><i></i><i></i></div>{term_html(c["term"])}</div>
      <div class="c-info">
        <p class="origin"><span class="tag">유래</span>{esc(c["origin"])}</p>
        <div class="opts">{opts}</div>
      </div>
    </article>"""


def page(i, pg):
    first = i == 0
    head = ""
    if first:
        head = """
    <header class="hero">
      <p class="eyebrow">MAC OS TERMINAL CHEAT SHEET</p>
      <h1>맥 터미널 필수 명령어 <span>20</span></h1>
      <p class="lead">사용 예시 · 유래 · 약어로 한 번에 익히기</p>
      <div class="howto">
        <span><b>터미널 여는 법</b> Cmd + Space → "터미널" → Enter</span>
        <span><b>읽는 법</b> 약어에서 <em>색 글자</em>가 명령어 이름이 된 부분</span>
      </div>
    </header>"""
    tips = ""
    if i == len(PAGES) - 1:
        tips = '<div class="tips"><span class="tips-title">손에 붙으면 빨라지는 키</span>' + "".join(
            f'<span class="tip"><kbd>{esc(k)}</kbd>{esc(d)}</span>' for k, d in TIPS) + "</div>"
    start = sum(len(p["cmds"]) for p in PAGES[:i])
    cards = "".join(card(start + k + 1, c) for k, c in enumerate(pg["cmds"]))
    return f"""
  <section class="page{' first' if first else ''}" style="--c:{pg['color']}; --t:{pg['tint']};">
    {head}
    <div class="band"><span class="pno">{i + 1} / {len(PAGES)}</span><h2>{esc(pg["theme"])}</h2><p>{esc(pg["sub"])}</p></div>
    <div class="cards">{cards}</div>
    {tips}
    <footer><span>「두 글자로 말하는 사람들」 맥 터미널 명령어 사전에서</span><span>zsh(%) 기준 · 예시 결과는 이해를 돕기 위한 것</span></footer>
  </section>"""


CSS = """
@page { size: 210mm 297mm; margin: 0; }
:root { --ink:#16211E; --muted:#5B6B65; --rule:#DCE2DE; --code:#17221F; --codeink:#E3EEE8; --codemuted:#93AAA0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background:#FFFFFF; color:var(--ink); font-family:'Noto Sans KR', sans-serif;
  -webkit-print-color-adjust:exact; print-color-adjust:exact; }
code, .c-term, kbd { font-family:'JetBrains Mono','Noto Sans KR',monospace; }
.page { width:210mm; height:297mm; padding:11mm 12mm 9mm; display:flex; flex-direction:column; page-break-after:always; overflow:hidden; }
.page:last-child { page-break-after:auto; }

.hero { padding-bottom:5mm; margin-bottom:4mm; border-bottom:1.2pt solid var(--ink); }
.eyebrow { font-size:7.5pt; font-weight:700; letter-spacing:.2em; color:var(--c); }
.hero h1 { font-family:'Gowun Batang', serif; font-size:30pt; font-weight:700; line-height:1.15; margin:2mm 0 1.5mm; letter-spacing:-.01em; }
.hero h1 span { color:#fff; background:var(--c); border-radius:4pt; padding:0 6pt; font-family:'JetBrains Mono',monospace; font-size:26pt; }
.lead { font-size:11pt; font-weight:500; color:var(--muted); }
.howto { display:flex; gap:8mm; margin-top:3mm; font-size:8.2pt; color:var(--muted); flex-wrap:wrap; }
.howto b { color:var(--ink); margin-right:4pt; }
.howto em { font-style:normal; color:var(--c); font-weight:700; text-decoration:underline; text-underline-offset:2pt; }

.band { display:flex; align-items:baseline; gap:4mm; background:var(--t); border-radius:6pt; padding:3.2mm 4.5mm; margin-bottom:3.5mm; }
.band .pno { font-family:'JetBrains Mono',monospace; font-size:8pt; font-weight:700; color:#fff; background:var(--c); border-radius:3pt; padding:1pt 5pt; }
.band h2 { font-family:'Gowun Batang', serif; font-size:15pt; font-weight:700; color:var(--ink); }
.band p { font-size:8.6pt; color:var(--muted); }

.cards { display:flex; flex-direction:column; gap:3mm; flex:1; }
.card { flex:1; display:grid; grid-template-columns:44mm 72mm 1fr; gap:4mm; align-items:stretch;
  border:0.8pt solid var(--rule); border-left:3.5pt solid var(--c); border-radius:6pt; padding:3.2mm 3.8mm; }
.c-id { display:flex; flex-direction:column; justify-content:center; }
.no { font-family:'JetBrains Mono',monospace; font-size:8pt; font-weight:700; color:var(--c); }
.c-id h3 { font-family:'JetBrains Mono',monospace; font-size:24pt; font-weight:700; line-height:1.05; margin:.5mm 0 1.5mm; letter-spacing:-.02em; }
.abbr { font-family:'JetBrains Mono','Noto Sans KR',monospace; font-size:8.8pt; color:var(--muted); line-height:1.35; }
.abbr b { color:var(--c); font-weight:700; text-decoration:underline; text-underline-offset:1.6pt; }
.mean { font-size:10pt; font-weight:700; color:var(--ink); margin-top:2mm; line-height:1.35; word-break:keep-all; }

.c-term { background:var(--code); border-radius:5pt; padding:2.4mm 3mm; color:var(--codeink); font-size:8.4pt; line-height:1.65;
  display:flex; flex-direction:column; justify-content:center; overflow:hidden; }
.dots { display:flex; gap:3pt; margin-bottom:1.6mm; }
.dots i { width:5pt; height:5pt; border-radius:50%; background:#FF5F57; display:block; }
.dots i:nth-child(2) { background:#FEBC2E; } .dots i:nth-child(3) { background:#28C840; }
.ln { white-space:pre-wrap; word-break:break-all; }
.ln .pr { color:#7BE0B7; font-weight:700; }
.ln.out { color:var(--codemuted); }
.ln .ar { color:#F0B375; }

.c-info { display:flex; flex-direction:column; justify-content:center; gap:2.2mm; }
.origin { font-size:8.8pt; line-height:1.55; color:var(--ink); word-break:keep-all; }
.tag { display:inline-block; font-size:6.8pt; font-weight:700; color:var(--c); background:var(--t); border-radius:3pt; padding:0 4pt; margin-right:4pt; vertical-align:1pt; }
.opts { display:flex; flex-wrap:wrap; gap:1.4mm; }
.opt { font-size:7.9pt; color:var(--muted); background:#F4F6F5; border-radius:3pt; padding:.6mm 1.8mm; }
.opt code { font-size:7.9pt; font-weight:700; color:var(--c); margin-right:3pt; }

.tips { margin-top:3.5mm; display:flex; flex-wrap:wrap; align-items:center; gap:2mm 4mm; border-top:1pt solid var(--rule); padding-top:3mm; }
.tips-title { font-family:'Gowun Batang',serif; font-weight:700; font-size:10pt; margin-right:2mm; }
.tip { font-size:8pt; color:var(--muted); }
kbd { font-size:7.6pt; font-weight:700; color:var(--ink); border:0.8pt solid var(--rule); border-bottom-width:1.8pt; border-radius:3pt; padding:0 4pt; margin-right:3pt; background:#FAFBFA; }

footer { margin-top:3mm; display:flex; justify-content:space-between; font-size:6.8pt; color:#9AA8A2; }
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700'
         '&family=Noto+Sans+KR:wght@400;500;700&family=JetBrains+Mono:wght@400;700&display=swap">')

doc = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>맥 터미널 필수 명령어 20</title>{FONTS}'
       f'<style>{CSS}</style></head><body>{"".join(page(i, p) for i, p in enumerate(PAGES))}</body></html>')
src = HERE / "infographic.html"
src.write_text(doc, encoding="utf-8")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", headless=True)
    pg = b.new_page()
    pg.goto(src.as_uri(), wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    pg.pdf(path=str(HERE / "infographic.pdf"), width="210mm", height="297mm", print_background=True,
           margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
    b.close()
print("ok", sum(len(p["cmds"]) for p in PAGES), "commands")
