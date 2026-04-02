"""
tests/test_parser.py — unit tests for zshrc_parser (no real ~/.zshrc touched)
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import zshrc_parser as zp


def _setup_fake_zshrc(tmp: Path, content: str):
    import textwrap
    f = tmp / ".zshrc"
    f.write_text(textwrap.dedent(content))
    zp.ZSHRC  = f
    zp.BACKUP = tmp / ".zshrc.backup"
    return f


def test_read_aliases_basic():
    with tempfile.TemporaryDirectory() as d:
        _setup_fake_zshrc(Path(d), """
            export PATH="$HOME/bin:$PATH"

            # BEGIN project-aliases
            # [project-alias]
            alias cdproj1='cd ~/Folder/proj1 && echo -ne "\\033]0;Proj1\\007"'
            # [project-alias]
            alias cdwork='cd ~/Work'
            # END project-aliases

            alias ll='ls -la'
        """)
        aliases = zp.read_aliases()
        assert len(aliases) == 2
        assert aliases[0].name == "cdproj1"
        assert aliases[0].path == "~/Folder/proj1"
        assert aliases[0].title == "Proj1"
        assert aliases[1].name == "cdwork"
        assert aliases[1].title == ""
        print("✅ test_read_aliases_basic passed")


def test_write_preserves_outside_lines():
    with tempfile.TemporaryDirectory() as d:
        f = _setup_fake_zshrc(Path(d), """
            export PATH="$HOME/bin:$PATH"

            # BEGIN project-aliases
            # [project-alias]
            alias cdold='cd ~/old'
            # END project-aliases

            alias ll='ls -la'
        """)
        zp.write_aliases([zp.AliasEntry("cdnew", "~/new", "", "NewTab")])
        result = f.read_text()
        assert "export PATH" in result
        assert "alias ll=" in result
        assert "cdold" not in result
        assert "cdnew" in result
        assert "NewTab" in result
        print("✅ test_write_preserves_outside_lines passed")


def test_backup_created():
    with tempfile.TemporaryDirectory() as d:
        _setup_fake_zshrc(Path(d), """
            # BEGIN project-aliases
            # END project-aliases
        """)
        backup = Path(d) / ".zshrc.backup"
        assert not backup.exists()
        zp.write_aliases([zp.AliasEntry("cdfoo", "~/foo")])
        assert backup.exists()
        print("✅ test_backup_created passed")


def test_append_block_when_missing():
    with tempfile.TemporaryDirectory() as d:
        f = _setup_fake_zshrc(Path(d), "export FOO=bar\n")
        zp.write_aliases([zp.AliasEntry("cdtest", "~/test", "", "Test")])
        result = f.read_text()
        assert "# BEGIN project-aliases" in result
        assert "# END project-aliases" in result
        assert "cdtest" in result
        assert "export FOO=bar" in result
        print("✅ test_append_block_when_missing passed")


def test_to_zsh_line_with_title():
    a = zp.AliasEntry("cdproj", "~/proj", "", "MyProj")
    line = a.to_zsh_line()
    assert "sleep 0.05" in line
    assert "MyProj" in line
    assert "cd ~/proj" in line
    print("✅ test_to_zsh_line_with_title passed")


def test_to_zsh_line_without_title():
    a = zp.AliasEntry("cdproj", "~/proj")
    assert a.to_zsh_line() == "alias cdproj='cd ~/proj'"
    print("✅ test_to_zsh_line_without_title passed")


def test_to_zsh_line_with_command():
    a = zp.AliasEntry("dev", "~/proj", "pnpm run dev", "Dev")
    line = a.to_zsh_line()
    assert "pnpm run dev" in line
    assert "sleep 0.05" in line
    assert "Dev" in line
    print("✅ test_to_zsh_line_with_command passed")


def test_to_zsh_line_command_only():
    a = zp.AliasEntry("k9s", "", "k9s --context prod")
    assert a.to_zsh_line() == "alias k9s='k9s --context prod'"
    print("✅ test_to_zsh_line_command_only passed")


if __name__ == "__main__":
    test_read_aliases_basic()
    test_write_preserves_outside_lines()
    test_backup_created()
    test_append_block_when_missing()
    test_to_zsh_line_with_title()
    test_to_zsh_line_without_title()
    test_to_zsh_line_with_command()
    test_to_zsh_line_command_only()
    print("\n🎉 All tests passed.")
