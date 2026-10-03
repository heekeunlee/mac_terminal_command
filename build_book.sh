#!/bin/zsh
# 책 PDF 빌드: src/book → 두_글자로_말하는_사람들.pdf
set -e
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
cd "$ROOT/src/book"
python3 build.py
cp terminal-book.pdf "$ROOT/두_글자로_말하는_사람들.pdf"
echo "완료: $ROOT/두_글자로_말하는_사람들.pdf"
