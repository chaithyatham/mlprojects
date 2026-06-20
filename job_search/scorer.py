import re
import math
from collections import Counter


# ── PM title classification ───────────────────────────────────────────────────

# Title must contain at least one PM term
_PM_TITLE_TERMS = [
    "product manager", "product management", "head of product",
    "director of product", "vp of product", "vp, product",
    "vice president of product", "chief product officer", "cpo",
    "group product manager", "gpm", "product lead",
    "principal product manager", "senior product manager",
    "technical product manager", "platform product manager",
    "product owner",
]

_PM_TITLE_PATTERNS = [
    r"\bmanager,\s*product\b",
    r"\bdirector,\s*product\b",
    r"\bprincipal,\s*product\b",
    r"\bsenior,\s*product\b",
    r"\blead,\s*product\b",
]

# These are staff-equivalent seniority signals (when combined with a PM title)
_STAFF_PLUS_SIGNALS = [
    "staff", "principal", "senior staff", "group", "director", "senior director",
    "vp", "vice president", "head of", "svp", "chief", "lead", "distinguished",
    "senior", "sr.",  # include Senior PM — maps to staff-equiv at most companies
]

# These explicitly exclude junior / non-PM roles
_EXCLUDE_TERMS = [
    "associate product manager", "apm", "junior", "intern",
    "technical program manager", "tpm", "project manager",
    "product marketing manager", "product operations",
    "product support", "product designer", "product analyst",
]


def is_product_role(title: str) -> bool:
    """Return True for product-management roles while excluding adjacent roles."""
    t = title.lower()

    if any(x in t for x in _EXCLUDE_TERMS):
        return False

    return any(p in t for p in _PM_TITLE_TERMS) or any(
        re.search(pattern, t) for pattern in _PM_TITLE_PATTERNS
    )


def _seniority_bonus(profile: dict, title: str) -> int:
    t = title.lower()
    level = profile.get("experience_level", "mid")
    has_senior_signal = any(s in t for s in _STAFF_PLUS_SIGNALS)

    if level == "staff":
        return 15 if has_senior_signal else 5
    if level == "senior":
        return 12 if has_senior_signal else 8
    return 8 if not any(s in t for s in ("director", "vp", "head of", "chief")) else 2


# ── Domain scoring ────────────────────────────────────────────────────────────

_HIGH_DOMAIN = [
    # Marketplace / consumer (Tinder background)
    "marketplace", "consumer", "social", "dating", "matching", "recommendation",
    "algorithm", "algorithmic", "ranking", "personalization", "feed",
    # ML / AI products (his expertise)
    "machine learning", "ml", "ai", "artificial intelligence", "llm",
    "model", "data platform", "data product", "analytics platform",
    # Growth / engagement (Tinder KPIs)
    "growth", "engagement", "retention", "monetization", "subscription",
    "platform", "ecosystem",
    "product-led", "self serve", "self-service",
]

_MED_DOMAIN = [
    "enterprise", "b2b", "saas", "api", "developer", "infrastructure",
    "fintech", "payments", "data", "search", "mobile",
]


def _domain_bonus(job: dict) -> int:
    """Return 0–25 bonus based on domain/industry fit."""
    combined = (job["title"] + " " + job["company"] + " " + job.get("description", "")).lower()
    high_hits = sum(1 for t in _HIGH_DOMAIN if t in combined)
    med_hits  = sum(1 for t in _MED_DOMAIN  if t in combined)
    stage_bonus = 6 if job.get("stage_focus") == "Series C/D" else 2
    return min(25, high_hits * 5 + med_hits * 2 + stage_bonus)


# ── Resume analysis ───────────────────────────────────────────────────────────

_PM_SKILLS = [
    "roadmap", "stakeholder", "go-to-market", "gtm", "kpi", "okr",
    "product strategy", "product vision", "user research", "a/b test",
    "a/b testing", "experimentation", "sprint", "agile", "scrum", "backlog",
    "product manager", "product management", "product lead", "product owner",
    "north star", "prfaq", "prd",
]

_TECH_SKILLS = [
    "machine learning", "nlp", "llm", "sql", "python", "data pipeline",
    "data science", "analytics", "spark", "databricks", "sap", "erp",
    "aws", "gcp", "azure", "kafka", "snowflake", "api", "microservices",
]


