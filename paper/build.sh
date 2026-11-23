#!/bin/sh
# Build the submission PDF. Requires pandoc and a LaTeX engine (tectonic here).
#   ./build.sh [output.pdf]
set -eu
cd "$(dirname "$0")"
out="${1:-paper.pdf}"
pandoc --citeproc paper.md -o "$out" \
  --pdf-engine=tectonic \
  --include-in-header=header.tex \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V colorlinks=true -V linkcolor=blue -V urlcolor=blue -V citecolor=black
echo "wrote $out"
