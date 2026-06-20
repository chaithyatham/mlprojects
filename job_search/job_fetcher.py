import re
import time
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from companies import TARGET_ASHBY, TARGET_GREENHOUSE, TARGET_LEVER

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 JobSearchBot/1.0"})
SESSION.mount("https://", HTTPAdapter(pool_connections=50, pool_maxsize=50))
TIMEOUT = 10


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


_PM_FETCH_TERMS = [
    "product manager", "product management", "head of product",
    "director of product", "vp of product", "vp, product",
    "vice president of product", "chief product officer", "cpo",
    "group product manager", "gpm", "product lead",
    "principal product manager", "senior product manager",
    "technical product manager", "platform product manager",
]


_PM_TITLE_PATTERNS = [
    r"\bmanager,\s*product\b",
    r"\bdirector,\s*product\b",
    r"\bprincipal,\s*product\b",
    r"\bsenior,\s*product\b",
    r"\blead,\s*product\b",
    r"\bproduct\s+lead\b",
    r"\bproduct\s+owner\b",
]


def _is_pm_title(title: str) -> bool:
    title_lower = title.lower()
    return any(p in title_lower for p in _PM_FETCH_TERMS) or any(
        re.search(pattern, title_lower) for pattern in _PM_TITLE_PATTERNS
    )


def _is_relevant(title: str, keywords: list[str]) -> bool:
    title_lower = title.lower()
    is_pm_search = any("product" in kw.lower() for kw in keywords)
    if is_pm_search:
        return _is_pm_title(title)
    return any(kw.lower() in title_lower for kw in keywords)


def _job_base(meta: dict) -> dict:
    return {
        "company": meta["name"],
        "domain": meta["domain"],
        "vc": meta.get("vc", ""),
        "stage": meta.get("stage", ""),
        "stage_focus": meta.get("stage_focus", ""),
        "source_note": "Curated VC-backed startup registry; verify funding stage before applying.",
    }


# ── Greenhouse ────────────────────────────────────────────────────────────────

def fetch_greenhouse(slug: str, meta: dict, keywords: list[str]) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        jobs = []
        for j in data.get("jobs", []):
            title = j.get("title", "")
            if not _is_relevant(title, keywords):
                continue
            desc = _strip_html(j.get("content", ""))[:1000]
            loc = j.get("location", {}).get("name", "")
            jobs.append({
                "id": f"gh-{slug}-{j.get('id')}",
                "title": title,
                **_job_base(meta),
                "location": loc,
                "url": j.get("absolute_url", ""),
                "description": desc,
                "source": "greenhouse",
            })
        return jobs
    except Exception as e:
        log.debug("Greenhouse %s: %s", slug, e)
        return []


# ── Lever ─────────────────────────────────────────────────────────────────────

def fetch_lever(slug: str, meta: dict, keywords: list[str]) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        jobs = []
        for j in r.json():
            title = j.get("text", "")
            if not _is_relevant(title, keywords):
                continue
            cats = j.get("categories", {})
            loc = cats.get("location", cats.get("allLocations", [""])[0] if cats.get("allLocations") else "")
            desc_raw = j.get("descriptionPlain", "") or _strip_html(j.get("description", ""))
            desc = desc_raw[:1000]
            jobs.append({
                "id": f"lv-{slug}-{j.get('id')}",
                "title": title,
                **_job_base(meta),
                "location": loc,
                "url": j.get("hostedUrl", ""),
                "description": desc,
                "source": "lever",
            })
        return jobs
    except Exception as e:
        log.debug("Lever %s: %s", slug, e)
        return []


def fetch_ashby(slug: str, meta: dict, keywords: list[str]) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        r = SESSION.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        jobs = []
        for j in r.json().get("jobs", []):
            title = j.get("title", "")
            if not _is_relevant(title, keywords):
                continue
            jobs.append({
                "id": f"ashby-{slug}-{j.get('id')}",
                "title": title,
                **_job_base(meta),
                "location": j.get("location", ""),
                "url": j.get("applyUrl") or j.get("jobUrl", ""),
                "description": (j.get("descriptionPlain") or _strip_html(j.get("descriptionHtml", "")))[:1000],
                "source": "ashby",
            })
        return jobs
    except Exception as e:
        log.debug("Ashby %s: %s", slug, e)
        return []


# ── Google Careers ────────────────────────────────────────────────────────────

def fetch_google(query: str) -> list[dict]:
    url = "https://careers.google.com/api/v3/search/"
    params = {"q": query, "page_size": 30, "page": 1, "location_filter": "United States"}
    try:
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        jobs = []
        for j in r.json().get("jobs", []):
            locs = j.get("locations", [])
            loc = locs[0].get("display", "") if locs else ""
            apply_url = j.get("apply_url", "") or j.get("job_id", "")
            if not apply_url.startswith("http"):
                apply_url = f"https://careers.google.com/jobs/results/{apply_url}"
            jobs.append({
                "id": f"google-{j.get('job_id', '')}",
                "title": j.get("title", ""),
                "company": "Google",
                "domain": "google.com",
                "vc": "",
                "location": loc,
                "url": apply_url,
                "description": _strip_html(j.get("description", ""))[:1000],
                "source": "google",
            })
        return jobs
    except Exception as e:
        log.debug("Google: %s", e)
        return []


