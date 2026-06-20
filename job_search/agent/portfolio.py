from __future__ import annotations

from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import Company


def extract_portfolio_companies(html: str, portfolio_url: str, limit: int) -> list[Company]:
    """Extract probable company links from a VC portfolio page."""
    soup = BeautifulSoup(html, "html.parser")
    portfolio_host = urlparse(portfolio_url).netloc.lower().removeprefix("www.")
    companies: dict[str, Company] = {}

    for anchor in soup.select("a[href]"):
        href = urljoin(portfolio_url, anchor["href"])
        parsed = urlparse(href)
        host = parsed.netloc.lower().removeprefix("www.")
        name = anchor.get_text(" ", strip=True)
        if not host or host == portfolio_host or not name or len(name) > 80:
            continue
        if any(value in href.lower() for value in ("linkedin.com", "twitter.com", "x.com", "mailto:")):
            continue
        companies.setdefault(
            host,
            Company(name=name, website=f"{parsed.scheme}://{parsed.netloc}", source=f"portfolio:{portfolio_url}"),
        )
        if len(companies) >= limit:
            break
    return list(companies.values())

