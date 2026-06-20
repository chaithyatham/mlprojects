from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class CompanySeed(BaseModel):
    name: str
    website: str
    careers_url: str | None = None
    source: str = "config"


class AgentConfig(BaseModel):
    target_roles: list[str]
    excluded_roles: list[str]
    locations: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    companies: list[CompanySeed] = Field(default_factory=list)
    vc_portfolio_urls: list[str] = Field(default_factory=list)
    max_companies_per_portfolio: int = 75
    strong_match_threshold: int = 75
    llm_model: str = "claude-3-5-haiku-latest"


class Company(BaseModel):
    name: str
    website: str
    careers_url: str | None = None
    source: str


class JobPosting(BaseModel):
    external_id: str
    company: str
    company_website: str
    title: str
    location: str = ""
    description: str = ""
    apply_url: str
    careers_url: str | None = None
    source: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JobAssessment(BaseModel):
    fit_score: int = Field(ge=0, le=100)
    why_this_is_a_fit: str
    concerns: str
    suggested_outreach_angle: str
    model: str


class ScoredJob(BaseModel):
    job: JobPosting
    assessment: JobAssessment
    match_level: Literal["strong", "potential", "weak"]