# ── Microsoft Careers ─────────────────────────────────────────────────────────

def fetch_microsoft(query: str) -> list[dict]:
    url = "https://gcsservices.careers.microsoft.com/search/api/v1/search"
    params = {"q": query, "l": "en_us", "pg": 1, "pgSz": 30, "o": "Relevance", "flt": "true"}
    try:
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        jobs = []
        for j in r.json().get("operationResult", {}).get("result", {}).get("jobs", []):
            loc_parts = [j.get("primaryWorkLocation", "")]
            jobs.append({
                "id": f"msft-{j.get('jobId', '')}",
                "title": j.get("title", ""),
                "company": "Microsoft",
                "domain": "microsoft.com",
                "vc": "",
                "location": ", ".join(loc_parts),
                "url": f"https://jobs.careers.microsoft.com/global/en/job/{j.get('jobId', '')}",
                "description": j.get("descriptionTeaser", "")[:1000],
                "source": "microsoft",
            })
        return jobs
    except Exception as e:
        log.debug("Microsoft: %s", e)
        return []


# ── Amazon Jobs ───────────────────────────────────────────────────────────────

def fetch_amazon(query: str) -> list[dict]:
    url = "https://www.amazon.jobs/en/jobs.json"
    params = {
        "normalized_country_code[]": "USA",
        "category[]": "software-development",
        "result_limit": 30,
        "sort": "relevant",
        "query": query,
    }
    try:
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        jobs = []
        for j in r.json().get("jobs", []):
            jobs.append({
                "id": f"amzn-{j.get('id_icims', '')}",
                "title": j.get("title", ""),
                "company": "Amazon",
                "domain": "amazon.com",
                "vc": "",
                "location": j.get("location", ""),
                "url": f"https://www.amazon.jobs{j.get('job_path', '')}",
                "description": _strip_html(j.get("description", ""))[:1000],
                "source": "amazon",
            })
        return jobs
    except Exception as e:
        log.debug("Amazon: %s", e)
        return []


# ── Salesforce ────────────────────────────────────────────────────────────────

def fetch_salesforce(query: str) -> list[dict]:
    url = "https://careers.salesforce.com/api/jobs"
    params = {"pageSize": 20, "page": 1, "keyword": query}
    try:
        r = SESSION.get(url, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        jobs = []
        for j in r.json().get("items", []):
            jobs.append({
                "id": f"sf-{j.get('jobId', '')}",
                "title": j.get("jobTitle", ""),
                "company": "Salesforce",
                "domain": "salesforce.com",
                "vc": "",
                "location": j.get("primaryLocation", ""),
                "url": j.get("applyUrl", ""),
                "description": j.get("jobDescription", "")[:1000],
                "source": "salesforce",
            })
        return jobs
    except Exception as e:
        log.debug("Salesforce: %s", e)
        return []


# ── Main orchestrator ─────────────────────────────────────────────────────────

def fetch_all_jobs(
    target_roles: list[str],
    skills: list[str],
    progress_cb=None,
    stage_focus: tuple[str, ...] = ("Series C/D",),
) -> list[dict]:
    """
    Fetch jobs from all sources concurrently.
    progress_cb(message, pct) is called periodically.
    Returns a flat list of raw job dicts.
    """
    keywords = list(dict.fromkeys(target_roles + ["Product Manager"] + skills[:5]))
    greenhouse = {
        slug: meta
        for slug, meta in TARGET_GREENHOUSE.items()
        if not stage_focus or meta.get("stage_focus") in stage_focus
    }
    lever = {
        slug: meta
        for slug, meta in TARGET_LEVER.items()
        if not stage_focus or meta.get("stage_focus") in stage_focus
    }
    ashby = {
        slug: meta
        for slug, meta in TARGET_ASHBY.items()
        if not stage_focus or meta.get("stage_focus") in stage_focus
    }

    all_jobs: list[dict] = []
    total = max(1, len(greenhouse) + len(lever) + len(ashby))
    done = 0

    def _cb(msg):
        nonlocal done
        done += 1
        pct = 20 + int((done / total) * 60)
        if progress_cb:
            progress_cb(msg, pct)

    futures = {}
    with ThreadPoolExecutor(max_workers=24) as pool:
        for slug, meta in greenhouse.items():
            f = pool.submit(fetch_greenhouse, slug, meta, keywords)
            futures[f] = f"Searching {meta['name']}…"

        for slug, meta in lever.items():
            f = pool.submit(fetch_lever, slug, meta, keywords)
            futures[f] = f"Searching {meta['name']}…"

        for slug, meta in ashby.items():
            f = pool.submit(fetch_ashby, slug, meta, keywords)
            futures[f] = f"Searching {meta['name']}…"

        for f in as_completed(futures):
            msg = futures[f]
            try:
                jobs = f.result()
                all_jobs.extend(jobs)
            except Exception:
                pass
            _cb(msg)

    # Deduplicate by URL
    seen = set()
    unique = []
    for j in all_jobs:
        key = j.get("url") or j["id"]
        if key and key not in seen:
            seen.add(key)
            unique.append(j)

    return unique
