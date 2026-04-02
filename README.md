# TermLink — Terminal Project Alias Manager

> **Stop typing the same commands every day.**

You open a new terminal. You type `cd ~/Projects/my-app`. Then `claude`. Or `gsd`. Or `pnpm run dev`. Every. Single. Time.

**TermLink fixes that.**

One alias. One word. You're in your project, your tool is running, your tab has the right name — in under a second. No terminal switching, no path memorizing, no repeated typing. Just get to work.

Built for developers who live in the terminal and hate friction.

---

## ⚡ The fast lane — claude, gsd, and beyond

This is where TermLink really shines. Instead of navigating to a project and launching your AI or planning tool manually, you define it once:

```bash
# Start Claude Code in your project:
alias aichat='cd ~/Projects/ai-chat && printf "\033]0;AI Chat\007" && claude'

# Open a GSD planning session:
alias plan='cd ~/Projects/myapp && printf "\033]0;Planning\007" && gsd'

# Full dev stack:
alias dev='cd ~/Projects/myapp && printf "\033]0;Dev\007" && pnpm run dev'
```

Type `aichat` → new tab, right folder, Claude running, tab named. Done.
Type `plan` → right folder, GSD open, zero friction.

> **▶ Run button:** TermLink can open a new iTerm2 tab and execute any alias directly from the app — no terminal needed at all.

---

## Installation

### Option A — .app (recommended)

Download the latest release and copy to Applications:

```bash
cp -R TermLink.app /Applications/
open /Applications/TermLink.app
```

> **First launch:** macOS may show "Unknown Developer". Right-click → Open → Confirm.

### Option B — Run with Python

```bash
pip3 install PyQt6
python3 main.py
```

### Option C — Build from source

```bash
python3 build_icns.py      # generate icon
python3 setup.py py2app    # bundle → dist/TermLink.app
```

---

## Usage

| Step | Action |
|------|--------|
| **1** | Click **＋ New** |
| **2** | Enter an alias name, e.g. `dev-myapp` |
| **3** | Drag a folder from Finder **or** click **Browse…** |
| **4** | Optional: add a command, e.g. `claude`, `gsd`, `pnpm run dev` |
| **5** | Optional: set an iTerm2 tab title, e.g. `MyApp` |
| **6** | Review the preview → **Save & Reload** |

---

## What gets written to `~/.zshrc`

TermLink only touches the marked block — everything else in your shell config is untouched:

```bash
# BEGIN project-aliases
# [project-alias]
alias aichat='cd ~/Projects/ai-chat && printf "\033]0;AI Chat\007" && claude'
# [project-alias]
alias plan='cd ~/Projects/myapp && printf "\033]0;Planning\007" && gsd'
# [project-alias]
alias dev='cd ~/Projects/myapp && printf "\033]0;Dev\007" && pnpm run dev'
# [project-alias]
alias k9sprod='k9s --context production'
# END project-aliases
```

> **Tab title is set before the command** — so blocking processes like `claude` or `gsd` don't prevent the title from appearing.

---

## How it works

- Writes **only** between `# BEGIN project-aliases` and `# END project-aliases`
- All other `~/.zshrc` content is **never touched**
- Automatic backup to `~/.zshrc.backup` before every change
- `source ~/.zshrc` runs automatically after saving

---

## Project structure

```
TermLink/
├── main.py              # GUI (PyQt6)
├── src/
│   ├── zshrc_parser.py  # read/write ~/.zshrc
│   └── version.py       # auto-generated from git tag at build time
├── tests/
│   └── test_parser.py   # unit tests
├── assets/
│   └── AppIcon.icns     # app icon
├── setup.py             # py2app build config
└── build_icns.py        # icon generator
```

---

## Requirements

- macOS 12+ (for `.app` build)
- Python 3.11+
- PyQt6
- iTerm2 (for tab title and ▶ Run button)

---

## License

MIT — made by klausinger
