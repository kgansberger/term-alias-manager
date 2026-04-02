# TermLink — iTerm2 Alias Manager

**TermLink** ist eine macOS-App zum Verwalten von Shell-Aliases in deiner `~/.zshrc`.  
Mit einem Befehl wechselst du in einen Projektordner — inklusive optionalem iTerm2-Tab-Titel und Startbefehl.

---

## Screenshot

![TermLink Screenshot][image-1]

---

## Installation

### Option A — Als .app (empfohlen)

```bash
# .app in Programme-Ordner kopieren
cp -R dist/TermLink.app /Applications/

# Starten
open /Applications/TermLink.app
```

> **Hinweis:** Beim ersten Start meldet macOS eventuell „Unbekannter Entwickler".  
> Einmalig rechtsklick → „Öffnen" → „Öffnen" bestätigen.

### Option B — Direkt mit Python

```bash
pip3 install PyQt6
python3 main.py
```

### Option C — .app neu bauen

```bash
python3 build_icns.py        # Icon erstellen
python3 setup.py py2app      # App bundlen → dist/TermLink.app
```

---

## Bedienung

| Schritt | Aktion                                                                         |
| ------- | ------------------------------------------------------------------------------ |
| **1**   | App starten                                                                    |
| **2**   | **＋ New** klicken                                                              |
| **3**   | Alias-Name eingeben, z.B. `dev-myapp`                                          |
| **4**   | Projektordner per **Drag & Drop** vom Finder ziehen *oder* **Browse…** klicken |
| **5**   | Optional: Befehl eingeben, z.B. `pnpm run dev`                                 |
| **6**   | Optional: iTerm2-Tab-Titel eingeben, z.B. `MyApp`                              |
| **7**   | Vorschau kontrollieren → **Save & Reload**                                     |

---

## iTerm2-Beispiel mit Tab-Titel

### Was TermLink in die `~/.zshrc` schreibt:

```bash
# BEGIN project-aliases
# [project-alias]
alias dev-myapp='cd ~/Projects/myapp && pnpm run dev && sleep 0.05 && echo -ne "\033]0;MyApp\007"'
# [project-alias]
alias cdproj1='cd ~/Projects/proj1 && sleep 0.05 && echo -ne "\033]0;Proj1\007"'
# [project-alias]
alias k9sprod='k9s --context production'
# END project-aliases
```

### Was in iTerm2 passiert:

```
$ dev-myapp
```

```
➜  myapp git:(main) pnpm run dev
  VITE v5.0.0  ready in 312 ms
  ➜  Local:   http://localhost:5173/
```

Der iTerm2-Tab heisst jetzt **MyApp** — sichtbar oben in der Tab-Leiste.

```
┌─────────────────────────────┐
│  Shell  MyApp  ✕            │  ← Tab-Titel wurde gesetzt
├─────────────────────────────┤
│ ➜  myapp  pnpm run dev      │
│    VITE ready on :5173      │
└─────────────────────────────┘
```

> **Warum `sleep 0.05`?**  
> Der Tab-Titel wird 50 ms nach dem Befehlsstart gesetzt,  
> damit iTerm2 ihn nicht sofort wieder überschreibt.

---

## Wie es funktioniert

- TermLink schreibt **nur** zwischen den Tags `# BEGIN project-aliases` und `# END project-aliases`
- Alles andere in deiner `~/.zshrc` bleibt **unberührt**
- Vor jeder Änderung wird automatisch `~/.zshrc.backup` angelegt
- Nach dem Speichern läuft `source ~/.zshrc` automatisch

---

## Projektstruktur

```
TermLink/
├── main.py              # GUI (PyQt6)
├── src/
│   └── zshrc_parser.py  # zshrc lesen/schreiben
├── tests/
│   └── test_parser.py   # 8 Unit-Tests
├── assets/
│   └── AppIcon.icns     # App-Icon
├── dist/
│   └── TermLink.app     # Fertiges .app Bundle
├── build_icns.py        # Icon-Generator
├── setup.py             # py2app Build-Config
├── screenshot.png       # App-Screenshot
└── icon.md              # Icon-Design-Prompts
```

[image-1]:	screenshot.png