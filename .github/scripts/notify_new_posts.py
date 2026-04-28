"""Notify upload-post.com about newly added blog posts.

Reads a newline-separated list of added markdown paths from the env var
ADDED_FILES, parses Hugo front matter, and POSTs a formatted message per file
to the upload-post.com text endpoint.
"""

import os
import sys
from pathlib import Path

import requests
import yaml

API_URL = "https://api.upload-post.com/api/upload_text"
SITE_BASE = "https://2rebcat.github.io"
BLOG_ROOT = Path("content/blog")
INDEX_NAME = "_index.md"


def parse_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing front matter")
    _, fm, _ = text.split("---", 2)
    return yaml.safe_load(fm) or {}


def build_message(title: str, summary: str, url: str) -> str:
    return (
        "새로운 게시글이 추가되었어요!\n\n"
        f"{title}\n\n"
        f"{summary}\n\n"
        "더 자세한 내용은 Blog에서 확인하세요!\n"
        f"URL: {url}"
    )


def post_url_for(path: Path) -> str:
    rel = path.relative_to(BLOG_ROOT)
    topic = rel.parts[0]
    slug = rel.stem
    return f"{SITE_BASE}/blog/{topic}/{slug}/"


def upload(message: str, api_key: str, user: str, platforms: list[str]) -> None:
    headers = {"Authorization": f"Apikey {api_key}"}
    fields = [("user", user), ("title", message)]
    fields.extend(("platform[]", p) for p in platforms)
    resp = requests.post(API_URL, headers=headers, files=fields, timeout=30)
    print(f"  status={resp.status_code} body={resp.text[:500]}")
    resp.raise_for_status()


def main() -> int:
    api_key = os.environ["UPLOAD_POST_API_KEY"].strip()
    user = os.environ["UPLOAD_POST_USER"].strip()
    if not api_key:
        print("UPLOAD_POST_API_KEY is empty.", file=sys.stderr)
        return 1
    if not user:
        print("UPLOAD_POST_USER is empty.", file=sys.stderr)
        return 1
    print(f"Using upload-post user='{user}' (length={len(user)})")
    platforms = [
        p.strip()
        for p in os.environ.get("UPLOAD_POST_PLATFORMS", "x").split(",")
        if p.strip()
    ]
    added = [
        line.strip()
        for line in os.environ.get("ADDED_FILES", "").splitlines()
        if line.strip()
    ]

    targets = []
    for raw in added:
        path = Path(raw)
        if not raw.startswith("content/blog/"):
            continue
        if path.name == INDEX_NAME:
            continue
        if path.suffix != ".md":
            continue
        if not path.exists():
            continue
        targets.append(path)

    if not targets:
        print("No new blog posts to announce.")
        return 0

    print(f"Found {len(targets)} new post(s): {[str(p) for p in targets]}")
    failures = 0
    for path in targets:
        try:
            fm = parse_front_matter(path)
            title = (fm.get("title") or "").strip()
            summary = (fm.get("summary") or "").strip()
            if not title or not summary:
                print(f"  SKIP {path}: missing title/summary in front matter")
                continue
            url = post_url_for(path)
            message = build_message(title, summary, url)
            print(f"Posting for {path}:")
            upload(message, api_key, user, platforms)
        except Exception as e:
            failures += 1
            print(f"  ERROR for {path}: {e}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
