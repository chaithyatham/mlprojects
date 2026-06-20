from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod

from .models import JobAssessment, JobPosting


class JobScorer(ABC):
    @abstractmethod
    def score(self, resume: str, job: JobPosting) -> JobAssessment:
        raise NotImplementedError


class AnthropicJobScorer(JobScorer):
    def __init__(self, model: str) -> None:
        import anthropic

        self.client = anthropic.Anthropic()
        self.model = model

    def score(self, resume: str, job: JobPosting) -> JobAssessment:
        prompt = f"""Assess this job for a senior product leader. Return only JSON with:
fit_score (0-100), why_this_is_a_fit, concerns, suggested_outreach_angle.

Resume:
{resume[:12000]}

Job:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Description: {job.description[:7000]}
"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=700,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(message.content[0].text)
        return JobAssessment(model=self.model, **data)


class HeuristicJobScorer(JobScorer):
    """Explicit offline mode for tests and development; not a substitute for LLM scoring."""

    def score(self, resume: str, job: JobPosting) -> JobAssessment:
        resume_lower = resume.lower()
        job_text = f"{job.title} {job.description}".lower()
        terms = ("ai", "data platform", "machine learning", "ml infrastructure", "governance", "roadmap")
        matches = [term for term in terms if term in resume_lower and term in job_text]
        score = min(95, 55 + len(matches) * 10 + (15 if "product" in job.title.lower() else 0))
        return JobAssessment(
            fit_score=score,
            why_this_is_a_fit=f"Shared signals: {', '.join(matches) or 'senior product scope'}.",
            concerns="Validate team scope, location, and product ownership during the first conversation.",
            suggested_outreach_angle="Lead with your experience translating data and AI capabilities into measurable product outcomes.",
            model="heuristic-offline",
        )


def build_scorer(model: str, offline: bool) -> JobScorer:
    if offline:
        return HeuristicJobScorer()
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required for LLM scoring. Use --offline for local development.")
    return AnthropicJobScorer(model)

