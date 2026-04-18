# Tech News Digest — Context & Operating Notes

_Last updated: Apr 18, 2026_

## Purpose
Static dashboard that aggregates tech headlines for Sur (interest: CNN, Engadget, Drudge Report). Output is generated locally and published through GitHub Pages (`docs/` folder symlinked as `site/`).

## Data Sources
- **CNN Technology** — `http://rss.cnn.com/rss/cnn_tech.rss`
  - This is the newer, regularly updated feed. The previous `edition_technology` feed was frozen at 2016.
  - Many CNN items are video posts without RFC-822 timestamps; retain link + summaries even if the date is missing.
- **Engadget** — `https://www.engadget.com/rss.xml`
- **Drudge Report** — `https://drudgereport.com/rss.xml`
  - Falls back to HTML scraping if RSS delivers no items.

`MAX_ITEMS_PER_FEED = 20`. Topic filtering is driven by `src/topics.yaml` (keywords lowered and applied to title+summary).

## Timezone & Formatting
- All timestamps are converted to **Pacific Time (America/Los_Angeles)** before rendering.
- JSON feed (`docs/feeds.json`)
  - `generated_at`: ISO8601 Pacific timestamp.
  - `generated_at_display`: Friendly PT string (e.g., `Apr 18, 2026 11:07 AM PT`).
  - Each entry exposes `published` (ISO PT) and `published_display` (friendly PT) when source timestamps exist.
- HTML template (`templates/index.html.j2`) reads the friendly `generated_at` string and shows friendly timestamps per item.

## Local Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/fetch.py
```
- Script writes fresh HTML + JSON into `docs/` (public) and keeps `site/` symlinked there.
- Render log prints `Rendered <n> feeds at <timestamp PT>`.

## Deployment / Publishing
- Repo: `github-buckwild:buckwild/tech-news-digest.git`, branch `main`.
- GitHub Pages configured to serve `docs/`.
- Update flow:
  1. Run fetch script (in venv) to regenerate artifacts.
  2. `git status` should show changes in `docs/` + `src/`/`templates` as needed.
  3. Commit message sample: `Switch CNN RSS + PT timestamps`.
  4. `git pull --rebase` (remote cron hourly updates the branch; pulls are required before pushing).
  5. `git push`.

## Notable Customizations (Apr 2026)
- CNN feed updated to `cnn_tech.rss` (previous feed out of date since 2016).
- Added Pacific Time conversion pipeline (`ZoneInfo` + helper functions) and template display logic.
- `feeds.json` now includes both ISO and display timestamps for reload clients.

Keep this file updated when feed sources, formatting rules, or deployment practices change.
