from __future__ import annotations

from pathlib import Path

from .filters import job_matches
from .models import AgentConfig, Company, JobPosting, ScoredJob
from .portfolio import extract_portfolio_companies
from .scraper import PlaywrightScraper, discover_careers_url, extract_jobs_from_html
from .scoring import JobScorer


class JobSearchAgent:
    def __init__(self, config: AgentConfig, scraper: PlaywrightScraper, scorer: JobScorer) -> None:
        self.config = config
        self.scraper = scraper
        self.scorer = scorer

    def run(self, resume_path: Path) -> list[ScoredJob]:
        resume = resume_path.read_text()
        companies = self._collect_companies()
        jobs = self._collect_jobs(companies)
        matches = [job for job in jobs if job_matches(job, self.config)]
        return [self._score(resume, job) for job in matches]

    def _collect_companies(self) -> list[Company]:
        companies = [
            Company(name=seed.name, website=seed.website, careers_url=seed.careers_url, source=seed.source)
            for seed in self.config.companies
        ]
        portfolio_pages = self.scraper.fetch_pages(self.config.vc_portfolio_urls)
        for portfolio_url, html in portfolio_pages.items():
            if html:
                companies.extend(
                    extract_portfolio_companies(html, portfolio_url, self.config.max_companies_per_portfolio)
                )
        unique: dict[str, Company] = {}
        for company in companies:
            unique.setdefault(company.website.rstrip("/").lower(), company)
        return list(unique.values())

    def _collect_jobs(self, companies: list[Company]) -> list[JobPosting]:
        homepage_urls = [company.website for company in companies if not company.careers_url]
        homepages = self.scraper.fetch_pages(homepage_urls)
        for company in companies:
            if not company.careers_url and homepages.get(company.website):
                company.careers_url = discover_careers_url(company, homepages[company.website])

        careers = [company for company in companies if company.careers_url]
        career_pages = self.scraper.fetch_pages([company.careers_url for company in careers if company.careers_url])
        jobs: list[JobPosting] = []
        for company in careers:
            html = career_pages.get(company.careers_url or "", "")
            if html:
                jobs.extend(extract_jobs_from_html(company, company.careers_url or "", html))
        return jobs

    def _score(self, resume: str, job: JobPosting) -> ScoredJob:
        assessment = self.scorer.score(resume, job)
        threshold = self.config.strong_match_threshold
        match_level = "strong" if assessment.fit_score >= threshold else (
            "potential" if assessment.fit_score >= 55 else "weak"
        )
        return ScoredJob(job=job, assessment=assessment, match_level=match_level)

