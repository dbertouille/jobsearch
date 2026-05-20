# job-search

A personal CLI for discovering, filtering, ranking, and resume/cover-letter writing,

## How it works

1. **Discover** — fetches job postings from a seed list of companies (plus any discovered via Remotive), filters by location keywords, and ranks results by cosine similarity to your experience summary using a local sentence transformer model.
2. **List / Get / Dismiss** — browse ranked results, inspect individual postings, and dismiss ones you're not interested in.
3. **Tailor** — use the Claude Code skills to tailor your resume or cover letter for a specific job via Google Drive.

## Setup

### Prerequisites

- [Devbox](https://www.jetpack.io/devbox) (manages Python 3.11 and system deps)
- [direnv](https://direnv.net/) (loads environment variables from `.envrc`)
- A `pass` password store entry for `google-workspace-cli-token` (for Drive integration)

### Install

```bash
devbox shell        # activates venv and runs pip install -r requirements.txt
direnv allow        # loads env vars from .envrc
```

### Configure

Copy the example config and fill in your details:

```bash
cp config.example.json config.json
```

If you would like to give access to Google Drive to read your Resume and/or cover letters, you need to add an access token to the password store. Note access tokens are short-lived so this will only grant access for 1-hour. Long-lived access is in the backlog.

1. Go to https://developers.google.com/oauthplayground/
2. Select scope(s) `https://www.googleapis.com/auth/drive` or `https://www.googleapis.com/auth/drive.readonly`
3. Click Authorize APIs
4. Go through the auth flow
5. Click Exchange authorization code for tokens
6. Copy the access token
7. Add it to pass with `pass add google-workspace-cli-token`
8. Reload env with `direnv allow`

`config.json` fields:

| Field | Description |
|---|---|
| `seed_companies` | List of company slugs to always check (e.g. `"stripe"`, `"1password"`) |
| `require_location_keywords` | Jobs must match at least one keyword in their location (e.g. `"canada"`) |
| `experience_summary` | Your professional background — used to rank jobs by semantic similarity |

`config.json` and `state.json` are gitignored.

## Claude Code skills

This project is primarily intended to be interacted through Claude

- **`/google-drive-manager`** — how to interact through google drive for resume/cover-letter retrieval and storage
- **`/job-discovery`** — discovers and lists jobs; auto-runs `discover` if data is older than 24 hours
- **`/tailor-resume`** — tailors your resume (from Google Drive) for a specific job using Claude
- **`/tailor-cover-letter`** — tailors your cover letter template for a specific job

Examples

Show me relevant job postings

```
> Show me the 10 job postings most relevant to me
```

Tailor your resume to a job found by job discovery
```
> Tailor my resume to job 1
```

Tailor your cover letter to a job posting on the web.
```
> Tailor my cover letter to https://www.linkedin.com/jobs/view/1234
```

## JobSearch

JobSearch is the CLI tool used for job discovery. Although it is intended to be used by Claude, you can also directly interact with it.

```
python -m jobsearch [-v] <command>
```

| Command | Description |
|---|---|
| `discover` | Fetch jobs from all known companies, filter, rank, and save to `state.json` |
| `list [--count N]` | Print up to N undismissed jobs as JSON (default: 10) |
| `get <job_id>` | Print full JSON for a single job |
| `dismiss <job_id>` | Mark a job as dismissed so it no longer appears in `list` |
| `status` | Print `last_discover_time` as JSON |

Add `-v` / `--verbose` for INFO-level logging on stderr.

### State file

`state.json` is the local database. It holds:

- `companies` — known companies and which ATS boards they use
- `jobs` — all discovered job objects (id, company, title, location, description, salary_range, url, source)
- `dismissed` — list of dismissed job IDs
- `last_discover_time` — ISO 8601 UTC timestamp of the last `discover` run
