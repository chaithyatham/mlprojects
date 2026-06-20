# Senior Product Job-Search Agent

Configuration-driven CLI agent for finding and scoring senior product roles focused on AI, data platforms, ML infrastructure, and data products.

## Setup

```bash
cd job_search
cp config.example.yaml config.yaml
cp resume.example.md resume.md
python3 -m pip install -r ../requirements.txt
python3 -m playwright install chromium
```

Set `ANTHROPIC_API_KEY` before a normal run. The live run uses Anthropic to generate the fit score, rationale, concerns, and outreach angle.

## Run

```bash
python3 -m agent --resume resume.md --config config.yaml
```

Use the deterministic local scorer while developing or testing:

```bash
python3 -m agent --resume resume.md --config config.yaml --offline
```

Optional targeted companies can supplement VC portfolio discovery:

```bash
python3 -m agent \
  --resume resume.md \
  --config config.yaml \
  --target-companies target_companies.yaml \
  --database data/job_search.sqlite \
  --csv data/job_matches.csv
```

## Flow

1. Load the resume and Pydantic-validated YAML config.
2. Render VC portfolio pages with Playwright and extract company names/websites with BeautifulSoup.
3. Discover company career links from each website.
4. Render career pages and collect job links/cards.
5. Filter to senior product/data/AI roles, removing junior, sales, marketing, support, and pure-engineering work.
6. Score each remaining job using Anthropic.
7. Upsert the results into SQLite and export the ranked table as CSV.

The generic HTML extractor handles conventional career pages and common ATS links. Add a source-specific adapter when a company exposes jobs only through a private API or highly custom frontend.

## Tests

```bash
cd job_search
python3 -m pytest tests
```

