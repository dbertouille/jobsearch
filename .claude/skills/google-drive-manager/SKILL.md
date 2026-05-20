---
name: google-drive-manager
description: Manage Google Drive files and folders using the Google Workspace CLI. Use this skill whenever the user wants to list, search, upload, download, move, share, or delete files in Google Drive, create folders, manage permissions, or work with shared drives. Trigger for any request involving Google Drive, Drive files, Drive folders, or sharing files via Google.
---

# Google Drive Manager

Manage Google Drive via `nix run github:googleworkspace/cli` (the `gws` CLI).

The CLI alias used throughout this skill:

```bash
alias gws='nix --extra-experimental-features "nix-command flakes" run github:googleworkspace/cli --'
```

Always run commands with that prefix. For brevity, examples use `gws` to represent the full invocation.

## Authentication

Before any Drive operation, confirm credentials are set up:

```bash
gws auth status
```

If not authenticated, guide the user through one of these options (in order of preference):

**Option 1 — OAuth login (interactive, recommended for personal use):**
```bash
gws auth login
```
This opens a browser to complete OAuth2. Credentials are saved to `~/.config/gws/`.

**Option 2 — Credentials file (recommended for automation):**
Set `GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE` to a service account or OAuth client JSON file downloaded from Google Cloud Console.

**Option 3 — Pre-obtained token:**
Set `GOOGLE_WORKSPACE_CLI_TOKEN` to a valid access token.

If the user needs to set up a GCP project and OAuth client from scratch, run:
```bash
gws auth setup
```
This requires `gcloud` to be available.

---

## Common Operations

### List files

```bash
# All files (default: 20 results)
gws drive files list --format table

# All files, paginated
gws drive files list --page-all --format table

# Files in a specific folder
gws drive files list --params '{"q": "'\''FOLDER_ID'\'' in parents and trashed=false", "fields": "files(id,name,mimeType,modifiedTime,size)"}'

# Only folders
gws drive files list --params '{"q": "mimeType='\''application/vnd.google-apps.folder'\'' and trashed=false"}'
```

### Search files

