"""
main.py — TermLink: Terminal Project Alias Manager
PyQt6 GUI — macOS & Windows
"""

import platform
import subprocess
import sys
from pathlib import Path

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

if IS_MAC:
    import plistlib

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QColor, QIcon, QPainter, QPainterPath, QPalette, QPixmap, QBrush,
)
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QStatusBar,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

sys.path.insert(0, str(Path(__file__).parent / "src"))
from zshrc_parser import AliasEntry, read_aliases, write_aliases, SHELL_CONFIG
from version import __version__ as APP_VERSION


# ── Design tokens ──────────────────────────────────────────────────────────
ACCENT     = "#007AFF"
ACCENT_HOV = "#0062CC"
ACCENT_PRS = "#004EA6"
DANGER     = "#FF3B30"
DANGER_HOV = "#CC2F25"
DANGER_PRS = "#A32620"
BG_CARD    = "#F2F2F7"
BG_CODE    = "#1E1E2E"
FG_CODE    = "#CDD6F4"
BORDER     = "#D1D1D6"

PLIST_ID   = "dev.termlink.app"
PLIST_PATH = Path.home() / f"Library/LaunchAgents/{PLIST_ID}.plist" if IS_MAC else Path()
PYTHON_BIN = subprocess.run(
    ["where", "python"] if IS_WIN else ["which", "python3"],
    capture_output=True, text=True
).stdout.strip().splitlines()[0]
MAIN_PY    = str(Path(__file__).resolve())


# ── App icon ───────────────────────────────────────────────────────────────
def _make_app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 32, 64, 128, 256, 512):
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        r = size * 0.22
        path.addRoundedRect(0, 0, size, size, r, r)
        p.fillPath(path, QBrush(QColor("#1E2A3A")))
        from PyQt6.QtGui import QFont
        f = QFont("Menlo")
        f.setBold(True)
        f.setPixelSize(max(6, int(size * 0.38)))
        p.setFont(f)
        p.setPen(QColor("#00D9FF"))
        p.drawText(pix.rect().adjusted(int(size*0.08), int(size*0.08),
                                       -int(size*0.04), -int(size*0.18)),
                   Qt.AlignmentFlag.AlignCenter, ">_")
        dr = max(2, int(size * 0.11))
        cx = size - int(size * 0.18)
        cy = size - int(size * 0.18)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#FFB300")))
        p.drawEllipse(cx - dr, cy - dr, dr * 2, dr * 2)
        p.end()
        icon.addPixmap(pix)
    return icon


# ── Autostart helpers ────────────────────────────────────────────────────────
def _autostart_enabled() -> bool:
    if IS_MAC:
        return PLIST_PATH.exists()
    if IS_WIN:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "TermLink")
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    return False

def _set_autostart(enable: bool):
    if IS_MAC:
        if enable:
            plist = {
                "Label":             PLIST_ID,
                "ProgramArguments":  [PYTHON_BIN, MAIN_PY],
                "RunAtLoad":         True,
                "KeepAlive":         False,
                "StandardOutPath":   str(Path.home() / "Library/Logs/TermLink.log"),
                "StandardErrorPath": str(Path.home() / "Library/Logs/TermLink.log"),
            }
            PLIST_PATH.write_bytes(plistlib.dumps(plist))
            subprocess.run(["launchctl", "load", str(PLIST_PATH)], capture_output=True)
        else:
            if PLIST_PATH.exists():
                subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True)
                PLIST_PATH.unlink()
    elif IS_WIN:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, "TermLink", 0, winreg.REG_SZ, f'"{MAIN_PY}"')
            else:
                try:
                    winreg.DeleteValue(key, "TermLink")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[autostart error] {e}")


