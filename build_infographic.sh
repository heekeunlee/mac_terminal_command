#!/bin/zsh
# 인포그래픽 PDF 빌드: src/infographic → 맥_터미널_필수명령어_20.pdf
set -e
ROOT="$(cd "$(dirname "$0")" && pwd -P)"
cd "$ROOT/src/infographic"
python3 make.py
cp infographic.pdf "$ROOT/맥_터미널_필수명령어_20.pdf"
echo "완료: $ROOT/맥_터미널_필수명령어_20.pdf"
