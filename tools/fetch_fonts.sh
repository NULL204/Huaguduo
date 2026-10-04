#!/usr/bin/env bash
# Download the SIL OFL fonts used by the PV from Google Fonts into assets/fonts/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p assets/fonts

fetch() {  # fetch <css family query> <output file>
  local url
  url=$(curl -sS --max-time 60 "https://fonts.googleapis.com/css2?family=$1" | grep -oE 'https://[^)]+\.ttf' | head -1)
  [ -n "$url" ] || { echo "could not resolve $1" >&2; exit 1; }
  curl -sS --max-time 300 -o "assets/fonts/$2" "$url"
  echo "  $2"
}

echo "fetching fonts:"
fetch "Ma+Shan+Zheng"            MaShanZheng.ttf
fetch "Zhi+Mang+Xing"            ZhiMangXing.ttf
fetch "Liu+Jian+Mao+Cao"         LiuJianMaoCao.ttf
fetch "Long+Cang"                LongCang.ttf
fetch "Noto+Serif+SC:wght@400"   NotoSerifSC-Regular.ttf
fetch "Noto+Serif+SC:wght@900"   NotoSerifSC-Black.ttf
