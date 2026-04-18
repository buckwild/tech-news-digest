# Tech News Digest

Hourly-updated static dashboard with headlines from CNN, Engadget, and Drudge Report.

## Project structure

- `src/` — Python scripts for fetching feeds and generating HTML/JSON.
- `templates/` — Jinja templates for rendering the dashboard.
- `site/` — Published static output served by GitHub Pages.
- `scripts/` — Helper scripts for automation (publishing, cron).

## Running locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/fetch.py
```

The script writes fresh data into `site/`.

## Deployment

GitHub Pages serves the `site/` folder from the `main` branch via the Pages build settings. A cron job commits and pushes updates every hour.
