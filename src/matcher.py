import hashlib

import json

import re

from pathlib import Path


from src.candidate_extractor import extract_candidate_info, get_openrouter_client

from src.cv_parser import extract_text

from src.job_parser import parse_job_description

from src.semantic_matcher import calculate_semantic_similarity


MODEL = "openai/gpt-4o-mini"

BASE_DIR = Path(__file__).resolve().parent.parent

ATTACHMENTS_DIR = BASE_DIR / "attachments"


JOB_FILE = BASE_DIR / "job_description.txt"
JOBS_FILE = BASE_DIR / "jobs.json"
RESULTS_FILE = BASE_DIR / "results.json"


STATUSES = {"Meets", "Partially Meets", "Does Not Meet"}

NO_EVIDENCE = "No evidence found in the provided candidate information."

SEMANTIC_REVIEW_THRESHOLD = 55.0

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def normalize_text(value):

    """Normalize text for case-insensitive comparisons."""

    value = str(value or "").casefold()

    value = re.sub(r"[^a-z0-9+#.]+", " ", value)

    return " ".join(value.split())


def normalize_email(value):

    """Return a normalized email address, or an empty string."""

    return value.strip().casefold() if isinstance(value, str) else ""


def get_requirements(job):

    """Collect and deduplicate job requirements."""

    requirements = []

    for field, category in [

        ("required_skills", "Must-Have"),

        ("preferred_skills", "Preferred"),

    ]:

        values = job.get(field, [])

        if not isinstance(values, list):

            values = [values]

        for value in values:

            if value and str(value).strip():

                requirements.append({

                    "requirement": str(value).strip(),

                    "type": category,

                })


    for field in ("education", "experience", "languages", "certifications"):

        value = job.get(field, "")

        values = value if isinstance(value, list) else [value]

        for item in values:

            if item and str(item).strip():

                requirements.append({

                    "requirement": str(item).strip(),

                    "type": field.capitalize(),

                })


    unique, seen = [], set()

    for item in requirements:

        key = (normalize_text(item["requirement"]), item["type"])

        if key not in seen:

            seen.add(key)

            unique.append(item)

    return unique


def candidate_values(candidate):

    """Return candidate information grouped by field."""

    result = {}

    for field in ("skills", "experience", "projects", "education",

                  "languages", "certifications"):

        value = candidate.get(field, [])

        if not isinstance(value, list):

            value = [value]

        result[field] = [

            str(item).strip() for item in value if item and str(item).strip()

        ]

    return result


def candidate_text(candidate):

    """Combine extracted candidate information into text."""

    return "\n".join(

        value

        for field_values in candidate_values(candidate).values()

        for value in field_values

    )


def get_relevant_candidate_info(requirement, req_type, candidate):

    """Select candidate fields relevant to a job requirement."""

    values = candidate_values(candidate)

    if req_type == "Education":

        fields = ["education"]

    elif req_type == "Experience":

        fields = ["experience", "projects"]

    elif req_type == "Languages":

        fields = ["languages"]

    elif req_type == "Certifications":

        fields = ["certifications"]

    else:

        fields = ["skills", "experience", "projects"]

    return "\n".join(

        item for field in fields for item in values.get(field, [])

    )


def find_explicit_evidence(requirement, candidate, cv_text=""):

    """

    Find traceable evidence in structured fields or the original CV text.

    Semantic similarity alone is never treated as evidence.

    """

    values = candidate_values(candidate)

    req = normalize_text(requirement)


    # Exact normalized match in a structured candidate field.

    for field_values in values.values():

        for value in field_values:

            if normalize_text(value) == req:

                return value


    # Explicit component checks for compound requirements.

    skill_groups = {

        "communication and leadership": [["communication"], ["leadership"]],

        "agile and scrum methodologies": [["agile"], ["scrum"]],

        "understanding of software development life cycle sdlc": [

            ["sdlc", "software development life cycle"]

        ],

        "knowledge of git and github": [["git"], ["github"]],

    }

    for group_name, components in skill_groups.items():

        if req == normalize_text(group_name):

            normalized_skills = [

                normalize_text(skill) for skill in values.get("skills", [])

            ]

            all_components_found = all(

                any(

                    alias in skill

                    for skill in normalized_skills

                    for alias in aliases

                )

                for aliases in components

            )

            if all_components_found:

                return "; ".join(values.get("skills", []))


    # Multiword requirement explicitly contained in a structured CV entry.

    for field_values in values.values():

        for value in field_values:

            normalized_value = normalize_text(value)

            if len(req.split()) >= 2 and req in normalized_value:

                return value


    # Only return a quote from the original CV when it contains the key terms

    # of the requirement. This is deliberately conservative.

    normalized_cv = normalize_text(cv_text)

    meaningful_terms = [

        term for term in req.split()

        if len(term) > 2 and term not in {

            "and", "with", "for", "the", "experience", "understanding",

            "knowledge", "familiarity", "strong", "basic", "similar",

        }

    ]

    if meaningful_terms and all(term in normalized_cv for term in meaningful_terms):

        for line in cv_text.splitlines():

            normalized_line = normalize_text(line)

            if all(term in normalized_line for term in meaningful_terms):

                return line.strip()[:400] or None


    return None


