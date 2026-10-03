# 두 글자로 말하는 사람들

**맥 터미널, 50개의 단어로 컴퓨터와 대화하는 법** — 맥 터미널 명령어 핸드북 전자책

- 소개 페이지 (제작 현황 · 주요 내용): https://heekeunlee.github.io/mac_terminal_command/
- 전자책 PDF (208쪽): [두_글자로_말하는_사람들.pdf](두_글자로_말하는_사람들.pdf)
- 필수 명령어 20 인포그래픽 (A4 4쪽): [맥_터미널_필수명령어_20.pdf](맥_터미널_필수명령어_20.pdf)

## 구성

| 부 | 내용 |
|---|---|
| 1부 · 두 글자 사전 | 터미널 기초 16문항, 명령어 50개(12개 장), 장별 빠른 참조표 |
| 2부 · 두 글자로 문제 풀기 | 13장 프로젝트 하루 따라 하기, 14장 문제 해결 사례 8가지 |

## 제작 현황

- 완료: 원고, 조판, 전자책 PDF, 인쇄용 사전 점검, 필수 20 인포그래픽
- 남은 일: 판권면·저자 정보, ISBN, 교보문고 POD 사양 확인, 펼침 표지

## 다시 만들기

```zsh
./build_book.sh          # 책 PDF
./build_infographic.sh   # 인포그래픽 PDF
```

필요한 것: Google Chrome, Python 패키지 `playwright` `pypdf` `pdfplumber` `reportlab` `pypdfium2`, 인터넷 연결(Google Fonts).

| 폴더 | 내용 |
|---|---|
| `src/book/` | 책 원고(`book.html`), 빌드(`build.py`), 내용 데이터, 폰트 |
| `src/infographic/` | 인포그래픽 생성(`make.py`) |
| `src/web-artifact/` | 초기 웹 버전 원본 |
| `assets/previews/` | 소개 페이지용 미리보기 이미지 |
