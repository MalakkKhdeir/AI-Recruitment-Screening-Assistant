# WIFQ — AI Recruitment Screening Assistant

WIFQ is an AI-assisted recruitment screening system designed to help HR teams organize job requirements, analyze candidate CVs, and compare candidate qualifications against job requirements.

The system provides evidence-based screening results to support human review. It does not make final hiring decisions automatically.

## Features

- Job description analysis and structured requirement extraction using an LLM.
- CV text extraction from PDF and DOCX files.
- Candidate screening against job requirements.
- Semantic similarity analysis.
- Requirement-by-requirement matching with evidence and missing requirements.
- Candidate match scores and recommendations.
- Gmail integration for collecting recruitment emails and attachments.
- FastAPI backend for job and candidate operations.
- Streamlit web interface for reviewing jobs, candidates, and HR decisions.
- HR review statuses: Shortlist, Review Later, and Reject.
- JSON-based storage for job descriptions and screening results.

## Technology Stack

- Python
- FastAPI
- Streamlit
- Pydantic
- OpenRouter API
- Sentence Transformers
- PyPDF
- python-docx
- Gmail API

## Project Structure

```text
Sahaba1/
├── src/
│   ├── api.py
│   ├── candidate_extractor.py
│   ├── cv_parser.py
│   ├── gmail_auth.py
│   ├── gmail_reader.py
│   ├── job_parser.py
│   ├── main.py
│   ├── matcher.py
│   └── semantic_matcher.py
├── attachments/
├── app.py
├── jobs.json
├── results.json
├── job_description.txt
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

The exact files may vary depending on the current project version.

## Requirements

- Python 3.10 or a compatible version supported by the installed dependencies.
- pip
- An OpenRouter API key for LLM-powered extraction.
- Gmail API credentials if Gmail integration is enabled.

## Installation

Clone the repository and open its directory:

```bash
git clone YOUR_REPOSITORY_URL
cd Sahaba1
```

Create and activate a virtual environment.

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If a required package is missing, install it in the activated environment.

## Configuration

Create a `.env` file in the project root and configure the required environment variables.

Example:

```env
OPENROUTER_API_KEY=your_api_key_here
```

Use your own API key. Never commit API keys, OAuth credentials, or access tokens to version control.

Gmail integration may also require OAuth client credentials and a generated token file. Follow the project's Gmail authentication setup.

## Running the Application

Start the FastAPI backend from the project root:

```bash
python -m uvicorn src.api:app --reload
```

The API will be available at:

- API root: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

Open a second terminal, activate the virtual environment, and start the Streamlit interface:

```bash
streamlit run app.py
```

Keep both terminals running while using the application.

## Workflow

1. Enter a job description.
2. Analyze and review the extracted requirements.
3. Save the job.
4. Screen candidate CVs against the selected job.
5. Review match scores, requirement statuses, and supporting evidence.
6. Save an HR review decision for a candidate.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/jobs` | Retrieve saved jobs |
| POST | `/jobs/parse` | Analyze a job description |
| POST | `/jobs` | Create a job |
| POST | `/jobs/{job_id}/screen` | Screen candidates for a job |
| GET | `/candidates` | Retrieve candidate records |
| POST | `/candidates/review` | Save an HR review decision |

## Data Storage

The current application uses JSON files for local persistence:

- `jobs.json`: saved job descriptions and extracted requirements.
- `results.json`: candidate screening results and HR review statuses.

Protect candidate information and do not upload real personal data to a public repository.

## Responsible Use

WIFQ is designed to assist HR professionals, not replace them. Match scores and semantic similarity are supporting signals and should not be treated as definitive measures of a candidate's suitability.

HR professionals should review the available evidence, consider missing information carefully, and make hiring decisions themselves.

## Security

- Keep `.env` out of Git.
- Never commit API keys, Gmail OAuth client secrets, or token files.
- Exclude private CVs and candidate data from public repositories.
- Use anonymized or synthetic candidate records for demonstrations.

## Current Limitations

- Screening quality depends on CV extraction quality and the information provided.
- Missing evidence does not necessarily mean a candidate lacks a skill.
- Results and HR decisions are stored locally in JSON files.
- Gmail functionality depends on valid credentials and configuration.
- The application requires the backend and frontend to be running simultaneously.