def verify_evidence(evidence, cv_text, candidate):

    """Verify that a proposed evidence quote is traceable to source text."""

    if not isinstance(evidence, str) or not evidence.strip():

        return None

    evidence = evidence.strip()

    if evidence == NO_EVIDENCE:

        return None


    normalized_evidence = normalize_text(evidence)

    if not normalized_evidence:

        return None


    sources = [cv_text, candidate_text(candidate)]

    for source in sources:

        if normalized_evidence in normalize_text(source):

            return evidence

    return None


def calculate_match(candidate, job, cv_text=None):

    """Evaluate every requirement and keep evidence distinct from similarity."""

    requirements = get_requirements(job)

    structured_text = candidate_text(candidate)

    original_cv_text = cv_text or structured_text

    result = {

        "match_score": None,

        "semantic_similarity": None,

        "matched_skills": [],

        "missing_skills": [],

        "matching_experience": [],

        "concerns": [],

        "recommendation": "Not Evaluated",

        "requirements_analysis": [],

    }


    if not requirements:

        result["concerns"].append("No job requirements were extracted.")

        return result


    if not structured_text.strip() and not original_cv_text.strip():

        result["concerns"].append("No candidate evidence was extracted.")

        result["requirements_analysis"] = [

            {**req, "status": "Does Not Meet", "evidence": NO_EVIDENCE,

             "semantic_similarity": None, "semantic_review": False}

            for req in requirements

        ]

        return result


    prompt = f"""

You are an AI recruitment screening assistant. Evaluate every requirement

separately using only the candidate's CV.


Extracted candidate information:

{json.dumps(candidate, ensure_ascii=False)}


Original CV text:

{original_cv_text}


Requirements:

{json.dumps(requirements, ensure_ascii=False)}


Return one JSON object with:

{{

  "requirements_analysis": [

    {{

      "requirement": "exact requirement text",

      "type": "Must-Have",

      "status": "Meets",

      "evidence": "short exact quote from the CV"

    }}

  ],

  "matching_experience": [],

  "concerns": []

}}


Rules:

- Return one item for every supplied requirement.

- Copy requirement text and type exactly.

- Allowed statuses: Meets, Partially Meets, Does Not Meet.

- Use only facts explicitly supported by the CV.

- Evidence must be a short exact quotation from the CV.

- A listed skill shows a candidate claim, not independently verified proficiency.

- Academic/personal projects can be relevant for entry-level roles; do not invent facts.

- If evidence is insufficient, use exactly: "{NO_EVIDENCE}"

- Missing evidence does not prove the candidate lacks a skill.

- Do not make a hiring decision. Return JSON only.

- matching_experience and concerns must be lists of strings.

"""


    try:

        client = get_openrouter_client()

        response = client.chat.completions.create(

            model=MODEL,

            messages=[{"role": "user", "content": prompt}],

            temperature=0,

            response_format={"type": "json_object"},

        )

        content = response.choices[0].message.content

        if not content:

            raise ValueError("OpenRouter returned an empty response.")

        data = json.loads(content)

        if not isinstance(data, dict):

            raise ValueError("Expected a JSON object.")


        analyses = data.get("requirements_analysis", [])

        if not isinstance(analyses, list):

            raise ValueError("Invalid requirements_analysis.")


        lookup = {}

        for item in analyses:

            if not isinstance(item, dict) or not isinstance(

                item.get("requirement"), str

            ):

                continue

            key = (

                normalize_text(item["requirement"]),

                normalize_text(item.get("type", "")),

            )

            lookup[key] = item


        for req in requirements:

            key = (

                normalize_text(req["requirement"]),

                normalize_text(req["type"]),

            )

            item = lookup.get(key, {})

            proposed_status = item.get("status")

            if proposed_status not in STATUSES:

                proposed_status = "Does Not Meet"


            # First verify the model's quote, then look for explicit evidence

            # independently in the CV and structured extraction.

            evidence = verify_evidence(

                item.get("evidence"), original_cv_text, candidate

            )

            explicit_evidence = find_explicit_evidence(

                req["requirement"], candidate, original_cv_text

            )

            if explicit_evidence:

                evidence = explicit_evidence


            # Critical fix: a model's "Meets" status cannot stand if there is

            # no traceable evidence. Similarity never changes this status.

            if evidence is None:

                status = "Does Not Meet"

            elif proposed_status == "Meets":

                status = "Meets"

            elif proposed_status == "Partially Meets":

                status = "Partially Meets"

            else:

                # Explicit evidence exists, but model judged it insufficient.

                status = "Partially Meets"


            relevant_info = get_relevant_candidate_info(

                req["requirement"], req["type"], candidate

            )

            similarity = None

            if relevant_info.strip():

                try:

                    similarity = round(

                        float(calculate_semantic_similarity(

                            req["requirement"], relevant_info

                        )) * 100,

                        2,

                    )

                except Exception:

                    similarity = None


            semantic_review = (

                evidence is None

                and similarity is not None

                and similarity >= SEMANTIC_REVIEW_THRESHOLD

            )

            result["requirements_analysis"].append({

                **req,

                "status": status,

                "evidence": evidence or NO_EVIDENCE,

                "semantic_similarity": similarity,

                "semantic_review": semantic_review,

            })


        matching_experience = data.get("matching_experience", [])

        concerns = data.get("concerns", [])

        result["matching_experience"] = (

            matching_experience if isinstance(matching_experience, list) else []

        )

        result["concerns"] = concerns if isinstance(concerns, list) else []


        mandatory = [

            item for item in result["requirements_analysis"]

            if item["type"] == "Must-Have"

        ]

        scored = mandatory or result["requirements_analysis"]

        points = {"Meets": 1.0, "Partially Meets": 0.5, "Does Not Meet": 0.0}

        result["match_score"] = round(

            100 * sum(points[item["status"]] for item in scored) / len(scored),

            2,

        )

        result["matched_skills"] = [

            item["requirement"]

            for item in result["requirements_analysis"]

            if item["type"] in {"Must-Have", "Preferred"}

            and item["status"] == "Meets"

        ]

        result["missing_skills"] = [

            item["requirement"] for item in mandatory

            if item["status"] != "Meets"

        ]


        similarities = [

            item["semantic_similarity"]

            for item in result["requirements_analysis"]

            if item["semantic_similarity"] is not None

        ]

        if similarities:

            result["semantic_similarity"] = round(

                sum(similarities) / len(similarities), 2

            )


        score = result["match_score"]

        result["recommendation"] = (

            "Strong Match" if score >= 85

            else "Good Match" if score >= 70

            else "Partial Match" if score >= 50

            else "Weak Match"

        )


        if result["missing_skills"]:

            result["concerns"].append(

                "Some Must-Have requirements lack fully verified evidence. "

                "HR should review the supporting CV sections."

            )

        if any(

            item["status"] == "Partially Meets"

            for item in result["requirements_analysis"]

        ):

            result["concerns"].append(

                "Partial matches require human review. Semantic similarity "

                "alone does not prove a qualification."

            )

        if any(

            item["semantic_review"]

            for item in result["requirements_analysis"]

        ):

            result["concerns"].append(

                "Some requirements have high semantic similarity but no "

                "traceable evidence. HR should review the CV."

            )


    except Exception as error:

        result["concerns"].append(

            f"Matching failed: {type(error).__name__}: {error}"

        )


    return result


