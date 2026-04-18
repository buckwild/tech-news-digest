#!/usr/bin/env python3
"""Fetch RSS feeds and render static dashboard."""

import json
import pathlib
import textwrap
from datetime import datetime, timezone

import feedparser
from dateutil import parser as date_parser
from jinja2 import Environment, FileSystemLoader, select_autoescape
import requests

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "site"
TEMPLATES_DIR = BASE_DIR / "templates"

FEEDS = {
    "CNN": "http://rss.cnn.com/rss/edition_technology.rss",
    "Engadget": "https://www.engadget.com/rss.xml",
    "Drudge Report": "https://drudgereport.com/rss.xml",
}

MAX_ITEMS_PER_FEED = 20


def fetch_feed(name: str, url: str):
    parsed = feedparser.parse(url)
    entries = []
    for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
        published = None
        if getattr(entry, "published", None):
            try:
                published = date_parser.parse(entry.published)
            except Exception:
                published = None
        entries.append(
            {
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", ""),
                "summary": textwrap.shorten(
                    feedparser._sanitizeHTML(entry.get("summary", "")),
                    width=240,
                    placeholder="…",
                ),
                "published": published.isoformat() if published else None,
            }
        )
    return {"name": name, "url": url, "entries": entries}


def render(feeds, generated_at):
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("index.html.j2")
    html = template.render(feeds=feeds, generated_at=generated_at)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "index.html").write_text(html, encoding="utf-8")
    (DATA_DIR / "feeds.json").write_text(
        json.dumps({"generated_at": generated_at, "feeds": feeds}, indent=2),
        encoding="utf-8",
    )


def main():
    feeds = []
    for name, url in FEEDS.items():
        try:
            feeds.append(fetch_feed(name, url))
        except Exception as exc:
            feeds.append(
                {
                    "name": name,
                    "url": url,
                    "entries": [],
                    "error": str(exc),
                }
            )
    generated_at = datetime.now(timezone.utc).isoformat()
    render(feeds, generated_at)
    print(f"Rendered {len(feeds)} feeds at {generated_at}")


if __name__ == "__main__":
    main()
