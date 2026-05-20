#!/usr/bin/env python3

from html.parser import HTMLParser
from datetime import datetime, timezone
import json
import logging
import os
import re
import typing

import requests
from sentence_transformers import SentenceTransformer


CONFIG_FILE = "config.json"


class Config(typing.TypedDict):
    require_location_keywords: list[str]
    experience_summary: str
    seed_companies: list[str]


def load_config() -> Config:
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Config file '{CONFIG_FILE}' not found. Create it before running discover.")
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

class StateCompany(typing.TypedDict):
    name: str
    sources: dict[str, dict]


class Job(typing.TypedDict):
    id: str
    company: str
    title: str
    location: str
    description: str
    salary_range: str
    url: str
    source: str


class State(typing.TypedDict):
    companies: dict[str, StateCompany]
    jobs: list[Job]
    dismissed: list[str]
    last_discover_time: str | None


STATE_FILE = "state.json"



# =========================================================
# HELPERS
# =========================================================

class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def strip_html(html: str) -> str:
    s = _HTMLStripper()
    s.feed(html)
    return s.get_text().strip()


_SALARY_RE = re.compile(
    r'\$\s*\d[\d,]*(?:\.\d+)?(?:\s*[kK])?\s*(?:[-–—]\s*\$\s*\d[\d,]*(?:\.\d+)?(?:\s*[kK])?)?'
    r'(?:\s*(?:USD|CAD|per year|annually|/yr|/year|a year))?',
    re.IGNORECASE,
)


def extract_salary(text: str) -> str:
    m = _SALARY_RE.search(text)
    return m.group(0).strip() if m else ""


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug).strip('-')
    return slug


# =========================================================
# ATS FETCHERS
# =========================================================
def fetch_greenhouse(company: str) -> tuple[bool, list[Job]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"

    r = requests.get(url, timeout=20)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logging.warning(f"Greenhouse: Company '{company}' not found")
            return False, []
        raise
    data = r.json()

    jobs: list[Job] = []

    for j in data.get("jobs", []):
        description = strip_html(j.get("content", "") or "")
        jobs.append({
            "id": str(j.get("id")),
            "company": company,
            "title": j.get("title", ""),
            "location": j.get("location", {}).get("name", ""),
            "description": description,
            "salary_range": extract_salary(description),
            "url": j.get("absolute_url", ""),
            "source": "greenhouse"
        })

    return True, jobs


def fetch_lever(company: str) -> tuple[bool, list[Job]]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"

    r = requests.get(url, timeout=20)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            logging.warning(f"Lever: Company '{company}' not found")
            return False, []
        raise
    data = r.json()

    jobs: list[Job] = []

    for j in data:
        description = j.get("descriptionPlain", "") or ""

        salary_range = ""
        sr = j.get("salaryRange") or {}
        if sr.get("min") or sr.get("max"):
            lo, hi = sr.get("min"), sr.get("max")
            currency = sr.get("currency", "")
            if lo and hi:
                salary_range = f"${lo:,} - ${hi:,} {currency}".strip()
            elif lo:
                salary_range = f"${lo:,}+ {currency}".strip()
            elif hi:
                salary_range = f"up to ${hi:,} {currency}".strip()
        else:
            # look through structured lists for a compensation header
            for lst in j.get("lists", []):
                header = (lst.get("text") or "").lower()
                if any(kw in header for kw in ("salary", "compensation", "pay", "wage")):
                    content = strip_html(lst.get("content", "") or "")
                    salary_range = extract_salary(content) or content[:80]
                    break
            if not salary_range:
                salary_range = extract_salary(description)

        jobs.append({
            "id": j.get("id") or j.get("hostedUrl"),
            "company": company,
            "title": j.get("text", ""),
            "location": j.get("categories", {}).get("location", ""),
            "description": description,
            "salary_range": salary_range,
            "url": j.get("hostedUrl", ""),
            "source": "lever"
        })

    return True, jobs


class Source(typing.TypedDict):
    name: str
    fetch_jobs: typing.Callable[[str], tuple[bool, list[Job]]]


SOURCES: dict[str, Source] = {
    "greenhouse": {
        "name": "greenhouse",
        "fetch_jobs": fetch_greenhouse,
    },
    "lever": {
        "name": "lever",
        "fetch_jobs": fetch_lever,
    },
}

# =========================================================
# STATE
# =========================================================

def load_state() -> State:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)

    return {
        "companies": {},
        "jobs": [],
        "dismissed": [],
        "last_discover_time": None,
    }


def save_state(state: State) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# =========================================================
# DISCOVERY
# =========================================================


def discover_from_remotive(state: State) -> None:
    """Fetch the Remotive software-dev feed and probe any company not yet in state."""
    r = requests.get(
        "https://remotive.com/api/remote-jobs?category=software-dev",
        timeout=20,
    )
    r.raise_for_status()

    company_names: set[str] = {
        job.get("company_name", "") for job in r.json().get("jobs", [])
    }

    for name in sorted(company_names):
        slug = slugify(name)
        if not slug or slug in state["companies"]:
            continue
        state["companies"][slug] = {"name": slug, "sources": {}}
        logging.info(f"Discovered {slug}")


# =========================================================
# FILTERS
# =========================================================

def passes_filters(job: Job, require_location_keywords: list[str]) -> bool:
    if not any(kw in job["location"].lower() for kw in require_location_keywords):
        return False
    return True

# =========================================================
# MAIN PIPELINE
# =========================================================

def run() -> list[Job]:
    config = load_config()
    state = load_state()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    resume_emb = model.encode(config["experience_summary"])

    # 1. COMPANY DISCOVERY
    # a. Load seed companies from config
    # b. Discover new companies via Remotive (could add more sources later)
    for company in config["seed_companies"]:
        slug = slugify(company)
        if slug not in state["companies"]:
            state["companies"][slug] = {"name": slug, "sources": {}}
    discover_from_remotive(state)
    save_state(state)

    # 2. JOB DISCOVERY
    all_jobs: list[Job] = []
    for slug, company in state["companies"].items():
        for source in SOURCES.values():
            # If company has a source and it doesn't match this source, skip it
            # Assumption is company posts all jobs to same source
            # May not be true but can adjust later if needed
            source_state = company["sources"].get(source["name"])
            if source_state and source_state.get("hasSlug") is False:
                continue
            has_slug, jobs = source["fetch_jobs"](company["name"])
            company["sources"][source["name"]] = {"hasSlug": has_slug}
            if len(jobs) > 0:
                state["companies"][slug]["source"] = source["name"]
                all_jobs.extend(jobs)

    # 3. FILTERING
    filtered_jobs = [job for job in all_jobs if passes_filters(job, config["require_location_keywords"])]

    # 4. SORTING
    results = sorted(
        filtered_jobs,
        key=lambda job: model.similarity(resume_emb, model.encode(job["title"] + job["description"])),
        reverse=True
    )

    # 5. UPDATE STATE
    state["jobs"] = results
    state["last_discover_time"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    return results

