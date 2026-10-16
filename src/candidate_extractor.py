
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.cv_parser import extract_text


load_dotenv()

MODEL = "openai/gpt-4o-mini"

EMPTY_CANDIDATE = {
    "name": "",
    "email": "",
    "phone": "",
    "education": "",
    "skills": [],
    "experience": [],
    "projects": [],
}


def get_openrouter_client():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is missing. Check your .env file."
        )

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def extract_candidate_info(cv_text):
    if not isinstance(cv_text, str) or not cv_text.strip():
        raise ValueError("CV text is empty.")

    prompt = f"""
You are an AI recruitment assistant.

Extract candidate information from the CV below.

Return only one valid JSON object with exactly these fields:
{{
    "name": "",
    "email": "",
    "phone": "",
    "education": "",
    "skills": [],
    "experience": [],
    "projects": []
}}

Rules:
- Use only information explicitly supported by the CV.
- Never invent missing information.
- Use an empty string for missing text fields.
- Use an empty list for missing list fields.
- Skills must be a list of strings.
- Experience and projects must be lists of strings.
- Do not infer skills from a job title alone.
- Return JSON only, without Markdown or explanations.

CV:
----------------
{cv_text}
----------------
"""

    client = get_openrouter_client()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    result = response.choices[0].message.content

    if not result:
        raise ValueError("OpenRouter returned an empty response.")

    result = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        result.strip(),
        flags=re.IGNORECASE,
    )

    candidate = json.loads(result)

    if not isinstance(candidate, dict):
        raise ValueError("Model response must be a JSON object.")

    validated = {}

    for field in ("name", "email", "phone", "education"):
        value = candidate.get(field, "")
        if not isinstance(value, str):
            value = ""
        validated[field] = value.strip()

    for field in ("skills", "experience", "projects"):
        value = candidate.get(field, [])
        if not isinstance(value, list):
            value = []

        validated[field] = [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]

    return validated


if __name__ == "__main__":
    attachments_dir = Path("attachments")

    files = sorted(
        path
        for path in attachments_dir.iterdir()
        if path.is_file()
        and path.suffix.lower() in {".pdf", ".docx"}
    ) if attachments_dir.exists() else []

    if not files:
        print("No CV files found in attachments.")
    else:
        for cv_file in files:
            print(f"\nProcessing: {cv_file.name}")
            print("-" * 40)

            try:
                cv_text = extract_text(cv_file)
                candidate = extract_candidate_info(cv_text)

                print(json.dumps(
                    candidate,
                    indent=4,
                    ensure_ascii=False,
                ))

            except json.JSONDecodeError:
                print("Error: OpenRouter returned invalid JSON.")

            except Exception as exc:
                print(
                    f"Error processing {cv_file.name}: "
                    f"{type(exc).__name__}: {exc}"
                )
