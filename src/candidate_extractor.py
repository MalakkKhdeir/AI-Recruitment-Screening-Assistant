import json
import re
from pathlib import Path

import ollama

from cv_parser import extract_text


MODEL = "qwen3:8b"


def extract_candidate_info(cv_text):

    prompt = f"""
You are an AI recruitment assistant.

Extract candidate information from the following CV.

Return ONLY valid JSON.
Do not add explanations or markdown.

Use exactly this structure:

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
- Extract information only from the CV.
- Do not invent missing information.
- If information is not available, use an empty string or empty list.
- Skills should be a list of skills.
- Experience should be a list of relevant work/internship experiences.
- Projects should be a list of projects.

CV:
----------------
{cv_text}
----------------
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    result = response["message"]["content"].strip()

    
    result = re.sub(r"```json\s*", "", result)
    result = re.sub(r"```\s*", "", result)

    try:
        candidate = json.loads(result)
    except json.JSONDecodeError:
        print("Could not parse Qwen response as JSON.")
        print(result)

        candidate = {
            "name": "",
            "email": "",
            "phone": "",
            "education": "",
            "skills": [],
            "experience": [],
            "projects": []
        }

    return candidate


if __name__ == "__main__":

    pdf_files = list(Path("attachments").glob("*.pdf"))

    if not pdf_files:
        print("No CV files found.")

    else:
        cv_file = pdf_files[0]

        print(f"Processing: {cv_file.name}")

        cv_text = extract_text(cv_file)

        candidate = extract_candidate_info(cv_text)

        print("\n===== CANDIDATE INFORMATION =====")

        print(json.dumps(
            candidate,
            indent=4,
            ensure_ascii=False
        ))