# ── Widget helpers ────────────────────────────────────────────────────────
def _btn(text, bg=ACCENT, hover=ACCENT_HOV, pressed=ACCENT_PRS, min_w=90):
    b = QPushButton(text)
    b.setMinimumWidth(min_w)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{bg}; color:white; border:none;
            border-radius:7px; padding:6px 16px;
            font-size:13px; font-weight:600;
        }}
        QPushButton:hover   {{ background:{hover};   color:white; }}
        QPushButton:pressed {{ background:{pressed}; color:white; }}
        QPushButton:disabled{{ background:#C7C7CC;   color:white; }}
    """)
    return b


def _ghost_btn(text):
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background:transparent; color:{ACCENT};
            border:1.5px solid {ACCENT};
            border-radius:7px; padding:5px 14px; font-size:13px;
        }}
        QPushButton:hover  {{ background:#E5F0FF; color:{ACCENT_HOV}; border-color:{ACCENT_HOV}; }}
        QPushButton:pressed{{ background:#CCE0FF; color:{ACCENT_PRS}; border-color:{ACCENT_PRS}; }}
    """)
    return b


def _icon_btn(symbol: str, tooltip: str) -> QPushButton:
    b = QPushButton(symbol)
    b.setFixedSize(32, 32)
    b.setToolTip(tooltip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{
            background: transparent; color: {ACCENT};
            border: 1.5px solid {BORDER}; border-radius: 7px;
            font-size: 13px;
        }}
        QPushButton:hover   {{ background: #E5F0FF; border-color: {ACCENT}; }}
        QPushButton:pressed {{ background: #CCE0FF; }}
        QPushButton:disabled{{ color: #C7C7CC; border-color: #E5E5EA; }}
    """)
    return b


def _lbl(text):
    l = QLabel(text)
    l.setStyleSheet("color:#8E8E93; font-size:11px; font-weight:600; letter-spacing:0.5px;")
    return l


def _field(ph=""):
    f = QLineEdit()
    f.setPlaceholderText(ph)
    f.setStyleSheet(f"""
        QLineEdit {{
            border:1.5px solid {BORDER}; border-radius:7px;
            padding:6px 10px; font-size:13px; background:white;
        }}
        QLineEdit:focus {{ border-color:{ACCENT}; }}
    """)
    return f


def _section_label(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet(
        "font-size:13px; font-weight:700; color:#1C1C1E; margin-top:8px;")
    return l


def _divider() -> QWidget:
    w = QWidget()
    w.setFixedHeight(1)
    w.setStyleSheet(f"background:{BORDER};")
    return w


# ── Drag-drop path field ───────────────────────────────────────────────────
class PathDropField(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setPlaceholderText("Drag folder here  or click Browse…")
        self.setStyleSheet(f"""
            QLineEdit {{
                border:1.5px dashed {ACCENT}; border-radius:7px;
                padding:6px 10px; font-size:13px; background:white;
            }}
            QLineEdit:focus {{ border-style:solid; border-color:{ACCENT}; }}
        """)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        urls = e.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            home = str(Path.home())
            if path.startswith(home):
                path = "~" + path[len(home):]
            self.setText(path)


# ── Help dialog ────────────────────────────────────────────────────────────
HELP_HTML = """
<style>
  body { font-family:-apple-system,sans-serif; font-size:13px;
         color:#1C1C1E; line-height:1.6; }
  h2   { color:#007AFF; margin-bottom:4px; }
  h3   { color:#3A3A3C; margin-top:14px; margin-bottom:2px; }
  code { background:#F2F2F7; border-radius:4px;
         padding:1px 5px; font-family:Menlo,monospace; font-size:12px; }
  pre  { background:#1E1E2E; color:#CDD6F4; border-radius:8px;
         padding:10px 14px; font-family:Menlo,monospace; font-size:12px; }
  ul,ol{ padding-left:18px; }
  li   { margin-bottom:4px; }
  .tip { background:#E5F0FF; border-left:3px solid #007AFF;
         border-radius:4px; padding:8px 12px; margin:8px 0; font-size:12px; }
</style>

<h2>⌨️ TermLink — Terminal Project Alias Manager</h2>
<p>TermLink manages shell aliases in your <code>~/.zshrc</code> that jump you into
any project folder in one keystroke — with an optional tab title and a startup
command that runs automatically.</p>

<div class="tip">
  💡 <b>The fast lane:</b> Instead of <code>cd ~/Projects/myapp &amp;&amp; claude</code>
  every time — just type <code>aichat</code>. One word. Done.
</div>

<h3>🚀 What does an alias do?</h3>
<pre>alias aichat='cd ~/Projects/myapp &amp;&amp; printf "\033]0;AI Chat\007" &amp;&amp; claude'</pre>
<ul>
  <li>Changes into <code>~/Projects/myapp</code></li>
  <li>Sets the iTerm2 tab title to <b>AI Chat</b> immediately</li>
  <li>Launches <code>claude</code> — tab title is already set before it starts</li>
</ul>

<h3>💡 Form fields</h3>
<ul>
  <li><b>Alias Name</b> — the command you type in the terminal</li>
  <li><b>Folder Path</b> — target folder for <code>cd</code> (optional, drag &amp; drop)</li>
  <li><b>Command</b> — runs after cd: <code>claude</code>, <code>gsd</code>,
      <code>pnpm run dev</code>, <code>python main.py</code> (optional)</li>
  <li><b>Tab Title</b> — sets the iTerm2 tab name, always before the command (optional)</li>
</ul>

<h3>📋 Examples</h3>
<pre># Jump to a project:
alias cdapi='cd ~/Projects/my-api'

# Open Claude Code:
alias aichat='cd ~/Projects/ai-chat &amp;&amp; printf "\033]0;AI Chat\007" &amp;&amp; claude'

# Start a GSD session:
alias plan='cd ~/Projects/myapp &amp;&amp; printf "\033]0;Planning\007" &amp;&amp; gsd'

# Full dev stack:
alias dev='cd ~/Projects/myapp &amp;&amp; printf "\033]0;Dev\007" &amp;&amp; pnpm run dev'

# Standalone command (no folder):
alias k9sprod='k9s --context production'</pre>

<h3>▶ Run button</h3>
<p>Opens a new iTerm2 tab and executes the alias directly from the app —
no terminal switching needed. Only active when the alias is saved and unchanged.</p>

<h3>✏️ Editable preview</h3>
<p>The preview at the bottom can be edited manually for advanced use cases.
Click <b>↺ Reset</b> to restore the auto-generated alias line.</p>

<h3>🔒 Safe editing</h3>
<p>TermLink only touches the marked block in your <code>~/.zshrc</code>:</p>
<pre># BEGIN project-aliases
# [project-alias]
alias dev='cd ~/Projects/myapp &amp;&amp; printf "\033]0;Dev\007" &amp;&amp; pnpm run dev'
# END project-aliases</pre>

<h3>💾 Automatic backup</h3>
<p>Before every change, <code>~/.zshrc.backup</code> is created automatically.</p>

<h3>🔄 Instantly active</h3>
<p>After saving, <code>source ~/.zshrc</code> runs automatically.
Open a <b>new iTerm2 tab</b> — your alias is ready immediately.</p>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TermLink — Help")
        self.setMinimumSize(520, 560)
        if parent:
            self.setWindowIcon(parent.windowIcon())
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 12)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        inner = QLabel()
        inner.setTextFormat(Qt.TextFormat.RichText)
        inner.setWordWrap(True)
        inner.setText(HELP_HTML)
        inner.setContentsMargins(24, 20, 24, 20)
        inner.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(inner)
        lay.addWidget(scroll)
        row = QHBoxLayout()
        row.addStretch()
        close = _btn("Close", min_w=80)
        close.clicked.connect(self.accept)
        row.addWidget(close)
        row.setContentsMargins(12, 0, 12, 0)
        lay.addLayout(row)


# ── Settings tab ──────────────────────────────────────────────────────────
class SettingsWidget(QWidget):
    def __init__(self, status_bar, parent=None):
        super().__init__(parent)
        self._status = status_bar
        self.setStyleSheet("background:white;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(0)

        # ── Section: General ───────────────────────────────────────────
        lay.addWidget(_section_label("⚙️  General"))
        lay.addSpacing(10)

        # Autostart row
        row_auto = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("Launch at login")
        t.setStyleSheet("font-size:13px; color:#1C1C1E;")
        sub = QLabel("TermLink starts at login via LaunchAgent (macOS) / Registry (Windows)")
        sub.setStyleSheet("font-size:11px; color:#8E8E93;")
        col.addWidget(t)
        col.addWidget(sub)
        row_auto.addLayout(col)
        row_auto.addStretch()
        self.autostart_cb = _toggle_switch()
        self.autostart_cb.setChecked(_autostart_enabled())
        self.autostart_cb.checkStateChanged.connect(self._on_autostart_toggle)
        row_auto.addWidget(self.autostart_cb)
        lay.addLayout(row_auto)

        lay.addSpacing(16)
        lay.addWidget(_divider())
        lay.addSpacing(16)

        # ── Section: Shell ─────────────────────────────────────────────
        lay.addWidget(_section_label("🐚  Shell"))
        lay.addSpacing(10)

        # Editor row
        row_ed = QHBoxLayout()
        col_ed = QVBoxLayout()
        col_ed.setSpacing(2)
        shell_file = "~/.zshrc" if IS_MAC else "%USERPROFILE%\\.bashrc (WSL/Git Bash)"
        t_ed = QLabel(f"Editor for {shell_file}")
        t_ed.setStyleSheet("font-size:13px; color:#1C1C1E;")
        sub_ed = QLabel('Used when clicking "Open"')
        sub_ed.setStyleSheet("font-size:11px; color:#8E8E93;")
        col_ed.addWidget(t_ed)
        col_ed.addWidget(sub_ed)
        row_ed.addLayout(col_ed)
        row_ed.addStretch()
        from PyQt6.QtWidgets import QComboBox
        self.editor_combo = QComboBox()
        if IS_WIN:
            self.editor_combo.addItems(["Notepad", "VS Code", "Cursor", "Notepad++", "Sublime Text"])
        else:
            self.editor_combo.addItems(["TextEdit", "VS Code", "Cursor", "Zed", "Sublime Text", "nano (Terminal)"])
        self.editor_combo.setFixedWidth(150)
        self.editor_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1.5px solid {BORDER}; border-radius: 7px;
                padding: 5px 10px; font-size: 13px; background: white;
            }}
            QComboBox:focus {{ border-color: {ACCENT}; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        row_ed.addWidget(self.editor_combo)
        lay.addLayout(row_ed)

        lay.addSpacing(14)

        # Shell config path row
        row_zsh = QHBoxLayout()
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        from zshrc_parser import SHELL_CONFIG
        t2 = QLabel("Shell config file")
        t2.setStyleSheet("font-size:13px; color:#1C1C1E;")
        self.zshrc_path_lbl = QLabel(str(SHELL_CONFIG))
        self.zshrc_path_lbl.setStyleSheet("font-size:11px; color:#8E8E93; font-family:Menlo,monospace;")
        col2.addWidget(t2)
        col2.addWidget(self.zshrc_path_lbl)
        row_zsh.addLayout(col2)
        row_zsh.addStretch()
        open_zsh_btn = _ghost_btn("Open")
        open_zsh_btn.setFixedWidth(80)
        open_zsh_btn.clicked.connect(self._open_zshrc)
        row_zsh.addWidget(open_zsh_btn)
        lay.addLayout(row_zsh)

        lay.addSpacing(16)
        lay.addWidget(_divider())
        lay.addSpacing(16)

        # ── Section: Backup ────────────────────────────────────────────
        lay.addWidget(_section_label("💾  Backup"))
        lay.addSpacing(10)

        row_bak = QHBoxLayout()
        col3 = QVBoxLayout()
        col3.setSpacing(2)
        t3 = QLabel("Show backup file")
        t3.setStyleSheet("font-size:13px; color:#1C1C1E;")
        from zshrc_parser import BACKUP
        sub3 = QLabel(f"Created before every change: {BACKUP}")
        sub3.setStyleSheet("font-size:11px; color:#8E8E93; font-family:Menlo,monospace;")
        col3.addWidget(t3)
        col3.addWidget(sub3)
        row_bak.addLayout(col3)
        row_bak.addStretch()
        open_bak_btn = _ghost_btn("Show")
        open_bak_btn.setFixedWidth(90)
        open_bak_btn.clicked.connect(self._show_backup)
        row_bak.addWidget(open_bak_btn)
        lay.addLayout(row_bak)

        lay.addSpacing(16)
        lay.addWidget(_divider())
        lay.addSpacing(16)

        # ── Section: Info ──────────────────────────────────────────────
        lay.addWidget(_section_label("ℹ️  Info"))
        lay.addSpacing(10)

        info_lay = QVBoxLayout()
        info_lay.setSpacing(4)
        for k, v in [
            ("Version", APP_VERSION),
            ("Developer", "klausinger"),
            ("Platform", platform.system()),
            ("Python", sys.version.split()[0]),
        ]:
            row = QHBoxLayout()
            kl = QLabel(k)
            kl.setStyleSheet("font-size:13px; color:#8E8E93; min-width:100px;")
            vl = QLabel(v)
            vl.setStyleSheet("font-size:13px; color:#1C1C1E;")
            row.addWidget(kl)
            row.addWidget(vl)
            row.addStretch()
            info_lay.addLayout(row)
        lay.addLayout(info_lay)

        lay.addStretch()

    def _on_autostart_toggle(self, state):
        enable = (state == Qt.CheckState.Checked)
        _set_autostart(enable)
        msg = "✓  Autostart aktiviert" if enable else "Autostart deaktiviert"
        self._status.showMessage(msg)

    def _open_zshrc(self):
        from zshrc_parser import SHELL_CONFIG
        path = str(SHELL_CONFIG)
        editor = self.editor_combo.currentText()
        if IS_WIN:
            app_map = {
                "VS Code":     "code",
                "Cursor":      "cursor",
                "Notepad++":   "notepad++",
                "Sublime Text":"subl",
                "Notepad":     "notepad",
            }
            cmd = app_map.get(editor, "notepad")
            subprocess.Popen([cmd, path])
        else:
            app_map = {
                "VS Code":      "Visual Studio Code",
                "Cursor":       "Cursor",
                "Zed":          "Zed",
                "Sublime Text": "Sublime Text",
                "TextEdit":     "TextEdit",
            }
            if editor == "nano (Terminal)":
                osascript = (
                    'tell application "iTerm2"\n'
                    '    activate\n'
                    '    tell current window\n'
                    '        create tab with default profile\n'
                    '        tell current session of current tab\n'
                    f'            write text "nano {path}"\n'
                    '        end tell\n'
                    '    end tell\n'
                    'end tell'
                )
                subprocess.run(["osascript", "-e", osascript])
            elif editor in app_map:
                subprocess.run(["open", "-a", app_map[editor], path])
            else:
                subprocess.run(["open", "-t", path])

    def _show_backup(self):
        from zshrc_parser import BACKUP
        bak = Path(BACKUP)
        if bak.exists():
            if IS_WIN:
                subprocess.Popen(["explorer", "/select,", str(bak)])
            else:
                subprocess.run(["open", "-R", str(bak)])
        else:
            QMessageBox.information(None, "No backup", "No backup file found yet.")


def _toggle_switch() -> QCheckBox:
    """Styled checkbox that looks like a macOS toggle."""
    cb = QCheckBox()
    cb.setStyleSheet(f"""
        QCheckBox {{
            spacing: 0px;
        }}
        QCheckBox::indicator {{
            width: 38px; height: 22px;
            border-radius: 11px;
            border: none;
            background: #D1D1D6;
        }}
        QCheckBox::indicator:checked {{
            background: {ACCENT};
        }}
        QCheckBox::indicator:hover {{
            background: #C0C0C8;
        }}
        QCheckBox::indicator:checked:hover {{
            background: {ACCENT_HOV};
        }}
    """)
    return cb


# ── Main window ────────────────────────────────────────────────────────────
class TermLinkWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TermLink")
        self.setMinimumSize(860, 580)
        self._aliases: list[AliasEntry] = []
        self._editing_index: int | None = None
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet(f"background:{ACCENT};")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(18, 0, 18, 0)
        t = QLabel("⌨️  TermLink")
        t.setStyleSheet("color:white; font-size:17px; font-weight:700;")
        hl.addWidget(t)
        hl.addStretch()
        s = QLabel("Terminal Project Alias Manager")
        s.setStyleSheet("color:rgba(255,255,255,.75); font-size:12px;")
        hl.addWidget(s)
        hb = QPushButton("?")
        hb.setFixedSize(26, 26)
        hb.setCursor(Qt.CursorShape.PointingHandCursor)
        hb.setStyleSheet("""
            QPushButton {
                background:rgba(255,255,255,.25); color:white;
                border:1.5px solid rgba(255,255,255,.5);
                border-radius:13px; font-size:13px; font-weight:700; margin-left:10px;
            }
            QPushButton:hover  { background:rgba(255,255,255,.40); }
            QPushButton:pressed{ background:rgba(255,255,255,.20); }
        """)
        hb.clicked.connect(lambda: HelpDialog(self).exec())
        hl.addWidget(hb)
        root.addWidget(hdr)

        # ── Tab widget ────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: white;
            }}
            QTabBar::tab {{
                background: {BG_CARD};
                color: #8E8E93;
                padding: 8px 22px;
                font-size: 13px;
                font-weight: 500;
                border-bottom: 2px solid transparent;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                color: {ACCENT};
                background: white;
                border-bottom: 2px solid {ACCENT};
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                color: #3A3A3C;
                background: #EAEAEF;
            }}
        """)

        # Tab 1 — Aliases
        aliases_tab = self._build_aliases_tab()
        self.tabs.addTab(aliases_tab, "⌨️  Aliases")

        # Tab 2 — Einstellungen (populated after status bar is created)
        self._settings_placeholder = QWidget()
        self.tabs.addTab(self._settings_placeholder, "⚙️  Einstellungen")

        root.addWidget(self.tabs, 1)

        # ── Status bar ────────────────────────────────────────────────
        self.status = QStatusBar()
        self.status.setStyleSheet(
            f"background:{BG_CARD}; color:#8E8E93; font-size:11px;")
        self.status.showMessage("Ready")
        made_by = QLabel("made by klausinger")
        made_by.setStyleSheet("color:#C7C7CC; font-size:10px; padding-right:8px;")
        self.status.addPermanentWidget(made_by)
        root.addWidget(self.status)

        # Now build settings tab with reference to status bar
        settings_tab = SettingsWidget(self.status, self)
        self.tabs.removeTab(1)
        self.tabs.addTab(settings_tab, "⚙️  Einstellungen")

    # ── Aliases tab ───────────────────────────────────────────────────
    def _build_aliases_tab(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background:white;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        sp = QSplitter(Qt.Orientation.Horizontal)
        sp.setHandleWidth(1)
        sp.setStyleSheet(f"QSplitter::handle{{ background:{BORDER}; }}")

        # ── LEFT ──────────────────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(220)
        left.setStyleSheet(f"background:{BG_CARD};")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 14, 12, 12)
        ll.setSpacing(8)

        lhdr = QHBoxLayout()
        lhdr.addWidget(_lbl("ALIASES"))
        lhdr.addStretch()
        reb = _icon_btn("↺", "Aliases neu laden")
        reb.setFixedSize(28, 28)
        reb.clicked.connect(self._load)
        lhdr.addWidget(reb)
        nb = _btn("＋ New", min_w=70)
        nb.clicked.connect(self._on_new)
        lhdr.addWidget(nb)
        ll.addLayout(lhdr)

        # ── Suchfeld ──────────────────────────────────────────────────
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍  Suchen…")
        self.search_field.setClearButtonEnabled(True)
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {BORDER}; border-radius: 7px;
                padding: 5px 10px; font-size: 12px; background: white;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """)
        self.search_field.textChanged.connect(self._on_search)
        ll.addWidget(self.search_field)

        # ── Sort-Buttons ───────────────────────────────────────────────
        sort_row = QHBoxLayout()
        sort_row.setSpacing(4)
        self._sort_mode = "manual"   # "manual" | "az" | "za"
        self.sort_az_btn = QPushButton("A→Z")
        self.sort_za_btn = QPushButton("Z→A")
        for b in (self.sort_az_btn, self.sort_za_btn):
            b.setFixedHeight(24)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setCheckable(True)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: white; color: #8E8E93;
                    border: 1.5px solid {BORDER}; border-radius: 5px;
                    font-size: 11px; font-weight: 600; padding: 0 8px;
                }}
                QPushButton:checked {{
                    background: {ACCENT}; color: white; border-color: {ACCENT};
                }}
                QPushButton:hover:!checked {{ background: #F0F6FF; color: {ACCENT}; border-color: {ACCENT}; }}
            """)
        self.sort_az_btn.clicked.connect(lambda: self._set_sort("az"))
        self.sort_za_btn.clicked.connect(lambda: self._set_sort("za"))
        sort_row.addWidget(self.sort_az_btn)
        sort_row.addWidget(self.sort_za_btn)
        sort_row.addStretch()
        ll.addLayout(sort_row)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                border:1.5px solid {BORDER}; border-radius:8px;
                background:white; font-size:13px; outline:none;
            }}
            QListWidget::item {{ padding:8px 10px; }}
            QListWidget::item:selected {{ background:#E5F0FF; color:#1C1C1E; border-left:3px solid {ACCENT}; }}
            QListWidget::item:hover    {{ background:#F0F6FF; }}
        """)
        self.list_widget.currentRowChanged.connect(self._on_select)
        ll.addWidget(self.list_widget)

        # ── Untere Buttons: Copy + Delete ──────────────────────────────
        bottom_row = QHBoxLayout()
        self.copy_alias_btn = _icon_btn("⎘", "Alias duplizieren")
        self.copy_alias_btn.setFixedSize(34, 34)
        self.copy_alias_btn.setEnabled(False)
        self.copy_alias_btn.clicked.connect(self._on_duplicate)
        bottom_row.addWidget(self.copy_alias_btn)
        bottom_row.addStretch()
        self.del_btn = _btn("Delete", bg=DANGER, hover=DANGER_HOV, pressed=DANGER_PRS)
        self.del_btn.clicked.connect(self._on_delete)
        bottom_row.addWidget(self.del_btn)
        ll.addLayout(bottom_row)
        sp.addWidget(left)

        # ── RIGHT ─────────────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("background:white;")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(24, 20, 24, 16)
        rl.setSpacing(12)

        self.form_title = QLabel("New Alias")
        self.form_title.setStyleSheet(
            "font-size:18px; font-weight:700; color:#1C1C1E;")
        rl.addWidget(self.form_title)

        # Name + Run button
        rl.addWidget(_lbl("ALIAS NAME"))
        name_row = QHBoxLayout()
        self.name_field = _field("e.g.  cdmyapp  /  dev  /  aichat")
        self.name_field.textChanged.connect(self._update_preview)
        name_row.addWidget(self.name_field)
        self.run_btn = QPushButton("▶  Ausführen")
        self.run_btn.setEnabled(False)
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setFixedHeight(34)
        self.run_btn.setMinimumWidth(120)
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background: #34C759; color: white; border: none;
                border-radius: 7px; padding: 0 16px;
                font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover   {{ background: #28A745; }}
            QPushButton:pressed {{ background: #1E7E34; }}
            QPushButton:disabled{{ background: #C7C7CC; color: white; }}
        """)
        self.run_btn.clicked.connect(self._on_run_alias)
        name_row.addWidget(self.run_btn)
        rl.addLayout(name_row)

        # Path
        rl.addWidget(_lbl("FOLDER PATH  (optional — drag & drop or Browse)"))
        pr = QHBoxLayout()
        self.path_field = PathDropField()
        self.path_field.textChanged.connect(self._update_preview)
        self.path_field.textChanged.connect(self._on_path_changed)
        pr.addWidget(self.path_field)
        bb = _ghost_btn("Browse…")
        bb.clicked.connect(self._on_browse)
        pr.addWidget(bb)
        open_finder_btn = _icon_btn("📂", "Im Finder öffnen")
        open_finder_btn.clicked.connect(self._on_open_finder)
        pr.addWidget(open_finder_btn)
        open_iterm_btn = _icon_btn(">_", "In iTerm2 öffnen")
        open_iterm_btn.clicked.connect(self._on_open_iterm)
        pr.addWidget(open_iterm_btn)
        self.open_finder_btn = open_finder_btn
        self.open_iterm_btn  = open_iterm_btn
        rl.addLayout(pr)

        # Command
        rl.addWidget(_lbl("COMMAND  (optional — runs after cd)"))
        self.cmd_field = _field("e.g.  pnpm run dev  /  claude  /  gsd  /  python main.py")
        self.cmd_field.textChanged.connect(self._update_preview)
        rl.addWidget(self.cmd_field)

        # Tab title
        rl.addWidget(_lbl("TAB TITLE  (optional — set before command)"))
        self.title_field = _field("e.g.  MyProject  /  AI Chat  /  Dev")
        self.title_field.textChanged.connect(self._update_preview)
        rl.addWidget(self.title_field)

        # Preview
        prev_hdr = QHBoxLayout()
        prev_hdr.addWidget(_lbl("PREVIEW"))
        prev_hdr.addStretch()
        self.copy_btn = QPushButton("⎘ Copy")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setEnabled(False)
        self.copy_btn.setFixedHeight(22)
        self.copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: #8E8E93;
                border: 1px solid #C7C7CC; border-radius: 5px;
                padding: 0px 8px; font-size: 11px;
            }}
            QPushButton:enabled       {{ color:{ACCENT}; border-color:{ACCENT}; }}
            QPushButton:enabled:hover {{ background:#E5F0FF; }}
            QPushButton:enabled:pressed{{ background:#CCE0FF; }}
        """)
        self.copy_btn.clicked.connect(self._on_copy_preview)
        prev_hdr.addWidget(self.copy_btn)
        rl.addLayout(prev_hdr)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFixedHeight(58)
        self.preview.setStyleSheet(f"""
            QTextEdit {{
                background:{BG_CODE}; color:{FG_CODE};
                border-radius:8px; padding:8px 12px;
                font-family:"SF Mono",Menlo,monospace; font-size:12px; border:none;
            }}
        """)
        rl.addWidget(self.preview)

        # Buttons
        br = QHBoxLayout()
        br.addStretch()
        cc = _ghost_btn("Cancel")
        cc.clicked.connect(self._on_cancel)
        br.addWidget(cc)
        self.save_btn = _btn("Save & Reload", min_w=130)
        self.save_btn.clicked.connect(self._on_save)
        br.addWidget(self.save_btn)
        rl.addLayout(br)
        rl.addStretch()

        sp.addWidget(right)
        sp.setSizes([240, 620])
        lay.addWidget(sp, 1)
        return container

    # ── Data ──────────────────────────────────────────────────────────────
    def _load(self):
        self._aliases = read_aliases()
        self._visible_indices = []
        self._refresh_list()
        self._clear_form()
        n = len(self._aliases)
        self.status.showMessage(f"Loaded {n} alias{'es' if n != 1 else ''} from {SHELL_CONFIG}")

    def _refresh_list(self, select_name: str | None = None):
        """Listet Aliases gefiltert nach Suche und sortiert nach _sort_mode."""
        query = self.search_field.text().strip().lower() if hasattr(self, "search_field") else ""

        # Sortierung
        items = list(enumerate(self._aliases))  # (original_idx, alias)
        if self._sort_mode == "az":
            items.sort(key=lambda x: x[1].name.lower())
        elif self._sort_mode == "za":
            items.sort(key=lambda x: x[1].name.lower(), reverse=True)

        # Suche
        if query:
            items = [(i, a) for i, a in items
                     if query in a.name.lower()
                     or query in a.path.lower()
                     or query in a.command.lower()]

        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self._visible_indices = []   # mapping: list-row → _aliases-index
        for orig_idx, a in items:
            label = a.name
            if a.command:
                label += f"  ›  {a.command.split()[0]}"
            item = QListWidgetItem(f"  {label}")
            item.setToolTip(a.to_zsh_line())
            self.list_widget.addItem(item)
            self._visible_indices.append(orig_idx)
        self.list_widget.blockSignals(False)

        # Nach Reload: vorher selektierten Eintrag wieder markieren
        if select_name:
            for row, orig_idx in enumerate(self._visible_indices):
                if self._aliases[orig_idx].name == select_name:
                    self.list_widget.setCurrentRow(row)
                    return
        self.list_widget.setCurrentRow(-1)

    def _set_sort(self, mode: str):
        if self._sort_mode == mode:
            mode = "manual"
        self._sort_mode = mode
        self.sort_az_btn.setChecked(mode == "az")
        self.sort_za_btn.setChecked(mode == "za")
        # merke aktuell selektierten Namen
        name = self._aliases[self._editing_index].name if self._editing_index is not None else None
        self._refresh_list(select_name=name)

    def _on_search(self, _text: str):
        name = self._aliases[self._editing_index].name if self._editing_index is not None else None
        self._refresh_list(select_name=name)

    def _on_duplicate(self):
        """Dupliziert den aktuellen Alias mit leerem Namen und zeigt ihn sofort im Formular."""
        idx = self._editing_index
        if idx is None:
            return
        src = self._aliases[idx]
        # Formular mit kopierten Werten befüllen, Name leer lassen
        self.list_widget.clearSelection()
        self._editing_index = None
        self.form_title.setText("Kopie von — " + src.name)
        for w in (self.name_field, self.path_field, self.cmd_field, self.title_field):
            w.blockSignals(True)
        self.name_field.clear()
        self.path_field.setText(src.path)
        self.cmd_field.setText(src.command)
        self.title_field.setText(src.title)
        for w in (self.name_field, self.path_field, self.cmd_field, self.title_field):
            w.blockSignals(False)
        self.run_btn.setEnabled(False)
        self.copy_alias_btn.setEnabled(False)
        self.del_btn.setEnabled(False)
        self.open_finder_btn.setEnabled(bool(src.path))
        self.open_iterm_btn.setEnabled(bool(src.path))
        self._update_preview()
        self.name_field.setFocus()
        self.status.showMessage(f"⎘  Copy of '{src.name}' — enter a new alias name")

    # ── Form ──────────────────────────────────────────────────────────────
    def _clear_form(self):
        self._editing_index = None
        self.form_title.setText("New Alias")
        self.name_field.clear()
        self.path_field.clear()
        self.cmd_field.clear()
        self.title_field.clear()
        self.preview.setPlainText("")
        self.copy_btn.setEnabled(False)
        self.run_btn.setEnabled(False)
        self.copy_alias_btn.setEnabled(False)
        self.open_finder_btn.setEnabled(False)
        self.open_iterm_btn.setEnabled(False)
        self.del_btn.setEnabled(False)

    def _populate_form(self, idx: int):
        a = self._aliases[idx]
        self._editing_index = idx
        self.form_title.setText(f"Edit — {a.name}")
        for w in (self.name_field, self.path_field, self.cmd_field, self.title_field):
            w.blockSignals(True)
        self.name_field.setText(a.name)
        self.path_field.setText(a.path)
        self.cmd_field.setText(a.command)
        self.title_field.setText(a.title)
        for w in (self.name_field, self.path_field, self.cmd_field, self.title_field):
            w.blockSignals(False)
        self.del_btn.setEnabled(True)
        self.copy_alias_btn.setEnabled(True)
        has_path = bool(a.path)
        self.open_finder_btn.setEnabled(has_path)
        self.open_iterm_btn.setEnabled(has_path)
        self._update_preview()

    def _update_preview(self):
        name  = self.name_field.text().strip()
        path  = self.path_field.text().strip()
        cmd   = self.cmd_field.text().strip()
        title = self.title_field.text().strip()
        if name and (path or cmd):
            line = AliasEntry(name, path, cmd, title).to_zsh_line()
            self.preview.setPlainText(line)
            self.copy_btn.setEnabled(True)
            self.open_finder_btn.setEnabled(bool(path))
            self.open_iterm_btn.setEnabled(bool(path))
        else:
            self.preview.setPlainText("")
            self.copy_btn.setEnabled(False)
            self.open_finder_btn.setEnabled(False)
            self.open_iterm_btn.setEnabled(False)

        # Ausführen nur erlauben wenn Eintrag gespeichert ist UND
        # der Formularinhalt exakt dem gespeicherten Eintrag entspricht
        can_run = False
        if self._editing_index is not None:
            saved = self._aliases[self._editing_index]
            can_run = (
                name  == saved.name    and
                path  == saved.path    and
                cmd   == saved.command and
                title == saved.title
            )
        self.run_btn.setEnabled(can_run)

    def _on_copy_preview(self):
        text = self.preview.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            self.copy_btn.setText("✓ Copied!")
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("⎘ Copy"))

    # ── Slots ─────────────────────────────────────────────────────────────
    def _on_new(self):
        self.list_widget.clearSelection()
        self._clear_form()
        self.name_field.setFocus()

    def _on_select(self, row):
        if 0 <= row < len(getattr(self, "_visible_indices", [])):
            self._populate_form(self._visible_indices[row])

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Project Folder", str(Path.home()),
            QFileDialog.Option.ShowDirsOnly)
        if path:
            home = str(Path.home())
            if path.startswith(home):
                path = "~" + path[len(home):]
            self.path_field.setText(path)

    def _on_cancel(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self._populate_form(row)
        else:
            self._clear_form()

    def _on_save(self):
        name  = self.name_field.text().strip()
        path  = self.path_field.text().strip()
        cmd   = self.cmd_field.text().strip()
        title = self.title_field.text().strip()

        if not name:
            QMessageBox.warning(self, "Missing Name",
                "Please enter an alias name.")
            return
        if not path and not cmd:
            QMessageBox.warning(self, "Missing Content",
                "Enter a folder path, a command, or both.")
            return
        if not name.replace("_","").replace("-","").isalnum():
            QMessageBox.warning(self, "Invalid Name",
                "Alias name may only contain letters, numbers, hyphens and underscores.")
            return
        for i, a in enumerate(self._aliases):
            if a.name == name and i != self._editing_index:
                QMessageBox.warning(self, "Duplicate",
                    f"An alias named '{name}' already exists.")
                return

        entry = AliasEntry(name, path, cmd, title)
        if self._editing_index is not None:
            self._aliases[self._editing_index] = entry
        else:
            self._aliases.append(entry)

        write_aliases(self._aliases)
        self._source_zshrc()
        self._aliases = read_aliases()
        self._visible_indices = []
        self._refresh_list(select_name=name)
        # editing_index auf den neu geladenen Eintrag setzen
        for i, a in enumerate(self._aliases):
            if a.name == name:
                self._editing_index = i
                break
        self._update_preview()
        self.status.showMessage(f"✓  Saved '{name}' and reloaded ~/.zshrc")

    def _on_delete(self):
        idx = self._editing_index
        if idx is None:
            return
        name = self._aliases[idx].name
        if QMessageBox.question(
            self, "Delete", f"Delete alias '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        ) == QMessageBox.StandardButton.Yes:
            self._aliases.pop(idx)
            write_aliases(self._aliases)
            self._source_zshrc()
            self._visible_indices = []
            self._refresh_list()
            self._clear_form()
            self.status.showMessage(f"🗑  Deleted '{name}' and reloaded ~/.zshrc")

    def _on_open_finder(self):
        path = self._resolved_path()
        if path:
            if IS_WIN:
                subprocess.Popen(["explorer", path])
            else:
                subprocess.run(["open", path])

    def _on_open_iterm(self):
        path = self._resolved_path()
        if path:
            if IS_WIN:
                subprocess.Popen(["wt", "-d", path])  # Windows Terminal
            else:
                subprocess.run(["open", "-a", "iTerm", path])

    def _resolved_path(self) -> str:
        raw = self.path_field.text().strip()
        if not raw:
            return ""
        expanded = str(Path(raw).expanduser())
        if not Path(expanded).exists():
            QMessageBox.warning(self, "Path not found",
                f"The folder does not exist:\n{expanded}")
            return ""
        return expanded

    def _on_path_changed(self, text: str):
        has = bool(text.strip())
        self.open_finder_btn.setEnabled(has)
        self.open_iterm_btn.setEnabled(has)

    def _on_run_alias(self):
        idx = self._editing_index
        if idx is None:
            return
        a = self._aliases[idx]
        parts = []
        if a.path:
            parts.append(f"cd {a.path}")
        if a.title:
            parts.append(f"printf '\\033]0;{a.title}\\007'")
        if a.command:
            parts.append(a.command)
        shell_cmd = " && ".join(parts) if parts else ""
        if not shell_cmd:
            return

        if IS_WIN:
            subprocess.Popen(["wt", "new-tab", "--", "cmd", "/k",
                              shell_cmd.replace("&&", "&")])
            self.status.showMessage(f"▶  '{a.name}' launched in Windows Terminal")
        else:
            safe_cmd = shell_cmd.replace("\\", "\\\\").replace('"', '\\"')
            apple = (
                'tell application "iTerm2"\n'
                '    activate\n'
                '    tell current window\n'
                '        create tab with default profile\n'
                '        tell current session of current tab\n'
                f'            write text "{safe_cmd}"\n'
                '        end tell\n'
                '    end tell\n'
                'end tell'
            )
            result = subprocess.run(["osascript", "-e", apple], capture_output=True, text=True)
            if result.returncode == 0:
                self.status.showMessage(f"▶  '{a.name}' launched in new iTerm2 tab")
            else:
                self.status.showMessage(f"⚠  AppleScript error: {result.stderr.strip()[:80]}")

    def _source_zshrc(self):
        if IS_WIN:
            return  # Windows: no source needed, aliases are in .bashrc/.profile
        try:
            r = subprocess.run(["zsh", "-i", "-c", "source ~/.zshrc"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode != 0:
                print(f"[source warning] {r.stderr.strip()}")
        except Exception as e:
            print(f"[source error] {e}")


# ── Entry point ────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TermLink")
    app.setStyle("Fusion")
    icon = _make_app_icon()
    app.setWindowIcon(icon)
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window, QColor("#F2F2F7"))
    pal.setColor(QPalette.ColorRole.Base,   QColor("white"))
    app.setPalette(pal)
    win = TermLinkWindow()
    win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
