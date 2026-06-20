from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .runner import JobSearchAgent
from .scraper import PlaywrightScraper
from .scoring import build_scorer
from .storage import ResultsStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find and score senior product leadership roles.")
    parser.add_argument("--resume", type=Path, default=Path("resume.md"))
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    parser.add_argument("--target-companies", type=Path)
    parser.add_argument("--database", type=Path, default=Path("data/job_search.sqlite"))
    parser.add_argument("--csv", type=Path, default=Path("data/job_matches.csv"))
    parser.add_argument("--offline", action="store_true", help="Use deterministic local scoring instead of an LLM.")
    parser.add_argument("--headed", action="store_true", help="Show the browser while scraping.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config, args.target_companies)
    agent = JobSearchAgent(
        config=config,
        scraper=PlaywrightScraper(headless=not args.headed),
        scorer=build_scorer(config.llm_model, offline=args.offline),
    )
    results = agent.run(args.resume)
    store = ResultsStore(args.database)
    store.initialize()
    store.upsert(results)
    exported = store.export_csv(args.csv)
    strong = sum(result.match_level == "strong" for result in results)
    print(f"Collected {len(results)} matching jobs; {strong} are strong matches.")
    print(f"Saved SQLite results to {args.database} and exported {exported} rows to {args.csv}.")


if __name__ == "__main__":
    main()