def load_saved_results():

    """Load prior results from JSON."""

    if not RESULTS_FILE.exists():

        return []

    try:

        data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))

        if not isinstance(data, list):

            raise ValueError("Expected results.json to contain a JSON list.")

        return data

    except (OSError, json.JSONDecodeError, ValueError) as error:

        raise RuntimeError(f"Could not read saved results: {error}") from error


def save_results(results):

    """Atomically persist results to JSON."""

    temporary_file = RESULTS_FILE.with_suffix(".json.tmp")

    temporary_file.write_text(

        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"

    )

    temporary_file.replace(RESULTS_FILE)


def get_job_fingerprint(job_text):

    return hashlib.sha256(job_text.encode("utf-8")).hexdigest()


def load_job_by_id(job_id):

    """Find a saved job using its unique ID."""

    if not JOBS_FILE.is_file():

        raise FileNotFoundError(

            f"Jobs file not found: {JOBS_FILE}"

        )


    with JOBS_FILE.open("r", encoding="utf-8") as file:

        jobs = json.load(file)


    if not isinstance(jobs, list):

        raise ValueError("jobs.json must contain a JSON list.")


    for job in jobs:

        if isinstance(job, dict) and job.get("job_id") == job_id:

            return job


    raise ValueError(f"No job found with ID: {job_id}")


