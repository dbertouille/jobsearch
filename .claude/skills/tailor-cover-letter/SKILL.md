Tailor a cover letter for a specific job using the cover letter template from Google Drive.

**Argument:** `$ARGUMENTS` — a job ID from `state.json` (e.g. `4480727005`), a job URL, or leave blank to pick interactively.

## Steps

### 1. Resolve the job

- If `$ARGUMENTS` looks like a numeric ID, invoke the `job-discovery` skill with `get $ARGUMENTS` to retrieve the full job JSON.
- If `$ARGUMENTS` is blank, invoke the `job-discovery` skill with `list` to show the first 10 non-dismissed jobs, then ask the user to pick one by ID, and invoke `job-discovery` with `get <chosen_id>`.
- If `$ARGUMENTS` looks like a URL, invoke the `job-discovery` skill with `list` to find the job whose `"url"` matches, then invoke `job-discovery` with `get <id>`. If no match is found, fetch the page with WebFetch and extract the job title, company, and description from it directly.

The job JSON returned by `get` has fields: `id`, `company`, `title`, `location`, `description`, `salary_range`, `url`, `source`. Use these fields in subsequent steps.

### 2. Get the cover letter template

Use the `google-drive-manager` skill to search for a cover letter template in Google Drive. Search for files with "cover letter" in the name. Present any matches to the user so they can confirm which template to use. Download the confirmed file twice:
- As **plain text** (for reading and tailoring)
- As **DOCX** to `tmp/cover_letter_original.docx` (to use as a pandoc reference doc for formatting)

If the skill finds nothing or the user prefers not to use Drive, ask them to paste their cover letter template directly into the chat (no DOCX reference will be available in that case).

### 3. Get the resume

Use the `google-drive-manager` skill to search for the resume in Google Drive. Search for files named "resume" and present any matches to the user so they can confirm which one to use. Export the confirmed file as plain text.

If the skill finds nothing or the user prefers not to use Drive, ask them to paste their resume text directly into the chat.

### 4. Tailor the cover letter

Using the job description, the cover letter template, and the resume as context, produce a tailored cover letter following these rules:

- **Preserve the template's structure and tone.** Keep the same opening/closing format, paragraph flow, and voice as the template.
- **Keep all facts true.** Do not invent experience, skills, or accomplishments that aren't in the resume.
- **Address the specific role and company.** Reference the job title, company name, and key requirements from the posting.
- **Mirror the job's language.** Use terminology from the posting where it accurately describes real experience.
- **Highlight the most relevant experience.** Surface accomplishments from the resume that best match the role's requirements.
- **Keep it concise.** A cover letter should be no more than one page — three to four short paragraphs.
- **Do not use generic filler phrases** like "I am excited to apply" or "I believe I would be a great fit" unless they appear naturally in the template.

The `description` field may contain HTML — strip tags mentally when reading it.

### 5. Output and save

Print the complete tailored cover letter.

Then ask: **"Save this as a .docx file on Google Drive? (y/n)"**

If yes:
1. Ensure the `tmp/` directory exists at the project root (create it if needed).
2. Write the tailored cover letter to `tmp/cover_letter_tailored.md` (use Markdown formatting: `**bold**` where appropriate, blank lines between paragraphs).
3. Convert to DOCX using the original as a reference doc to preserve formatting:
   - If `tmp/cover_letter_original.docx` exists: `pandoc -o tmp/cover_letter_tailored.docx --reference-doc=tmp/cover_letter_original.docx tmp/cover_letter_tailored.md`
   - Otherwise: `pandoc -o tmp/cover_letter_tailored.docx tmp/cover_letter_tailored.md`
4. Use the `google-drive-manager` skill to upload `tmp/cover_letter_tailored.docx` with the name `"[Company] — [Job Title] Cover Letter"`.
5. Delete all local temp files from `tmp/` (`cover_letter_tailored.md`, `cover_letter_tailored.docx`, `cover_letter_original.docx`).
6. Print the resulting Google Drive link.
