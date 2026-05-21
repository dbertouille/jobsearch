Wrapper around the `jobsearch` CLI. Interprets natural-language requests and runs the appropriate subcommand.

**Argument:** `$ARGUMENTS` — a natural-language instruction or a direct subcommand (see below).

## Subcommands

### discover
Find new jobs matching the configured criteria. Runs `python -m jobsearch discover` and reports how many jobs were found.

Trigger phrases: "discover", "find jobs", "search for jobs", "refresh", "update jobs"

### list [N] [--applied] [--company SLUG]
Show discovered jobs that haven't been dismissed. Runs `python -m jobsearch list --count N` (default N=10). Applied jobs are hidden by default; pass `--applied` to show only applied jobs. Pass `--company SLUG` to restrict results to a single company. Output is a JSON array of job objects (or `[]` if none found).

Trigger phrases: "list", "show jobs", "what jobs", "show me jobs", "show N jobs", "show applied jobs" (→ add `--applied`), "show jobs from [company]" (→ add `--company SLUG`)

Parse the JSON output to present jobs in a readable format. After listing, offer the user these follow-up actions for any job:
- "Tell me more about [job]" → use the already-parsed JSON (no need to re-read `state.json`), strip HTML from the description, and give a concise summary of the role, requirements, and salary.
- "Dismiss [job]" → run the dismiss subcommand.
- "Mark [job] as applied" → run the apply subcommand.
- "Tailor my resume for [job]" → invoke the `/tailor-resume` skill with that job's ID.

### companies [--with-jobs]
List all known companies. Runs `python -m jobsearch companies` and returns a JSON array of objects with `slug` and `source` fields. `source` is `"greenhouse"`, `"lever"`, or `null` if no jobs were found for that company. Pass `--with-jobs` to show only companies that have active job postings in the current state.

Trigger phrases: "list companies", "show companies", "what companies", "which companies", "companies with jobs" (→ add `--with-jobs`)

Present as a readable list. The `slug` is the value to pass to `list --company` or `dismiss`.

### get <job_id>
Print the full JSON for a single job. Runs `python -m jobsearch get <job_id>` and displays the output.

Trigger phrases: "get job", "show details", "full details", "raw json", "json for job", "tell me more about"

If the user refers to a job by company name or title instead of ID, read `state.json` to find the matching job ID first. Prefer this over reading `state.json` directly when the user wants structured detail about a specific job.

### apply <job_id>
Mark a job as applied. Runs `python -m jobsearch apply <job_id>`. Applied jobs are hidden from `list` by default.

Trigger phrases: "applied", "mark as applied", "I applied to", "submitted application"

If the user refers to a job by company name or title instead of ID, read `state.json` to find the matching job ID first.

### dismiss <job_id>
Remove a job from the list. Runs `python -m jobsearch dismiss <job_id>`.

Trigger phrases: "dismiss", "remove", "hide", "not interested in"

If the user refers to a job by company name or title instead of ID, read `state.json` to find the matching job ID first.


## Behavior

- Run all commands from the project root (the directory containing `state.json`).
- **On every invocation:** run `python -m jobsearch status` first and parse the JSON output. If `last_discover_time` is `null` or more than 24 hours before the current time, automatically run `python -m jobsearch discover` before proceeding with the user's requested action.
- If `$ARGUMENTS` is blank or unclear, ask the user what they want to do: discover new jobs, list existing ones, or dismiss one.
- After any command completes, briefly summarize the result and suggest a logical next step (e.g. after discover → "Run list to see them"; after list → "Want to tailor your resume for any of these?").
