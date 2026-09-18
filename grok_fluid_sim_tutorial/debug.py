#!/usr/bin/env python3
"""Launch a debugger on source lines that end with a dbg token.

tmux prefix-e runs ~/.scripts/debugger.sh, which types ./debug.py once
in a project pane. This file scans for marks, then start_debugger()
runs the debuggee. This file is the launcher, not the program under test.

Edit:
  TOKENS / SOURCE_SUFFIXES / SKIP_DIRS
  start_debugger(hits)  — swap pdb for gdb/lldb/node/etc.
"""

import importlib
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Project settings
# ---------------------------------------------------------------------------

# Trailing word nvim's ;b writes. Prefix is the language's line comment:
#   python/ruby/sh  #dbg
#   c/java/go/rust  //dbg
#   lua             --dbg
TOKENS = ("#dbg", "//dbg", "--dbg")

SOURCE_SUFFIXES = {".py"}

SKIP_DIRS = {".venv", "__pycache__", ".git", "node_modules", "target", "build"}

HERE = Path(__file__).resolve()
ROOT = HERE.parent


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def is_mark(line):
    stripped = line.rstrip()
    return any(stripped.endswith(token) for token in TOKENS)


def collect(root):
    """Absolute (path, lineno) for source lines that end with a dbg token.

    Skips this file: it is the launcher, and its comments name the token.
    """
    hits = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SOURCE_SUFFIXES:
            continue
        if path.resolve() == HERE:
            continue
        if SKIP_DIRS & set(path.parts):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if is_mark(line):
                hits.append((str(path.resolve()), lineno))
    return hits


# ---------------------------------------------------------------------------
# Debugger recipe — replace start_debugger() for other languages
# ---------------------------------------------------------------------------
# The default recipe needs the project venv (numpy, the package). gdb/lldb
# on a binary do not: omit ensure_uv_python() from your replacement.
#
# execvp replaces this process with `uv run python debug.py` and restarts
# the file from the top (collect is silent; that second pass is cheap).
# Anything you print before ensure_uv_python() therefore appears twice.

def in_project_venv():
    project_venv = (ROOT / ".venv").resolve()
    env_venv = os.environ.get("VIRTUAL_ENV")
    if env_venv and Path(env_venv).resolve() == project_venv:
        return True
    return Path(sys.prefix).resolve() == project_venv


def ensure_uv_python():
    if in_project_venv():
        return
    os.execvp("uv", ["uv", "run", "--", "python", str(HERE), *sys.argv[1:]])


def load_entry_point():
    """Callable named by [project.scripts] in pyproject.toml."""
    try:
        import tomllib
    except ImportError:
        raise SystemExit("debug.py: python 3.11+ required to read pyproject.toml")

    pyproject = ROOT / "pyproject.toml"
    if not pyproject.is_file():
        raise SystemExit("debug.py: no pyproject.toml — edit load_entry_point()")

    data = tomllib.loads(pyproject.read_text())
    scripts = data.get("project", {}).get("scripts") or {}
    if not scripts:
        raise SystemExit("debug.py: no [project.scripts] — edit load_entry_point()")

    # Prefer a script whose name matches the project; otherwise first entry.
    project_name = data.get("project", {}).get("name", "")
    spec = scripts.get(project_name) or next(iter(scripts.values()))
    module_name, func_name = spec.split(":", 1)
    func_name = func_name.split()[0]
    return getattr(importlib.import_module(module_name), func_name)


def start_debugger(hits):
    """Default: pdb in this process, runcall the project entry point.

    `hits` is [(absolute_path, lineno), ...] from collect().

    gdb example (no venv; do not call ensure_uv_python):

        cmd = ["gdb"]
        for path, lineno in hits:
            cmd += ["-ex", f"break {path}:{lineno}"]
        cmd += ["-ex", "run", "--args", str(ROOT / "a.out")]
        os.execvp(cmd[0], cmd)
    """
    import pdb

    ensure_uv_python()

    for path, lineno in hits:
        print(f"break {path}:{lineno}")

    func = load_entry_point()
    dbg = pdb.Pdb()
    for path, lineno in hits:
        err = dbg.set_break(path, lineno)
        if err:
            print(err)
    # pdb stops on the first line of runcall's target; continue to the marks.
    dbg.rcLines.append("continue")
    dbg.runcall(func)


if __name__ == "__main__":
    os.chdir(ROOT)
    start_debugger(collect(ROOT))
