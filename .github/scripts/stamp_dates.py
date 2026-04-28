"""Stamp date/lastmod in Hugo front matter for added/modified blog posts.

Reads newline-separated paths from ADDED_FILES and MODIFIED_FILES env vars,
rewrites only the date/lastmod lines in the front matter (preserving the rest
verbatim), and signals whether anything changed via the `changed` output.
"""

import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))
INDEX_NAME = "_index.md"
BLOG_PREFIX = "content/blog/"
DATE_RE = re.compile(r"^date:\s*.*$", re.MULTILINE)
LASTMOD_RE = re.compile(r"^lastmod:\s*.*$", re.MULTILINE)


def kst_now_iso() -> str:
    s = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S%z")
    return s[:-2] + ":" + s[-2:]


def split_front_matter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---"):
        return None
    rest = text[3:]
    if rest.startswith("\n"):
        rest = rest[1:]
    sep = rest.find("\n---")
    if sep == -1:
        return None
    fm = rest[:sep]
    body = rest[sep + 4:]
    return fm, body


def replace_or_insert(fm: str, key_re: re.Pattern, key: str, value: str) -> str:
    line = f"{key}: {value}"
    if key_re.search(fm):
        return key_re.sub(line, fm, count=1)
    if not fm.endswith("\n"):
        fm += "\n"
    return fm + line + "\n"


def stamp(path: Path, set_date: bool, now: str) -> bool:
    original = path.read_text(encoding="utf-8")
    parts = split_front_matter(original)
    if parts is None:
        print(f"  SKIP {path}: no front matter", file=sys.stderr)
        return False
    fm, body = parts

    new_fm = fm
    if set_date:
        new_fm = replace_or_insert(new_fm, DATE_RE, "date", now)
    new_fm = replace_or_insert(new_fm, LASTMOD_RE, "lastmod", now)

    if new_fm == fm:
        return False

    new_text = "---\n" + new_fm
    if not new_text.endswith("\n"):
        new_text += "\n"
    new_text += "---" + body
    path.write_text(new_text, encoding="utf-8")
    return True


def collect(env_name: str) -> list[Path]:
    raw_lines = [
        line.strip()
        for line in os.environ.get(env_name, "").splitlines()
        if line.strip()
    ]
    paths = []
    for raw in raw_lines:
        if not raw.startswith(BLOG_PREFIX):
            continue
        p = Path(raw)
        if p.name == INDEX_NAME or p.suffix != ".md" or not p.exists():
            continue
        paths.append(p)
    return paths


def write_output(name: str, value: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return
    with open(out, "a", encoding="utf-8") as f:
        f.write(f"{name}={value}\n")


def main() -> int:
    now = kst_now_iso()
    print(f"Stamping with {now}")

    added = collect("ADDED_FILES")
    modified = [p for p in collect("MODIFIED_FILES") if p not in added]

    changed = False
    for p in added:
        if stamp(p, set_date=True, now=now):
            print(f"  stamped (new): {p}")
            changed = True
    for p in modified:
        if stamp(p, set_date=False, now=now):
            print(f"  stamped (modified): {p}")
            changed = True

    write_output("changed", "true" if changed else "false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
