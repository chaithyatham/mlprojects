from __future__ import annotations

import hashlib
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import Company, JobPosting

CAREER_HINTS = ("career", "careers", "jobs", "join-us", "joinus", "work-with-us", "workat")
ATS_HOSTS = ("boards.greenhouse.io", "jobs.lever.co", "jobs.ashbyhq.com", "myworkdayjobs.com")


def discover_careers_url(company: Company, html: str) -> str | None:
    """Find a linked careers page, preferring known ATS boards."""
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[str] = []
    for anchor in soup.select("a[href]"):
        href = urljoin(company.website, anchor["href"])
        text = anchor.get_text(" ", strip=True).lower()
        combined = f"{href.lower()} {text}"
        if any(hint in combined for hint in CAREER_HINTS):
            candidates.append(href)
    if not candidates:
        return None
    candidates.sort(key=lambda url: 0 if any(host in url for host in ATS_HOSTS) else 1)
    return candidates[0]


def extract_jobs_from_html(company: Company, careers_url: str, html: str) -> list[JobPosting]:
    """Extract job cards and links from conventional career pages and ATS boards."""
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[JobPosting] = []
    seen: set[str] = set()
    for anchor in soup.select("a[href]"):
        title = anchor.get_text(" ", strip=True)
        href = urljoin(careers_url, anchor["href"])
        normalized = re.sub(r"\s+", " ", title).strip()
        if len(normalized) < 5 or len(normalized) > 160 or href in seen:
            continue
        haystack = f"{normalized} {href}".lower()
        if not ("product" in haystack or "data" in haystack or "machine-learning" in haystack or "ml-" in haystack):
            continue
        seen.add(href)
        parent_text = anchor.parent.get_text(" ", strip=True) if anchor.parent else ""
        external_id = hashlib.sha256(f"{company.name}:{href}".encode()).hexdigest()[:20]
        jobs.append(
            JobPosting(
                external_id=external_id,
                company=company.name,
                company_website=company.website,
                title=normalized,
                location=_extract_location(parent_text),
                description=parent_text[:2500],
                apply_url=href,
                careers_url=careers_url,
                source=company.source,
            )
        )
    return jobs


def _extract_location(text: str) -> str:
    match = re.search(r"(remote|[A-Z][a-z]+(?:,\s*[A-Z]{2}|,\s*[A-Z][a-z]+))", text)
    return match.group(1) if match else ""


class PlaywrightScraper:
    """Browser-backed page loader used for dynamic portfolio and career pages."""

    def __init__(self, headless: bool = True) -> None:
        self.headless = headless

    def fetch_pages(self, urls: list[str]) -> dict[str, str]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError("Install Playwright and run 'python -m playwright install chromium'.") from exc

        pages: dict[str, str] = {}
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            page = browser.new_page()
            for url in urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                    page.wait_for_timeout(500)
                    pages[url] = page.content()
                except Exception:
                    pages[url] = ""
            browser.close()
        return pages

