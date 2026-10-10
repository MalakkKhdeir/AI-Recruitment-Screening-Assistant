
import json
import ollama
from pathlib import Path

from cv_parser import extract_text
from candidate_extractor import extract_candidate_info
from job_parser import parse_job_description
from semantic_matcher import calculate_semantic_similarity


MODEL = "qwen3:8b"


def calculate_match(candidate, job):
    """Compare candidate information with job requirements."""

    prompt = f"""
You are an AI recruitment screening assistant.

Compare the candidate information with the job requirements.

Candidate:
{json.dumps(candidate, indent=2, ensure_ascii=False)}

Job:
{json.dumps(job, indent=2, ensure_ascii=False)}

Evaluate the candidate based ONLY on the provided information.

Return ONLY valid JSON using exactly this structure:

{{
    "match_score": 0,
    "matched_skills": [],
    "missing_skills": [],
    "matching_experience": [],
    "concerns": [],
    "recommendation": ""
}}

Rules:
- match_score must be a number from 0 to 100.
- matched_skills must be supported by candidate information.
- missing_skills must contain important required skills without supporting evidence.
- matching_experience must contain relevant documented experience or projects.
- concerns must describe relevant gaps or missing evidence.
- recommendation must be one of:
  "Strong Match", "Good Match", "Partial Match", "Weak Match".
- Do not invent information.
- Do not judge the candidate based on personal information.
- Missing information is not proof that the candidate lacks a skill.
- Do not make a final hiring decision.
"""

    # Run Ollama
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )
        raw_result = response["message"]["content"].strip()

    except Exception as error:
        return {
            "match_score": None,
            "semantic_similarity": None,
            "matched_skills": [],
            "missing_skills": [],
            "matching_experience": [],
            "concerns": [f"AI analysis failed: {error}"],
            "recommendation": "Not Evaluated"
        }

    # Remove Markdown fences if present
    raw_result = raw_result.replace("```json", "").replace("```", "").strip()

    # Parse and validate JSON
    try:
        result = json.loads(raw_result)

        if not isinstance(result, dict):
            raise ValueError("AI response must be a JSON object")

        required_keys = [
            "match_score",
            "matched_skills",
            "missing_skills",
            "matching_experience",
            "concerns",
            "recommendation"
        ]

        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing key in AI response: {key}")

        score = result["match_score"]
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not 0 <= score <= 100
        ):
            raise ValueError("match_score must be between 0 and 100")

        for key in [
            "matched_skills",
            "missing_skills",
            "matching_experience",
            "concerns"
        ]:
            if not isinstance(result[key], list):
                raise ValueError(f"{key} must be a list")

        allowed_recommendations = {
            "Strong Match",
            "Good Match",
            "Partial Match",
            "Weak Match"
        }

        if result["recommendation"] not in allowed_recommendations:
            raise ValueError("Invalid recommendation")

    except (json.JSONDecodeError, ValueError) as error:
        return {
            "match_score": None,
            "semantic_similarity": None,
            "matched_skills": [],
            "missing_skills": [],
            "matching_experience": [],
            "concerns": [f"Invalid AI response: {error}"],
            "recommendation": "Not Evaluated"
        }

    # Prepare text for semantic similarity
    required_skills = job.get("required_skills", [])
    if not isinstance(required_skills, list):
        required_skills = [required_skills]

    job_requirements = " ".join(
        str(item) for item in required_skills if item
    )

    candidate_information = ""

    for key in ("skills", "experience", "projects"):
        value = candidate.get(key, [])

        if isinstance(value, list):
            candidate_information += " " + " ".join(
                str(item) for item in value if item
            )
        elif value:
            candidate_information += " " + str(value)

    # Avoid presenting similarity as proof of qualification
    if not job_requirements.strip() or not candidate_information.strip():
        result["semantic_similarity"] = None
        result.setdefault(
            "concerns", []
        ).append("Insufficient text to calculate semantic similarity.")
        return result

    try:
        print("Running semantic matching...")

        semantic_score = calculate_semantic_similarity(
            job_requirements,
            candidate_information
        )

        result["semantic_similarity"] = round(
            float(semantic_score) * 100, 2
        )

    except Exception as error:
        result["semantic_similarity"] = None
        result.setdefault("concerns", []).append(
            f"Semantic matching failed: {error}"
        )

    return result


def main():
    """Screen all PDF and DOCX CVs in the attachments folder."""

    attachments_dir = Path("attachments")
    cv_files = sorted(
        list(attachments_dir.glob("*.pdf"))
        + list(attachments_dir.glob("*.docx"))
        + list(attachments_dir.glob("*.PDF"))
        + list(attachments_dir.glob("*.DOCX"))
    )

    if not cv_files:
        print("No PDF or DOCX CV files found in attachments.")
        return

    job_file = Path("job_description.txt")

    if not job_file.exists():
        print("Job description not found: job_description.txt")
        return

    try:
        job_text = job_file.read_text(encoding="utf-8")
        job = parse_job_description(job_text)
    except Exception as error:
        print(f"Could not process job description: {error}")
        return

    results = []

    for cv_file in cv_files:
        print("\n" + "=" * 55)
        print(f"Processing CV: {cv_file.name}")
        print("=" * 55)

        try:
            cv_text = extract_text(cv_file)

            if not cv_text or not cv_text.strip():
                print("Could not extract text from this CV.")
                continue

            print("Extracting candidate information...")
            candidate = extract_candidate_info(cv_text)

            if not isinstance(candidate, dict):
                print("Candidate extraction returned an invalid result.")
                continue

            print("Running AI matching...")
            result = calculate_match(candidate, job)
            result["cv_file"] = cv_file.name
            results.append(result)

            print("\n===== CV SCREENING RESULT =====")
            print(json.dumps(result, indent=4, ensure_ascii=False))

            print("\n===== SCREENING SUMMARY =====")
            print(f"CV: {cv_file.name}")
            print(f"AI Match Score: {result.get('match_score', 'N/A')}")
            print(
                "Semantic Similarity: "
                f"{result.get('semantic_similarity', 'N/A')}%"
            )
            print(
                "Recommendation: "
                f"{result.get('recommendation', 'Not Evaluated')}"
            )

        except Exception as error:
            print(f"Error processing {cv_file.name}: {error}")
            continue

    # Summary of all processed CVs
    print("\n" + "=" * 55)
    print("===== ALL CANDIDATES SUMMARY =====")
    print("=" * 55)

    for result in sorted(
        results,
        key=lambda item: (
            item.get("match_score") is None,
            -(item.get("match_score") or 0)
        )
    ):
        print(
            f"{result['cv_file']} | "
            f"AI Score: {result.get('match_score', 'N/A')} | "
            f"Semantic Similarity: "
            f"{result.get('semantic_similarity', 'N/A')} | "
            f"{result.get('recommendation', 'Not Evaluated')}"
        )


if __name__ == "__main__":
    main()
