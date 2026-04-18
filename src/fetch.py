#!/usr/bin/env python3
"""Fetch RSS feeds and render static dashboard."""

import json
import pathlib
import re
import textwrap
from datetime import datetime, timezone
from html import unescape

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from jinja2 import Environment, FileSystemLoader, select_autoescape
from readability import Document

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "site"
TEMPLATES_DIR = BASE_DIR / "templates"
TOPICS_FILE = BASE_DIR / "src" / "topics.yaml"

FEEDS = {
    "CNN": "http://rss.cnn.com/rss/edition_technology.rss",
    "Engadget": "https://www.engadget.com/rss.xml",
    "Drudge Report": "https://drudgereport.com/rss.xml",
}

MAX_ITEMS_PER_FEED = 20
READABILITY_TIMEOUT = 10
TOPIC_MATCH_FIELDS = ("title", "summary")


def fetch_feed(name: str, url: str):
    parsed = feedparser.parse(url)
    entries = []
    if not parsed.entries and "drudge" in url:
        entries = fetch_drudge_fallback()
        return {"name": name, "url": url, "entries": entries}
    for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
        published = None
        if getattr(entry, "published", None):
            try:
                published = date_parser.parse(entry.published)
            except Exception:
                published = None
        summary_raw = entry.get("summary", "")
        summary_clean = clean_summary(summary_raw)
        link = entry.get("link", "")
        excerpt = extract_excerpt(link)
        entries.append(
            {
                "title": entry.get("title", "Untitled"),
                "link": link,
                "summary": textwrap.shorten(
                    summary_clean,
                    width=240,
                    placeholder="…",
                )
                if summary_clean
                else None,
                "published": published.isoformat() if published else None,
                "excerpt": excerpt,
            }
        )
    return {"name": name, "url": url, "entries": entries}


def clean_summary(text: str) -> str:
    if not text:
        return ""
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_excerpt(url: str) -> str | None:
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=READABILITY_TIMEOUT, headers={"User-Agent": "tech-news-digest/1.0"})
        resp.raise_for_status()
        doc = Document(resp.text)
        summary_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(summary_html, "html.parser")
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]
        if paragraphs:
            return paragraphs[0]
    except Exception:
        return None
    return None


def fetch_drudge_fallback():
    try:
        resp = requests.get("https://drudgereport.com", timeout=READABILITY_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for a in soup.select("a"):
            title = a.get_text(strip=True)
            href = a.get("href")
            if not title or not href:
                continue
            if not href.startswith("http"):
                continue
            items.append({
                "title": title,
                "link": href,
                "summary": None,
                "published": None,
                "excerpt": None,
            })
            if len(items) >= MAX_ITEMS_PER_FEED:
                break
        return items
    except Exception as exc:
        return [{"title": "Unable to fetch Drudge Report", "link": "", "summary": str(exc), "published": None, "excerpt": None}]


def load_topics():
    if not TOPICS_FILE.exists():
        return []
    data = yaml.safe_load(TOPICS_FILE.read_text())
    topics = data.get("topics", []) if isinstance(data, dict) else data
    normalized = []
    for topic in topics:
        keywords = topic.get("keywords", [])
        normalized.append({"name": topic.get("name", ""), "keywords": [k.lower() for k in keywords]})
    return normalized


def matches_topics(entry, topics):
    if not topics:
        return True
    text = " ".join(filter(None, [entry.get(field, "") for field in TOPIC_MATCH_FIELDS])).lower()
    for topic in topics:
        if any(keyword in text for keyword in topic["keywords"]):
            return True
    return False


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
    topics = load_topics()
    feeds = []
    for name, url in FEEDS.items():
        try:
            feed_data = fetch_feed(name, url)
            filtered_entries = [entry for entry in feed_data["entries"] if matches_topics(entry, topics)]
            feed_data["entries"] = filtered_entries
            feeds.append(feed_data)
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