def analyze_resume(resume_text: str) -> dict:
    text = resume_text.lower()
    lines = [l.strip() for l in resume_text.splitlines() if l.strip()]

    # Name
    name = ""
    for line in lines[:5]:
        if "@" not in line and not any(c.isdigit() for c in line) and 1 < len(line.split()) <= 5:
            name = line.strip()
            break

    # Email
    m = re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", resume_text)
    email = m.group(0) if m else ""

    # Years experience
    m = re.search(r"(\d{1,2})\s*\+?\s*years?\b", text)
    yrs = int(m.group(1)) if m else _estimate_years(resume_text)
    yrs = min(yrs, 25)

    level = "staff" if yrs >= 10 else ("senior" if yrs >= 7 else "mid")

    pm_skills  = [k for k in _PM_SKILLS   if k in text]
    tech_skills = [k for k in _TECH_SKILLS if k in text]
    skills = list(dict.fromkeys(pm_skills + tech_skills))[:20]

    is_pm = len(pm_skills) >= 2 or "product manager" in text

    if is_pm:
        target_titles = [
            "Product Manager", "Senior Product Manager", "Staff Product Manager",
            "Principal Product Manager", "Group Product Manager",
            "Director of Product", "Head of Product",
        ]
    else:
        target_titles = ["Product Manager", "Technical Product Manager", "AI Product Manager"]

    summary = (
        f"Product-oriented profile with {yrs}+ years. "
        f"Relevant signals: {', '.join((pm_skills + tech_skills)[:5]) or 'resume keywords'}."
    )

    return {
        "name": name,
        "email": email,
        "experience_years": yrs,
        "experience_level": level,
        "is_pm": is_pm,
        "target_titles": target_titles,
        "skills": skills,
        "summary": summary,
        "_resume_text": resume_text[:4000],
    }


def _estimate_years(text: str) -> int:
    years = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
    if len(years) >= 2:
        return min(max(int(y) for y in years) - min(int(y) for y in years), 20)
    return 5


# ── Scoring ───────────────────────────────────────────────────────────────────

def _build_candidate_text(profile: dict) -> str:
    return (
        "Senior product manager with expertise in: "
        + ", ".join(profile.get("skills", []))
        + ". Target roles: "
        + ", ".join(profile.get("target_titles", []))
        + ". Background: "
        + profile.get("_resume_text", "")[:2000]
    )


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z][a-z0-9+#.-]{2,}", text.lower())


def _cosine_counter(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    numerator = sum(a[t] * b[t] for t in common)
    denom_a = math.sqrt(sum(v * v for v in a.values()))
    denom_b = math.sqrt(sum(v * v for v in b.values()))
    if not denom_a or not denom_b:
        return 0.0
    return numerator / (denom_a * denom_b)


def _similarity_scores(candidate_text: str, job_texts: list[str]) -> list[float]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        matrix = TfidfVectorizer(stop_words="english", max_features=4000).fit_transform(
            [candidate_text] + job_texts
        )
        return cosine_similarity(matrix[0:1], matrix[1:]).flatten().tolist()
    except Exception:
        candidate = Counter(_tokens(candidate_text))
        return [_cosine_counter(candidate, Counter(_tokens(text))) for text in job_texts]


def _score_reason(profile: dict, job: dict, domain_bonus: int, seniority_bonus: int) -> str:
    skills = set(s.lower() for s in profile.get("skills", []))
    combined = (job["title"] + " " + job.get("description", "")).lower()
    matched = [s for s in skills if s in combined and len(s) > 3][:4]
    if matched:
        return f"Resume match: {', '.join(matched)}."
    if domain_bonus >= 15:
        return "Strong product/domain overlap with your background."
    if seniority_bonus >= 12:
        return "Seniority appears aligned with your resume."
    if domain_bonus >= 8:
        return "Moderate domain overlap with your experience."
    return "Product role at a target late-stage startup."


def score_all_jobs(
    profile: dict,
    jobs: list[dict],
    progress_cb=None,
    top_n: int = 50,
) -> list[dict]:
    is_pm = profile.get("is_pm", False)

    if progress_cb:
        progress_cb("Filtering to product-management roles…", 81)

    filtered = [j for j in jobs if is_product_role(j["title"])]

    if progress_cb:
        progress_cb(f"Found {len(filtered)} PM roles — scoring…", 83)

    if not filtered:
        return []

    candidate_text = _build_candidate_text(profile)

    total = len(filtered)
    job_texts = [f"{j['title']} at {j['company']}. {j.get('description','')[:600]}" for j in filtered]
    all_sims = _similarity_scores(candidate_text, job_texts)

    if progress_cb:
        progress_cb(f"Scored {total} PM roles…", 95)

    scored = []
    for job, sim in zip(filtered, all_sims):
        sem_score = max(0, min(50, int(sim * 160)))
        domain_bonus = _domain_bonus(job)
        seniority_bonus = _seniority_bonus(profile, job["title"])
        title_bonus = 10 if is_pm else 6
        total_score = min(100, sem_score + domain_bonus + seniority_bonus + title_bonus)

        j = dict(job)
        j["score"] = total_score
        j["reason"] = _score_reason(profile, job, domain_bonus, seniority_bonus)
        scored.append(j)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]
