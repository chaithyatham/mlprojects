from datetime import datetime, timezone

from agent.filters import job_matches
from agent.models import AgentConfig, JobPosting, ScoredJob
from agent.portfolio import extract_portfolio_companies
from agent.runner import JobSearchAgent
from agent.scoring import HeuristicJobScorer
from agent.storage import ResultsStore


def config() -> AgentConfig:
    return AgentConfig(
        target_roles=["Senior Product Manager", "Data Platform", "ML Infrastructure"],
        excluded_roles=["Product Marketing Manager"],
        locations=["Remote", "San Francisco"],
        seniority=["Senior", "Principal", "Director"],
    )


def job(title: str, location: str = "Remote") -> JobPosting:
    return JobPosting(
        external_id=title.replace(" ", "-"),
        company="Example",
        company_website="https://example.com",
        title=title,
        location=location,
        description="Own the AI and data platform product roadmap.",
        apply_url="https://example.com/apply",
        source="test",
        scraped_at=datetime.now(timezone.utc),
    )


def test_portfolio_extraction_filters_internal_links() -> None:
    companies = extract_portfolio_companies(
        """<a href="/about">About</a>
        <a href="https://www.acme.ai">Acme AI</a>
        <a href="https://www.exampledata.com">Example Data</a>""",
        "https://vc.example/portfolio",
        limit=10,
    )
    assert [company.name for company in companies] == ["Acme AI", "Example Data"]
    assert companies[0].website == "https://www.acme.ai"


def test_job_filter_keeps_target_role_and_excludes_marketing() -> None:
    assert job_matches(job("Senior Product Manager, Data Platform"), config())
    assert not job_matches(job("Senior Product Marketing Manager"), config())
    assert not job_matches(job("Senior Software Engineer, ML Infrastructure"), config())


def test_offline_scorer_returns_assessment() -> None:
    assessment = HeuristicJobScorer().score(
        "Senior product leader for AI, data platform, machine learning, and roadmap work.",
        job("Senior Product Manager, AI Platform"),
    )
    assert assessment.fit_score >= 75
    assert assessment.model == "heuristic-offline"


def test_store_upserts_and_exports_csv(tmp_path) -> None:
    posting = job("Principal Product Manager, Data Platform")
    assessment = HeuristicJobScorer().score("AI data platform roadmap", posting)
    result = ScoredJob(job=posting, assessment=assessment, match_level="strong")
    database = tmp_path / "results.sqlite"
    output = tmp_path / "results.csv"

    store = ResultsStore(database)
    store.initialize()
    store.upsert([result])

    assert store.export_csv(output) == 1
    assert "Principal Product Manager" in output.read_text()


def test_agent_discovers_and_scores_a_career_page(tmp_path) -> None:
    class FakeScraper:
        def fetch_pages(self, urls):
            return {
                "https://example.com": '<a href="/careers">Careers</a>',
                "https://example.com/careers": """
                    <a href="/jobs/product-data-platform">Senior Product Manager, Data Platform</a>
                    <a href="/jobs/product-marketing">Product Marketing Manager</a>
                """,
            }

    resume = tmp_path / "resume.md"
    resume.write_text("Senior product leader with AI, data platform, and roadmap experience.")
    agent = JobSearchAgent(
        config=AgentConfig(
            target_roles=["Senior Product Manager", "Data Platform"],
            excluded_roles=["Product Marketing Manager"],
            companies=[{"name": "Example", "website": "https://example.com"}],
        ),
        scraper=FakeScraper(),
        scorer=HeuristicJobScorer(),
    )

    results = agent.run(resume)
    assert len(results) == 1
    assert results[0].job.title == "Senior Product Manager, Data Platform"
