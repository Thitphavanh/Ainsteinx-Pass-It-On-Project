#!/bin/bash
# Restore the ບອກຕໍ່ຄວາມຮູ້ pipeline into a fresh cloud session.
set -e
D=$(cd "$(dirname "$0")" && pwd)
mkdir -p /home/claude /root/fonts
cp -r "$D/geo" "$D/statue" "$D/ep1" "$D/ep3fix" /home/claude/
cp "$D"/fonts/*.ttf /root/fonts/
mkdir -p /home/claude/geo/out60 /home/claude/geo/vo60 /home/claude/geo/vo_in
cp "$D"/vo_in/* /home/claude/geo/vo_in/ 2>/dev/null || true
cd /home/claude/statue && npm install --silent three@0.160.0
pip install --break-system-packages -q playwright opencv-python-headless pillow numpy scikit-image >/dev/null 2>&1 || true
echo "pipeline ready: /home/claude/geo (UI + mix), /home/claude/statue (three.js 3D)"
