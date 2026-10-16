from src.matcher import main as run_screening
import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.job_parser import parse_job_description


BASE_DIR = Path(__file__).resolve().parent.parent

RESULTS_FILE = BASE_DIR / "results.json"
JOBS_FILE = BASE_DIR / "jobs.json"


app = FastAPI(
    title="AI Recruitment Screening Assistant",
    description="API for retrieving AI-assisted candidate screening results.",
    version="1.0.0",
)


# =========================
# Job storage functions
# =========================

def load_jobs():
    """Load saved jobs from jobs.json."""

    if not JOBS_FILE.exists():
        return []

    try:
        with JOBS_FILE.open("r", encoding="utf-8") as file:
            jobs = json.load(file)

    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=500,
            detail="The saved jobs file contains invalid JSON.",
        ) from error

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not read saved jobs.",
        ) from error

    if not isinstance(jobs, list):
        raise HTTPException(
            status_code=500,
            detail="The saved jobs file must contain a JSON list.",
        )

    return jobs


def save_jobs(jobs):
    """Save jobs to jobs.json."""

    try:
        with JOBS_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                jobs,
                file,
                indent=2,
                ensure_ascii=False,
            )
            file.write("\n")

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not save jobs.",
        ) from error


# =========================
# Request validation
# =========================

class JobDescriptionRequest(BaseModel):
    description: str = Field(
        min_length=1,
        max_length=20000,
        description="The full job description to analyze.",
    )


# =========================
# General endpoints
# =========================

@app.get("/")
def home():
    """Return basic API information."""

    return {
        "message": "AI Recruitment Screening Assistant API is running.",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    """Check whether the API is running."""

    return {"status": "ok"}


@app.post("/jobs/{job_id}/screen")
def screen_job(job_id: str):
    try:
        from src.matcher import load_job_by_id, main as run_screening

        load_job_by_id(job_id)
        run_screening(job_id=job_id)

        candidates = json.loads(
            RESULTS_FILE.read_text(encoding="utf-8")
        ) if RESULTS_FILE.exists() else []

        job_candidates = [
            candidate for candidate in candidates
            if candidate.get("job_id") == job_id
        ]

        return {
            "message": "Screening completed.",
            "job_id": job_id,
            "count": len(job_candidates),
            "candidates": job_candidates,
        }

    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Screening failed: {error}",
        )



@app.get("/candidates")
def get_candidates():
    """Return all saved candidate records."""

    if not RESULTS_FILE.is_file():
        raise HTTPException(
            status_code=404,
            detail="Candidate results file was not found.",
        )

    try:
        with RESULTS_FILE.open("r", encoding="utf-8") as file:
            candidates = json.load(file)

    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=500,
            detail="Candidate results contain invalid JSON.",
        ) from error

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not read candidate results.",
        ) from error

    if not isinstance(candidates, list):
        raise HTTPException(
            status_code=500,
            detail="Candidate results must be a JSON list.",
        )

    return {
        "count": len(candidates),
        "candidates": candidates,
    }


# =========================
# Job endpoints
# =========================

@app.get("/jobs")
def get_jobs():
    """Return all saved job descriptions."""

    jobs = load_jobs()

    return {
        "count": len(jobs),
        "jobs": jobs,
    }


@app.post("/jobs/parse")
def parse_job_endpoint(request: JobDescriptionRequest):
    """Extract structured requirements from a job description."""

    try:
        job = parse_job_description(request.description)

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        # Avoid exposing API keys or internal provider details.
        print(
            f"Job parsing failed: {type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail="Could not analyze the job description.",
        ) from error

    return {
        "message": "Job description analyzed successfully.",
        "job": job,
    }


@app.post("/jobs")
def create_job(request: JobDescriptionRequest):
    """Analyze and save a new job description."""

    try:
        job = parse_job_description(request.description)

        jobs = load_jobs()

        new_job = {
            "job_id": str(uuid4()),
            "description": request.description.strip(),
            **job,
        }

        jobs.append(new_job)
        save_jobs(jobs)

        return {
            "message": "Job created successfully.",
            "job": new_job,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        print(
            f"Job creation failed: {type(error).__name__}: {error}"
        )

        raise HTTPException(
            status_code=502,
            detail="Could not create the job.",
        ) from error


# =========================
# HR candidate review decisions
# =========================

class CandidateReviewRequest(BaseModel):
    job_id: str = Field(min_length=1)
    candidate_email: str | None = None
    candidate_name: str | None = None
    status: str = Field(min_length=1)


@app.post("/candidates/review")
def save_candidate_review(request: CandidateReviewRequest):
    """Save an HR review decision for a candidate and a specific job."""

    allowed_statuses = {"Shortlist", "Review Later", "Reject"}

    if request.status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail="Status must be Shortlist, Review Later, or Reject.",
        )

    if not request.candidate_email and not request.candidate_name:
        raise HTTPException(
            status_code=422,
            detail="Provide a candidate email or name.",
        )

    if not RESULTS_FILE.is_file():
        raise HTTPException(
            status_code=404,
            detail="Candidate results file was not found.",
        )

    try:
        with RESULTS_FILE.open("r", encoding="utf-8") as file:
            candidates = json.load(file)

    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=500,
            detail="Candidate results contain invalid JSON.",
        ) from error

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not read candidate results.",
        ) from error

    if not isinstance(candidates, list):
        raise HTTPException(
            status_code=500,
            detail="Candidate results must be a JSON list.",
        )

    matching_candidates = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict)
        and candidate.get("job_id") == request.job_id
        and (
            (
                request.candidate_email
                and str(candidate.get("email", "")).strip().casefold()
                == request.candidate_email.strip().casefold()
            )
            or (
                request.candidate_name
                and str(candidate.get("name", "")).strip().casefold()
                == request.candidate_name.strip().casefold()
            )
        )
    ]

    if not matching_candidates:
        raise HTTPException(
            status_code=404,
            detail="Candidate was not found for this job.",
        )

    if len(matching_candidates) > 1:
        raise HTTPException(
            status_code=409,
            detail="More than one record matched. Use the candidate email.",
        )

    candidate = matching_candidates[0]
    candidate["hr_review_status"] = request.status

    try:
        with RESULTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                candidates,
                file,
                indent=2,
                ensure_ascii=False,
            )
            file.write("\n")

    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail="Could not save the HR review decision.",
        ) from error

    return {
        "message": "HR review decision saved successfully.",
        "job_id": request.job_id,
        "candidate_name": candidate.get("name"),
        "hr_review_status": candidate["hr_review_status"],
    }
