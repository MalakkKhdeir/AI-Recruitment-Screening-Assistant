
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = "openai/gpt-4o-mini"

EMPTY_JOB = {
    "job_title": "",
    "required_skills": [],
    "preferred_skills": [],
    "education": "",
    "experience": "",
    "responsibilities": [],
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


def parse_job_description(job_text):
    if not isinstance(job_text, str) or not job_text.strip():
        raise ValueError("Job description is empty.")

    prompt = f"""
You are an AI recruitment assistant.

Analyze the job description and extract screening requirements.

Return one valid JSON object with exactly these fields:
{{
    "job_title": "",
    "required_skills": [],
    "preferred_skills": [],
    "education": "",
    "experience": "",
    "responsibilities": []
}}

Rules:
- Use only information supported by the job description.
- Never invent missing requirements.
- Use an empty string for missing text fields.
- Use an empty list for missing list fields.
- required_skills must contain explicitly mandatory skills.
- preferred_skills must contain preferred or optional skills.
- Never move a preferred skill into required_skills.
- Keep responsibilities as a list of strings.
- Return JSON only, without Markdown or explanations.

Job description:
----------------
{job_text}
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

    job = json.loads(result)

    if not isinstance(job, dict):
        raise ValueError("Model response must be a JSON object.")

    validated = {}

    for field in ("job_title", "education", "experience"):
        value = job.get(field, "")
        validated[field] = (
            value.strip() if isinstance(value, str) else ""
        )

    for field in (
        "required_skills",
        "preferred_skills",
        "responsibilities",
    ):
        value = job.get(field, [])

        if not isinstance(value, list):
            value = []

        validated[field] = [
            item.strip()
            for item in value
            if isinstance(item, str) and item.strip()
        ]

    return validated


if __name__ == "__main__":
    job_file = Path("job_description.txt")

    if not job_file.is_file():
        print(f"Job description file not found: {job_file}")

    else:
        try:
            job_text = job_file.read_text(encoding="utf-8")

            print(f"Processing: {job_file.name}")

            job = parse_job_description(job_text)

            print("\n===== JOB INFORMATION =====")
            print(json.dumps(
                job,
                indent=4,
                ensure_ascii=False,
            ))

        except json.JSONDecodeError:
            print("Error: OpenRouter returned invalid JSON.")

        except Exception as exc:
            print(f"Error: {type(exc).__name__}: {exc}")