The `q` parameter supports the [Drive search syntax](https://developers.google.com/workspace/drive/api/guides/search-files):

```bash
# By name
gws drive files list --params '{"q": "name contains '\''report'\'' and trashed=false"}'

# By type (docs, sheets, slides, pdf, etc.)
gws drive files list --params '{"q": "mimeType='\''application/pdf'\'' and trashed=false"}'

# Modified after a date
gws drive files list --params '{"q": "modifiedTime > '\''2025-01-01T00:00:00'\'' and trashed=false"}'

# Shared with me
gws drive files list --params '{"q": "sharedWithMe=true"}'

# Starred
gws drive files list --params '{"q": "starred=true and trashed=false"}'
```

Common MIME types:
| Type | MIME |
|------|------|
| Folder | `application/vnd.google-apps.folder` |
| Google Doc | `application/vnd.google-apps.document` |
| Google Sheet | `application/vnd.google-apps.spreadsheet` |
| Google Slides | `application/vnd.google-apps.presentation` |
| PDF | `application/pdf` |

### Get file metadata

```bash
gws drive files get --params '{"fileId": "FILE_ID", "fields": "id,name,mimeType,size,modifiedTime,parents,webViewLink"}'
```

### Upload a file

```bash
# Upload to My Drive root
gws drive +upload ./path/to/file.pdf

# Upload to a specific folder
gws drive +upload ./report.pdf --parent FOLDER_ID

# Upload with a different name
gws drive +upload ./data.csv --name 'Sales Data Q4.csv'
```

### Download a file

```bash
# Download by file ID
gws drive files download --params '{"fileId": "FILE_ID"}' --output ./local-file.ext
```

### Export a Google Workspace document

Google Docs/Sheets/Slides cannot be downloaded directly — use export:

```bash
# Export Google Doc as PDF
gws drive files export --params '{"fileId": "FILE_ID", "mimeType": "application/pdf"}' --output ./doc.pdf

# Export Google Doc as DOCX
gws drive files export --params '{"fileId": "FILE_ID", "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}' --output ./doc.docx

# Export Google Sheet as CSV
gws drive files export --params '{"fileId": "FILE_ID", "mimeType": "text/csv"}' --output ./sheet.csv

# Export Google Sheet as XLSX
gws drive files export --params '{"fileId": "FILE_ID", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}' --output ./sheet.xlsx
```

### Create a folder

```bash
gws drive files create --json '{"name": "My Folder", "mimeType": "application/vnd.google-apps.folder"}'

# Create inside a parent folder
gws drive files create --json '{"name": "Subfolder", "mimeType": "application/vnd.google-apps.folder", "parents": ["PARENT_FOLDER_ID"]}'
```

### Move a file

Moving in Drive means updating the file's `parents`:

```bash
gws drive files update --params '{"fileId": "FILE_ID", "addParents": "NEW_FOLDER_ID", "removeParents": "OLD_FOLDER_ID"}' --json '{}'
```

To find the current parent, get the file metadata first with `parents` in the `fields` parameter.

### Rename a file

```bash
gws drive files update --params '{"fileId": "FILE_ID"}' --json '{"name": "New Name"}'
```

### Copy a file

```bash
gws drive files copy --params '{"fileId": "FILE_ID"}' --json '{"name": "Copy of File"}'

# Copy into a specific folder
gws drive files copy --params '{"fileId": "FILE_ID"}' --json '{"name": "Copy of File", "parents": ["FOLDER_ID"]}'
```

### Delete a file (permanently)

```bash
gws drive files delete --params '{"fileId": "FILE_ID"}'
```

Note: this bypasses trash. To trash instead, update `trashed: true`:
```bash
gws drive files update --params '{"fileId": "FILE_ID"}' --json '{"trashed": true}'
```

### Empty trash

```bash
gws drive files emptyTrash
```

---

## Permissions and Sharing

### List permissions on a file

```bash
gws drive permissions list --params '{"fileId": "FILE_ID"}'
```

### Share a file

```bash
# Share with a specific user (reader/writer/commenter)
gws drive permissions create --params '{"fileId": "FILE_ID"}' --json '{"type": "user", "role": "writer", "emailAddress": "user@example.com"}'

# Share with anyone (public link)
gws drive permissions create --params '{"fileId": "FILE_ID"}' --json '{"type": "anyone", "role": "reader"}'

# Share with a domain
gws drive permissions create --params '{"fileId": "FILE_ID"}' --json '{"type": "domain", "role": "reader", "domain": "example.com"}'
```

Roles: `reader`, `commenter`, `writer`, `fileOrganizer`, `organizer`, `owner`

### Update a permission

```bash
gws drive permissions update --params '{"fileId": "FILE_ID", "permissionId": "PERMISSION_ID"}' --json '{"role": "reader"}'
```

### Remove a permission

```bash
gws drive permissions delete --params '{"fileId": "FILE_ID", "permissionId": "PERMISSION_ID"}'
```

---

## Shared Drives

```bash
# List shared drives
gws drive drives list --format table

# Get a shared drive
gws drive drives get --params '{"driveId": "DRIVE_ID"}'

# Search files in a shared drive
gws drive files list --params '{"driveId": "DRIVE_ID", "corpora": "drive", "includeItemsFromAllDrives": true, "supportsAllDrives": true, "q": "trashed=false"}'
```

---

## Output and Parsing Tips

- Use `--format table` for human-readable output
- Use `--format json` (default) for scripting and piping to `jq`
- Use `--format csv` for spreadsheet-friendly output
- Use `--page-all` to retrieve all results past the default page size

Extract specific fields:
```bash
# Get just IDs and names
gws drive files list --params '{"fields": "files(id,name)", "q": "trashed=false"}' | jq '.files[] | {id, name}'
```

---

## Checking the Schema

If you're unsure what parameters a command accepts:

```bash
gws schema drive.files.list
gws schema drive.files.create
gws schema drive.permissions.create
# etc.
```

---

## Error Reference

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | API error (Google returned an error) |
| 2 | Auth error — run `gws auth login` |
| 3 | Validation error — bad arguments |
| 4 | Discovery error — schema fetch failed |
| 5 | Internal error |
