#!/usr/bin/env python3
"""Guard against writing a stale Overleaf Dropbox mirror.

Overleaf pushes web edits to Dropbox only every 10-20 minutes. Writing to a
local mirror file that has not been refreshed since then silently overwrites
whatever was typed on overleaf.com in the meantime.

This script has two jobs:

  1. As a Claude Code PreToolUse hook (no arguments, JSON on stdin), it denies
     writes to any file under a configured Overleaf mirror root unless that
     project was stamped fresh within the TTL.

  2. As a CLI, `--stamp PATH` records that a project was just synced. The skill
     calls it after forcing "Sync this project now" in the Overleaf UI.

Fails open: any internal error allows the tool call rather than blocking work.

Configuration, highest precedence first:

  OVERLEAF_MIRROR_ROOTS       colon-separated roots
  ~/.config/overleaf-skill/roots   one root per line
  ~/.config/overleaf-skill/projects.yaml   defaults.mirror_roots
  ../projects.yaml            same key, shipped template
  ~/Dropbox/Apps/Overleaf     fallback

  OVERLEAF_FRESHNESS_TTL_MINUTES   minutes a stamp is trusted (default 15)
  OVERLEAF_GUARD_READS=1           also prompt on stale reads (default off)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

DEFAULT_TTL_MINUTES = 15
DEFAULT_ROOT = "~/Dropbox/Apps/Overleaf"

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_TOOLS = {"Read", "Grep", "Glob"}

# Shell fragments that indicate a Bash command mutates a file.
WRITE_VERBS = (
    ">", "tee", "sed -i", "perl -i", "cp ", "mv ", "rm ", "install ",
    "truncate", "dd ", "chmod", "touch ", "patch ", "git checkout",
)

# Redirections that contain ">" but do not write to the mirror.
BENIGN_REDIRECTS = ("2>&1", "2>/dev/null", ">/dev/null", "2> /dev/null", "> /dev/null")


# --------------------------------------------------------------------------- #
# configuration
# --------------------------------------------------------------------------- #

def skill_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def registry() -> Path:
    """The live registry: user config if present, else the shipped template."""
    user = Path(os.path.expanduser("~/.config/overleaf-skill/projects.yaml"))
    return user if user.is_file() else skill_dir() / "projects.yaml"


def expand(p: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(p.strip()))).resolve()


def _roots_from_yaml(path: Path) -> list[str]:
    """Read defaults.mirror_roots without requiring PyYAML."""
    if not path.is_file():
        return []
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text()) or {}
        roots = (data.get("defaults") or {}).get("mirror_roots") or []
        return [str(r) for r in roots if r]
    except Exception:
        pass

    roots: list[str] = []
    in_block = False
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if re.match(r"^mirror_roots\s*:", stripped):
            in_block = True
            continue
        if in_block:
            m = re.match(r"^-\s+(.+?)\s*$", stripped)
            if m:
                roots.append(m.group(1).strip("'\""))
                continue
            if stripped:
                in_block = False
    return roots


def mirror_roots_raw() -> list[str]:
    """Root paths exactly as configured, before expansion."""
    env = os.environ.get("OVERLEAF_MIRROR_ROOTS")
    if env:
        raw = [r for r in env.split(":") if r.strip()]
    else:
        cfg = Path(os.path.expanduser("~/.config/overleaf-skill/roots"))
        raw = []
        if cfg.is_file():
            raw = [ln for ln in cfg.read_text().splitlines()
                   if ln.strip() and not ln.strip().startswith("#")]
        if not raw:
            raw = _roots_from_yaml(registry())
        if not raw:
            raw = [DEFAULT_ROOT]
    return [r.strip() for r in raw if r.strip()]


def mirror_roots() -> list[Path]:
    """Configured roots, fully resolved. Used for path containment."""
    roots: list[Path] = []
    for r in mirror_roots_raw():
        try:
            roots.append(expand(r))
        except Exception:
            continue
    return roots


def root_forms() -> list[tuple[Path, set[str]]]:
    """Each resolved root paired with every string form it may appear as in a
    shell command: as configured, tilde-expanded, fully resolved, and the
    resolved form re-abbreviated to `~`. A Dropbox root is often reached
    through a symlink, so these differ."""
    home = os.path.expanduser("~")
    pairs = []
    for raw in mirror_roots_raw():
        try:
            resolved = expand(raw)
        except Exception:
            continue
        forms = {raw.rstrip("/"), os.path.expanduser(raw).rstrip("/"), str(resolved)}
        if str(resolved).startswith(home):
            forms.add(str(resolved).replace(home, "~", 1))
        pairs.append((resolved, {f for f in forms if f}))
    return pairs


def ttl_seconds() -> int:
    env = os.environ.get("OVERLEAF_FRESHNESS_TTL_MINUTES")
    if env:
        try:
            return max(60, int(float(env) * 60))
        except ValueError:
            pass
    yml = registry()
    if yml.is_file():
        m = re.search(r"^\s*freshness_ttl_minutes\s*:\s*(\d+)", yml.read_text(), re.M)
        if m:
            return max(60, int(m.group(1)) * 60)
    return DEFAULT_TTL_MINUTES * 60


def stamp_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    d = Path(base) / "overleaf-skill" / "freshness"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------- #
# project resolution and stamping
# --------------------------------------------------------------------------- #

def project_dir_for(path: Path) -> Path | None:
    """Return the per-project mirror folder containing `path`, if any."""
    try:
        candidate = Path(os.path.expanduser(str(path)))
        candidate = candidate if candidate.is_absolute() else candidate.resolve()
    except Exception:
        return None

    for root in mirror_roots():
        try:
            rel = candidate.resolve(strict=False).relative_to(root)
        except Exception:
            continue
        parts = rel.parts
        if not parts:
            return None          # the root itself, not a project
        return root / parts[0]
    return None


def stamp_file(project: Path) -> Path:
    key = hashlib.sha1(str(project).encode("utf-8")).hexdigest()[:16]
    return stamp_dir() / f"{key}.stamp"


def write_stamp(project: Path) -> None:
    stamp_file(project).write_text(f"{int(time.time())}\n{project}\n")


def stamp_age(project: Path) -> float | None:
    f = stamp_file(project)
    if not f.is_file():
        return None
    try:
        return time.time() - int(f.read_text().splitlines()[0])
    except Exception:
        return None


def is_fresh(project: Path) -> bool:
    age = stamp_age(project)
    return age is not None and age <= ttl_seconds()


# --------------------------------------------------------------------------- #
# hook mode
# --------------------------------------------------------------------------- #

def bash_targets(command: str) -> list[Path]:
    """Project folders a Bash command appears to touch under a mirror root."""
    cleaned = command
    for r in BENIGN_REDIRECTS:
        cleaned = cleaned.replace(r, " ")
    if not any(v in cleaned for v in WRITE_VERBS):
        return []

    found: list[Path] = []
    for root, forms in root_forms():
        for form in forms:
            start = 0
            while True:
                i = cleaned.find(form, start)
                if i < 0:
                    break
                start = i + len(form)
                rest = cleaned[start:].lstrip("/")
                seg = rest.split("/", 1)[0]
                seg = seg.strip().strip("'\"").rstrip("'\";")
                seg = seg.replace("\\ ", " ").rstrip("\\")
                if seg:
                    p = root / seg
                    if p not in found:
                        found.append(p)
    return found


def decision(kind: str, reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def stale_reason(project: Path, action: str) -> str:
    age = stamp_age(project)
    when = "never verified this session" if age is None else f"last verified {int(age // 60)} min ago"
    return (
        f"Overleaf mirror guard: {action} '{project.name}' blocked — {when}, "
        f"TTL is {ttl_seconds() // 60} min.\n"
        f"Overleaf pushes web edits to Dropbox only every 10-20 minutes, so this "
        f"local copy may be behind overleaf.com and writing it would overwrite "
        f"newer web edits.\n"
        f"Run the freshness protocol first: open the project in Chrome, "
        f"Integrations -> Dropbox -> 'Sync this project now', wait for the local "
        f"folder to settle, then:\n"
        f"  python3 {Path(__file__).resolve()} --stamp '{project}'\n"
        f"In `suggest` mode, do not write here at all — make the edit in the "
        f"Overleaf editor in Reviewing mode."
    )


def hook_mode() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)                      # unparseable input: never block

    tool = payload.get("tool_name") or ""
    ti = payload.get("tool_input") or {}

    if tool in WRITE_TOOLS:
        raw = ti.get("file_path") or ti.get("notebook_path") or ""
        if raw:
            project = project_dir_for(Path(raw))
            if project and not is_fresh(project):
                decision("deny", stale_reason(project, "write to"))

    elif tool == "Bash":
        for project in bash_targets(ti.get("command") or ""):
            if not is_fresh(project):
                decision("deny", stale_reason(project, "shell write to"))

    elif tool in READ_TOOLS and os.environ.get("OVERLEAF_GUARD_READS"):
        raw = ti.get("file_path") or ti.get("path") or ti.get("pattern") or ""
        if raw:
            project = project_dir_for(Path(str(raw)))
            if project and not is_fresh(project):
                decision("ask", stale_reason(project, "read from"))

    sys.exit(0)


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #

def main() -> None:
    args = sys.argv[1:]
    if not args:
        hook_mode()
        return

    cmd = args[0]

    if cmd in ("-h", "--help"):
        print(__doc__)
        return

    if cmd == "--roots":
        for r in mirror_roots():
            print(f"{r}  {'(exists)' if r.is_dir() else '(missing)'}")
        print(f"ttl: {ttl_seconds() // 60} min")
        return

    if cmd == "--list":
        now = time.time()
        any_found = False
        for f in sorted(stamp_dir().glob("*.stamp")):
            try:
                ts, proj = f.read_text().splitlines()[:2]
                age = int((now - int(ts)) // 60)
                state = "fresh" if now - int(ts) <= ttl_seconds() else "STALE"
                print(f"{state:6}  {age:4d} min  {proj}")
                any_found = True
            except Exception:
                continue
        if not any_found:
            print("no stamps recorded")
        return

    if cmd in ("--stamp", "--check"):
        if len(args) < 2:
            print(f"usage: {Path(__file__).name} {cmd} PATH", file=sys.stderr)
            sys.exit(2)
        target = Path(os.path.expanduser(args[1]))
        project = project_dir_for(target)
        if project is None:
            print(f"not under a configured Overleaf mirror root: {target}\n"
                  f"roots: {', '.join(str(r) for r in mirror_roots())}",
                  file=sys.stderr)
            sys.exit(1)
        if cmd == "--stamp":
            write_stamp(project)
            print(f"stamped fresh: {project}  (valid {ttl_seconds() // 60} min)")
            return
        if is_fresh(project):
            age = stamp_age(project) or 0
            print(f"fresh: {project} ({int(age // 60)} min old)")
            sys.exit(0)
        print(f"stale: {project}", file=sys.stderr)
        sys.exit(1)

    print(f"unknown argument: {cmd}\n{__doc__}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:                       # fail open, always
        print(f"overleaf-freshness: {exc}", file=sys.stderr)
        sys.exit(0)
