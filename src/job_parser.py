import json
import ollama
from pathlib import Path


MODEL = "qwen3:8b"


def parse_job_description(job_text):

    prompt = f"""
You are an AI recruitment assistant.

Analyze the following job description and extract the important
requirements for candidate screening.

Return ONLY valid JSON.
Do not add explanations or markdown.

Use exactly this structure:

{{
    "job_title": "",
    "required_skills": [],
    "preferred_skills": [],
    "education": "",
    "experience": "",
    "responsibilities": []
}}

Rules:
- Extract information only from the job description.
- Do not invent missing information.
- If information is not available, use an empty string or empty list.
- required_skills should contain skills explicitly required for the job.
- preferred_skills should contain skills that are preferred or considered a plus.
- responsibilities should contain the main responsibilities of the position.

Job Description:
----------------
{job_text}
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

    # Remove markdown code fences if Qwen adds them
    result = result.replace("```json", "")
    result = result.replace("```", "")
    result = result.strip()

    try:
        job = json.loads(result)

    except json.JSONDecodeError:
        print("Could not parse Qwen response as JSON.")
        print(result)

        job = {
            "job_title": "",
            "required_skills": [],
            "preferred_skills": [],
            "education": "",
            "experience": "",
            "responsibilities": []
        }

    return job


if __name__ == "__main__":

    job_file = Path("job_description.txt")

    if not job_file.exists():
        print("Job description file not found.")

    else:

        job_text = job_file.read_text(
            encoding="utf-8"
        )

        print(f"Processing: {job_file.name}")

        job = parse_job_description(job_text)

        print("\n===== JOB INFORMATION =====")

        print(
            json.dumps(
                job,
                indent=4,
                ensure_ascii=False
            )
        )