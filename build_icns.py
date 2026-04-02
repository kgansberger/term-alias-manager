#!/usr/bin/env python3
"""
build_icns.py — creates assets/AppIcon.icns from the programmatic icon
Run once before py2app:  python3 build_icns.py
"""
import os, sys, subprocess, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
app = QApplication(sys.argv)

from main import _make_app_icon

assets = Path("assets")
assets.mkdir(exist_ok=True)
iconset = assets / "AppIcon.iconset"
iconset.mkdir(exist_ok=True)

sizes = {
    "icon_16x16.png":      16,
    "icon_16x16@2x.png":   32,
    "icon_32x32.png":      32,
    "icon_32x32@2x.png":   64,
    "icon_128x128.png":    128,
    "icon_128x128@2x.png": 256,
    "icon_256x256.png":    256,
    "icon_256x256@2x.png": 512,
    "icon_512x512.png":    512,
    "icon_512x512@2x.png": 1024,
}

icon = _make_app_icon()
for filename, size in sizes.items():
    pix = icon.pixmap(size, size)
    if pix.isNull():
        # fallback: paint manually at this size
        from PyQt6.QtGui import QPainter, QColor, QPainterPath, QBrush, QFont
        from PyQt6.QtCore import Qt
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
    pix.save(str(iconset / filename), "PNG")
    print(f"  {filename}")

result = subprocess.run(
    ["iconutil", "-c", "icns", str(iconset), "-o", str(assets / "AppIcon.icns")],
    capture_output=True, text=True
)
if result.returncode == 0:
    print(f"\n✅  assets/AppIcon.icns created")
    shutil.rmtree(iconset)
else:
    print(f"❌  iconutil error: {result.stderr}")
    sys.exit(1)
