from __future__ import annotations

import re

from .models import AgentConfig, JobPosting


DEFAULT_INCLUDED_TERMS = (
    "director product",
    "director of product",
    "senior product manager",
    "principal product manager",
    "staff product manager",
    "ai platform",
    "data platform",
    "ml infrastructure",
    "machine learning infrastructure",
    "data product",
    "data governance",
    "data acquisition",
)

DEFAULT_EXCLUDED_TERMS = (
    "junior",
    "intern",
    "associate product manager",
    "sales",
    "marketing",
    "support",
    "software engineer",
    "engineering manager",
    "devops",
    "site reliability",
)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _has_phrase(text: str, phrase: str) -> bool:
    return _normalize(phrase) in _normalize(text)


def job_matches(job: JobPosting, config: AgentConfig) -> bool:
    """Keep senior product/data/ML positions while excluding adjacent functions."""
    title = _normalize(job.title)
    searchable = f"{title} {_normalize(job.description[:500])}"
    excluded = tuple(config.excluded_roles) + DEFAULT_EXCLUDED_TERMS
    if any(_has_phrase(title, term) for term in excluded):
        return False

    included = tuple(config.target_roles) + DEFAULT_INCLUDED_TERMS
    has_target_signal = any(_has_phrase(searchable, term) for term in included)
    has_product_title = "product" in title and any(
        term in title for term in ("manager", "director", "principal", "head", "lead")
    )
    if not (has_target_signal or has_product_title):
        return False

    if config.seniority and not any(_has_phrase(title, term) for term in config.seniority):
        return False

    if config.locations:
        location = _normalize(job.location)
        if location and not any(_has_phrase(location, value) for value in config.locations):
            return False
    return True

