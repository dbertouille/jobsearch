Tailor the resume for a specific job from the discovered job list.

**Argument:** `$ARGUMENTS` — a job ID from `state.json` (e.g. `4480727005`), a job URL, or leave blank to pick interactively.

## Steps

### 1. Resolve the job

- If `$ARGUMENTS` looks like a numeric ID, invoke the `job-discovery` skill with `get $ARGUMENTS` to retrieve the full job JSON.
- If `$ARGUMENTS` is blank, invoke the `job-discovery` skill with `list` to show the first 10 non-dismissed jobs, then ask the user to pick one by ID, and invoke `job-discovery` with `get <chosen_id>`.
- If `$ARGUMENTS` looks like a URL, invoke the `job-discovery` skill with `list` to find the job whose `"url"` matches, then invoke `job-discovery` with `get <id>`. If no match is found, fetch the page with WebFetch and extract the job title, company, and description from it directly.

The job JSON returned by `get` has fields: `id`, `company`, `title`, `location`, `description`, `salary_range`, `url`, `source`. Use these fields in subsequent steps.

### 2. Get the resume

Use the `google-drive-manager` skill to search for the resume in Google Drive. Search for files named "resume" and present any matches to the user so they can confirm which one to use. Download the confirmed file as plain text.

If the skill finds nothing or the user prefers not to use Drive, ask them to paste their resume text directly into the chat.

### 3. Tailor the resume

Using your own reasoning, produce a tailored version of the resume following these rules:

- **Keep all facts true.** Do not invent experience, skills, or accomplishments that aren't in the original.
- **Reorder and reweight.** Bring forward experience most relevant to this role.
- **Mirror the job's language.** Use the same terminology the posting uses where it accurately describes real experience (e.g. "observability" instead of "monitoring" if that's what the job says).
- **Tighten the summary** to speak directly to this company and role.
- **Surface the most relevant skills first** in any skills section.
- **Do not change dates, titles, or company names.**
- **Keep the same overall structure** (sections, formatting style).

The `description` field may contain HTML — strip tags mentally when reading it.

### 4. Output and save

Print the complete tailored resume.

Then ask: **"Save this as a .docx file on Google Drive? (y/n)"**

If yes:
1. Write the tailored resume to a local temp file (e.g. `resume_tailored.txt`).
2. Run `pandoc -o resume_tailored.docx resume_tailored.txt` to convert it to DOCX.
3. Use the `google-drive-manager` skill to upload `resume_tailored.docx` with the name `"[Company] — [Job Title] Resume"`.
4. Delete both local temp files.
5. Print the resulting Google Drive link.
