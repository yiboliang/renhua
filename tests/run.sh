#!/usr/bin/env bash
# 回归测试：tests/ai 必须全部 FAIL（检出），tests/human 必须全部 PASS（不误报）
cd "$(dirname "$0")/.."
miss=0; fp=0
for f in tests/ai/*.md; do python3 scripts/renhua_check.py "$f" >/dev/null && { echo "漏检 $f"; miss=$((miss+1)); }; done
for f in tests/human/*.md; do python3 scripts/renhua_check.py "$f" >/dev/null || { echo "误报 $f"; fp=$((fp+1)); }; done
na=$(ls tests/ai/*.md | wc -l); nh=$(ls tests/human/*.md | wc -l)
echo "检出 $((na-miss))/$na，误报 $fp/$nh"
[ $miss -eq 0 ] && [ $fp -eq 0 ]
