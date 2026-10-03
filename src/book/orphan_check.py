import re, pdfplumber
from cases import CASES
from walkthrough import STEPS
from content_data import EXAMPLES
from new_cmds import NEW
heads = {"형식", "유래", "주요 옵션", "상황별 예제", "명령어 해부", "명령어 해부 · 한 줄씩, 조각마다", "기억법", "꿀팁",
         "비하인드 스토리", "흔한 실수", "다음부터는", "책 밖의 도구", "증상", "이 장을 읽는 법", "이 장의 사례"}
for c in CASES:
    for ph in c["phases"]:
        heads.add(ph["title"])
for ex in list(EXAMPLES.values()) + [d["examples"] for d in NEW.values()]:
    for q, _, _ in ex:
        heads.add(q)
for st in STEPS:
    heads.add(st["title"])
bad = []
with pdfplumber.open("terminal-book.pdf") as pdf:
    for i, pg in enumerate(pdf.pages):
        lines = [l.strip() for l in (pg.extract_text() or "").split("\n")]
        lines = [l for l in lines if l and not l.startswith("PM_") and not re.fullmatch(r"\d+", l)]
        if not lines:
            continue
        for tail in lines[-3:]:
            core = re.sub(r"^(\d{2}\s*|Q\s*|[1-4]\s*(진단|원인|해결|확인)\s*)", "", tail).strip()
            if core in heads or any(core.endswith(h) for h in heads if len(h) > 6):
                bad.append((i, tail)); break
print("orphaned headings:", len(bad))
for b in bad: print("  pdf page", b[0], "->", b[1])
