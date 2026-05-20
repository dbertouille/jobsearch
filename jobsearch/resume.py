import json
import os

import anthropic
import requests


def _auth_headers() -> dict:
    token = os.environ.get("GOOGLE_WORKSPACE_CLI_TOKEN")
    if not token:
        raise EnvironmentError("GOOGLE_WORKSPACE_CLI_TOKEN is not set.")
    return {"Authorization": f"Bearer {token}"}


def download_as_text(file_id: str) -> str:
    r = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}/export",
        params={"mimeType": "text/plain"},
        headers=_auth_headers(),
        timeout=30,
    )
    r.raise_for_status()
    return r.text


def tailor_resume(resume_text: str, job: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set.")
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": f"""You are a professional resume writer. Tailor the resume below for the given job posting.

Adjust emphasis and wording to match the role's requirements. Keep the same structure and do not invent experience that isn't there. Return only the tailored resume text with no additional commentary.

Job Title: {job['title']}
Company: {job['company']}
Location: {job['location']}

Job Description:
{job['description']}

Resume:
{resume_text}"""
        }]
    )

    return message.content[0].text


def create_doc(name: str, content: str) -> str:
    boundary = "jobsearch_boundary"
    metadata = json.dumps({"name": name, "mimeType": "application/vnd.google-apps.document"})
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
        f"{metadata}\r\n"
        f"--{boundary}\r\n"
        f"Content-Type: text/plain\r\n\r\n"
        f"{content}\r\n"
        f"--{boundary}--"
    )
    r = requests.post(
        "https://www.googleapis.com/upload/drive/v3/files",
        params={"uploadType": "multipart", "fields": "webViewLink"},
        headers={
            **_auth_headers(),
            "Content-Type": f"multipart/related; boundary={boundary}",
        },
        data=body.encode("utf-8"),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["webViewLink"]
