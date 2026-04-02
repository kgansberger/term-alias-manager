"""
zshrc_parser.py — Reads and writes project-aliases between
# BEGIN project-aliases … # END project-aliases tags in ~/.zshrc
Each alias line is preceded by a # [project-alias] marker.
All other lines are left untouched.
"""

import platform
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

_IS_WIN = platform.system() == "Windows"

# Shell config file — .zshrc on macOS, .bashrc for Git Bash/WSL on Windows
if _IS_WIN:
    SHELL_CONFIG = Path.home() / ".bashrc"
else:
    SHELL_CONFIG = Path.home() / ".zshrc"

ZSHRC  = SHELL_CONFIG   # backwards compat alias
BACKUP = Path(str(SHELL_CONFIG) + ".backup")
BEGIN_TAG = "# BEGIN project-aliases"
END_TAG   = "# END project-aliases"
LINE_TAG  = "# [project-alias]"

# Matches both quote styles, optional && echo title at the end
# alias name='cd ~/path && some command && sleep 0.05 && echo -ne "\033]0;Title\007"'
_ALIAS_RE = re.compile(
    r"""^alias\s+([\w\-]+)=['"](.+?)(?:\s*&&\s*sleep\s+[\d.]+)?(?:\s*&&\s*echo\s+-ne\s+["']\\033\]0;(.+?)\\007["'])?['"]$"""
)

# Detect whether the value contains a cd at the start
_CD_RE = re.compile(r"^cd\s+(\S+)\s*(.*)$")


@dataclass
class AliasEntry:
    name:    str
    path:    str   = ""   # folder for cd — may be empty
    command: str   = ""   # extra command after cd (or standalone)
    title:   str   = ""   # optional iTerm2 tab title

    def to_zsh_line(self) -> str:
        parts = []
        if self.path:
            parts.append(f"cd {self.path}")
        if self.title:
            # Titel sofort nach cd setzen — VOR dem Command,
            # damit blockierende Prozesse (claude, gsd, …) den Titel nicht verhindern
            parts.append(f'printf "\\033]0;{self.title}\\007"')
        if self.command:
            parts.append(self.command)

        body = " && ".join(parts) if parts else ""
        if not body:
            return f"alias {self.name}=''"
        return f"alias {self.name}='{body}'"

    @staticmethod
    def from_zsh_line(line: str) -> "AliasEntry | None":
        """Parse any alias line — best effort, graceful fallback."""
        stripped = line.strip()

        # Extract:  alias NAME='VALUE'  or  alias NAME="VALUE"
        m = re.match(r"""^alias\s+([\w\-]+)=['"](.+?)['"]$""", stripped)
        if not m:
            return None
        name  = m.group(1)
        value = m.group(2)

        # Remove tab-title sequence (printf or legacy echo -ne), anywhere in the value
        title = ""
        title_m = re.search(
            r"""\s*&&\s*(?:printf\s+["']\\033\]0;(.+?)\\007["']|(?:sleep\s+[\d.]+\s*&&\s*)?echo\s+-ne\s+["']\\033\]0;(.+?)\\007["'])""",
            value,
        )
        if title_m:
            title = (title_m.group(1) or title_m.group(2) or "").strip()
            value = (value[:title_m.start()] + value[title_m.end():]).strip()
            # aufräumen: doppelte && entfernen
            value = re.sub(r"\s*&&\s*&&\s*", " && ", value).strip(" &&").strip()

        # Detect leading cd
        path = ""
        command = ""
        cd_m = re.match(r"^cd\s+(\S+)\s*(?:&&\s*(.+))?$", value)
        if cd_m:
            path    = cd_m.group(1)
            command = (cd_m.group(2) or "").strip()
        else:
            command = value.strip()

        return AliasEntry(name=name, path=path, command=command, title=title)


# ── I/O ───────────────────────────────────────────────────────────────────────

def _read_zshrc() -> list[str]:
    if not SHELL_CONFIG.exists():
        return []
    return SHELL_CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)


def _backup():
    if SHELL_CONFIG.exists():
        shutil.copy2(SHELL_CONFIG, BACKUP)


def read_aliases() -> list[AliasEntry]:
    lines  = _read_zshrc()
    inside = False
    result = []
    for line in lines:
        s = line.rstrip("\n")
        if s == BEGIN_TAG:
            inside = True;  continue
        if s == END_TAG:
            break
        if inside and s == LINE_TAG:
            continue
        if inside and s.startswith("alias "):
            e = AliasEntry.from_zsh_line(s)
            if e:
                result.append(e)
    return result


def write_aliases(aliases: list[AliasEntry]) -> None:
    _backup()
    lines = _read_zshrc()

    block: list[str] = [BEGIN_TAG + "\n"]
    for a in aliases:
        block.append(LINE_TAG + "\n")
        block.append(a.to_zsh_line() + "\n")
    block.append(END_TAG + "\n")

    begin_idx = end_idx = None
    for i, line in enumerate(lines):
        s = line.rstrip("\n")
        if s == BEGIN_TAG:
            begin_idx = i
        if s == END_TAG:
            end_idx = i
            break

    if begin_idx is not None and end_idx is not None:
        new_lines = lines[:begin_idx] + block + lines[end_idx + 1:]
    else:
        new_lines = lines
        if new_lines and new_lines[-1].strip():
            new_lines.append("\n")
        new_lines.extend(block)

    SHELL_CONFIG.write_text("".join(new_lines), encoding="utf-8")
