#!/usr/bin/env python3
"""Rewrite GoReleaser's legacy `postflight do` quarantine hook as `postflight_steps`.

Homebrew deprecated `postflight` blocks in third-party taps. GoReleaser (as of
2.18.x) still generates them from `homebrew_casks.hooks.post.install`, so each
release reintroduces the warning. This converts the one snippet our configs
produce and fails loudly on any other `postflight do` block.

Usage: fix_postflight.py [cask_dir ...]   (default: Casks)
"""
import re
import sys
from pathlib import Path

LEGACY = re.compile(
    r"^  postflight do\n"
    r'[ ]*if system_command\("/usr/bin/xattr", args: \["-h"\]\)\.exit_status == 0\n'
    r"(?:[ ]*#[^\n]*\n)*"
    r'[ ]*system_command "/usr/bin/xattr", args: \["-dr", "com\.apple\.quarantine", '
    r'"#\{(?P<base>staged_path|appdir)\}/(?P<target>[^"]+)"\]\n'
    r"[ ]*end\n"
    r"^  end\n",
    re.M,
)

REPLACEMENT = '''  postflight_steps do
    on_macos do
      run "/usr/bin/xattr",
          args:         ["-dr", "com.apple.quarantine", "{{{{{base}}}}}/{target}"],
          must_succeed: false
    end
  end
'''


def main(dirs: list[str]) -> int:
    status = 0
    for d in dirs:
        for path in sorted(Path(d).glob("*.rb")):
            text = path.read_text()
            new, n = LEGACY.subn(
                lambda m: REPLACEMENT.format(base=m["base"], target=m["target"]), text
            )
            if re.search(r"^\s*postflight do\b", new, re.M):
                print(f"::error file={path}::unrecognised legacy postflight block; fix by hand")
                status = 1
            if n:
                path.write_text(new)
                print(f"converted {path}")
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["Casks"]))