def main(job_id=None):

    if not ATTACHMENTS_DIR.is_dir():

        print(f"Attachments directory not found: {ATTACHMENTS_DIR}")

        return


    try:

        if job_id is not None:

            job = load_job_by_id(job_id)

            job_text = job["description"]

        else:

            if not JOB_FILE.is_file():

                print(f"Job description not found: {JOB_FILE}")

                return


            job_text = JOB_FILE.read_text(encoding="utf-8")

            job = parse_job_description(job_text)


        job_fingerprint = get_job_fingerprint(job_text)


    except Exception as error:

        print(f"Could not load job description: {error}")

        return


    try:
        previous_results = load_saved_results()
    except Exception as error:
        print(f"Could not load saved results: {error}")
        return

    files = sorted(
        path for path in ATTACHMENTS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        print("No PDF or DOCX CV files found in attachments.")
        return

    existing_by_email = {}
    for item in previous_results:
        if job_id is not None:
            same_job = (
                item.get("job_id") == job_id
                or (
                    not item.get("job_id")
                    and item.get("job_fingerprint") == job_fingerprint
                )
            )
        else:
            same_job = item.get("job_fingerprint") == job_fingerprint

        if not same_job:
            continue

        email = normalize_email(item.get("email", ""))
        if email:
            existing_by_email[email] = item

    results_by_email = {}
    results_without_email = []
    seen_file_hashes = set()


    for file in files:

        print(f"\nProcessing: {file.name}")

        try:

            file_hash = hashlib.sha256(file.read_bytes()).hexdigest()

            if file_hash in seen_file_hashes:

                print("Duplicate file content detected; skipping duplicate file.")

                continue

            seen_file_hashes.add(file_hash)


            cv_text = extract_text(file)

            if not cv_text or not cv_text.strip():

                print("No text extracted; skipping.")

                continue

            candidate = extract_candidate_info(cv_text)

            if not isinstance(candidate, dict):

                print("Invalid candidate data; skipping.")

                continue


            email = normalize_email(candidate.get("email", ""))

            if email and email in results_by_email:

                record = results_by_email[email]

                if file.name not in record["cv_files"]:

                    record["cv_files"].append(file.name)

                print("Duplicate candidate email; attached file to existing record.")

                continue


            if email and email in existing_by_email:

                saved = dict(existing_by_email[email])

                saved_files = saved.get("cv_files", [])

                if not isinstance(saved_files, list):

                    saved_files = []

                saved["cv_files"] = sorted(set(saved_files + [file.name]))

                saved["cv_file"] = saved["cv_files"][0]

                saved["email"] = email

                saved["job_fingerprint"] = job_fingerprint
                saved["job_id"] = job_id
                saved["job_title"] = job.get("job_title", "")

                results_by_email[email] = saved

                print("Candidate already screened for this job; reusing saved result.")

                continue


            result = calculate_match(candidate, job, cv_text=cv_text)

            result.update({

                "name": str(candidate.get("name", "")).strip(),

                "email": email,

                "cv_file": file.name,

                "cv_files": [file.name],
                "job_fingerprint": job_fingerprint,
                "job_id": job_id,
                "job_title": job.get("job_title", ""),
            })

            if email:

                results_by_email[email] = result

            else:

                result["concerns"].append(

                    "No email was extracted; duplicate identity could not be "

                    "reliably checked. HR should review this record."

                )

                results_without_email.append(result)


            print(json.dumps(result, indent=2, ensure_ascii=False))


        except Exception as error:

            print(f"Error processing {file.name}: {type(error).__name__}: {error}")

            continue


    print("\n" + "=" * 55)
    print("===== ALL CANDIDATES SUMMARY =====")
    print("=" * 55)


    results = list(results_by_email.values()) + results_without_email

    results.sort(key=lambda item: (

        item.get("match_score") is None,

        -(item.get("match_score") or 0),

        normalize_email(item.get("email", "")),

        item.get("name", "").casefold(),

    ))


    def belongs_to_current_job(item):
        if job_id is not None:
            return (
                item.get("job_id") == job_id
                or (
                    not item.get("job_id")
                    and item.get("job_fingerprint") == job_fingerprint
                )
            )
        return item.get("job_fingerprint") == job_fingerprint

    results_to_save = [
        item for item in previous_results
        if not belongs_to_current_job(item)
    ] + results

    try:
        save_results(results_to_save)

    except Exception as error:

        print(f"Could not save results to {RESULTS_FILE}: {error}")

        return


    print("\n===== CANDIDATES SUMMARY =====")

    for item in results:

        print(

            f"{item.get('name') or 'Unknown candidate'} | "

            f"{item.get('email') or 'No email'} | "

            f"CVs: {', '.join(item.get('cv_files', []))} | "

            f"Score: {item.get('match_score')} | "

            f"Recommendation: {item.get('recommendation')}"

        )

    print(
        f"\nSaved {len(results)} candidate record(s) for this job. "
        f"Total saved records across jobs: {len(results_to_save)} in {RESULTS_FILE}"
    )


if __name__ == "__main__":

    main()
