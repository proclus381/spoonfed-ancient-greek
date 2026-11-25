#!/bin/sh
# compact checker run: problems + coverage (without the long "used fewer" list).  usage: chk.sh [N lines]
cd "$(dirname "$0")/../project" || exit 1
PY=python3; [ -x ../.venv/bin/python ] && PY=../.venv/bin/python
$PY check2.py -q --cover $(ls sentences/ch[0-9][0-9].txt | sort) 2>&1 | grep -v "^used fewer" | cut -c1-1500 | tail -${1:-40}
