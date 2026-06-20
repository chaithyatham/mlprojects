from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .models import ScoredJob


class ResultsStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS job_results (
                    external_id TEXT PRIMARY KEY,
                    company TEXT NOT NULL,
                    title TEXT NOT NULL,
                    location TEXT,
                    apply_url TEXT NOT NULL,
                    careers_url TEXT,
                    source TEXT,
                    fit_score INTEGER NOT NULL,
                    match_level TEXT NOT NULL,
                    why_this_is_a_fit TEXT NOT NULL,
                    concerns TEXT NOT NULL,
                    suggested_outreach_angle TEXT NOT NULL,
                    model TEXT NOT NULL,
                    scraped_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def upsert(self, results: list[ScoredJob]) -> None:
        rows = [
            (
                result.job.external_id, result.job.company, result.job.title, result.job.location,
                result.job.apply_url, result.job.careers_url, result.job.source,
                result.assessment.fit_score, result.match_level, result.assessment.why_this_is_a_fit,
                result.assessment.concerns, result.assessment.suggested_outreach_angle,
                result.assessment.model, result.job.scraped_at.isoformat(),
            )
            for result in results
        ]
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """INSERT INTO job_results (
                    external_id, company, title, location, apply_url, careers_url, source,
                    fit_score, match_level, why_this_is_a_fit, concerns, suggested_outreach_angle,
                    model, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(external_id) DO UPDATE SET
                    fit_score=excluded.fit_score, match_level=excluded.match_level,
                    why_this_is_a_fit=excluded.why_this_is_a_fit, concerns=excluded.concerns,
                    suggested_outreach_angle=excluded.suggested_outreach_angle, model=excluded.model,
                    scraped_at=excluded.scraped_at, updated_at=CURRENT_TIMESTAMP""",
                rows,
            )

    def export_csv(self, csv_path: Path) -> int:
        with sqlite3.connect(self.database_path) as connection:
            dataframe = pd.read_sql_query(
                "SELECT * FROM job_results ORDER BY fit_score DESC, company, title", connection
            )
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        dataframe.to_csv(csv_path, index=False)
        return len(dataframe)

