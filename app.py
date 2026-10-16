import streamlit as st

import requests
import textwrap

# Normalize HTML passed to st.markdown.
# Streamlit treats HTML indented by four or more spaces as a code block.
_original_markdown = st.markdown
def _dedented_markdown(body, *args, **kwargs):
    if isinstance(body, str):
        if "<div" in body or "<style>" in body:
            body = "\n".join(line.lstrip() for line in body.splitlines()).strip()
        else:
            body = textwrap.dedent(body)
    return _original_markdown(body, *args, **kwargs)

st.markdown = _dedented_markdown

st.set_page_config(

    page_title="WIFQ | Recruitment Intelligence",

    page_icon="✦",

    layout="wide",

    initial_sidebar_state="expanded",

)

# WIFQ brand palette

NAVY = "#0D1B2A"

MIDNIGHT = "#1B263B"

STEEL_BLUE = "#415A77"

SAGE = "#778D7A"

BEIGE = "#D4C4A8"

CREAM = "#F4F1DE"

API_BASE_URL = "http://127.0.0.1:8000"

def fetch_api_data(endpoint):

    """Fetch JSON data from the FastAPI backend."""

    try:

        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)

        response.raise_for_status()

        data = response.json()

        return data if isinstance(data, dict) else {}

    except requests.RequestException as error:

        st.error(

            f"Could not connect to WIFQ API ({endpoint}). "

            f"Make sure FastAPI is running at {API_BASE_URL}. Details: {error}"

        )

        return {}

def as_list(value):

    return value if isinstance(value, list) else []

def candidate_name(candidate, index=0):

    return (

        candidate.get("candidate_name")

        or candidate.get("name")

        or candidate.get("full_name")

        or candidate.get("email")

        or f"Candidate {index + 1}"

    )

def is_must_have(item):

    req_type = str(item.get("type", "")).strip().lower().replace("_", "-")

    return req_type in {"must-have", "must have", "required", "mandatory"}


def is_unmet(item):

    status = str(item.get("status", "")).strip().lower().replace("_", " ")

    return status in {
        "does not meet", "not met", "missing", "unmet", "not satisfied",
        "not demonstrated", "insufficient evidence"
    }


def unmet_must_haves(candidate):

    return [
        item for item in as_list(candidate.get("requirements_analysis"))
        if isinstance(item, dict) and is_must_have(item) and is_unmet(item)
    ]


def has_unmet_must_have(candidate):

    return bool(unmet_must_haves(candidate))

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    :root {{
        --navy: {NAVY};
        --midnight: {MIDNIGHT};
        --steel: {STEEL_BLUE};
        --sage: {SAGE};
        --beige: {BEIGE};
        --cream: {CREAM};
        --ink: #142235;
        --muted: #52657A;
        --line: #E3DCCB;
        --white: #FFFFFF;
    }}

    html, body, [class*="css"], button, input, textarea, select {{
        font-family: 'DM Sans', sans-serif !important;
    }}
    .stApp {{ background: var(--cream); color: var(--ink); }}
    [data-testid="stHeader"] {{ background: rgba(244,241,222,.97); }}
    [data-testid="stToolbar"] {{ right: 1rem; }}
    [data-testid="stSidebar"] {{
        background: var(--navy);
        border-right: 1px solid rgba(212,196,168,.25);
    }}
    [data-testid="stSidebar"] * {{ color: var(--cream); }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {{
        color: var(--cream) !important; font-weight: 500;
    }}
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{ color: var(--beige) !important; }}

    .brand {{ display:flex; align-items:center; gap:12px; padding:8px 4px 24px; }}
    .brand-mark {{
        display:flex; align-items:center; justify-content:center;
        width:46px; height:46px; border-radius:14px;
        background:var(--midnight); color:var(--beige); font-size:28px;
        border:1px solid rgba(212,196,168,.18);
    }}
    .brand-name {{ color:var(--cream); font-size:24px; font-weight:700; letter-spacing:2px; line-height:1.2; }}
    .brand-caption {{ color:#C3CED8; font-size:10px; letter-spacing:1.5px; margin-top:4px; }}

    .eyebrow {{ color:var(--steel); font-size:11px; font-weight:700; letter-spacing:2px; text-transform:uppercase; }}
    .page-title {{ color:var(--navy); font-size:36px; font-weight:700; letter-spacing:-1.1px; margin:4px 0 6px; }}
    .page-subtitle {{ color:var(--muted); font-size:15px; margin-bottom:26px; }}
    h1, h2, h3, h4, h5, h6 {{ color:var(--navy) !important; letter-spacing:-.25px; }}
    p, li, .stMarkdown, .stText, [data-testid="stCaptionContainer"] {{ color:var(--ink); }}
    [data-testid="stCaptionContainer"] p {{ color:var(--muted) !important; }}

    .metric-card {{
        background:var(--white); border:1px solid var(--line); border-radius:16px;
        padding:22px; min-height:132px; box-shadow:0 3px 12px rgba(13,27,42,.035);
    }}
    .metric-label {{ color:var(--muted); font-size:13px; font-weight:600; }}
    .metric-value {{ color:var(--navy); font-size:34px; font-weight:700; margin-top:11px; line-height:1.1; }}
    .metric-note {{ color:#607B6A; font-size:12px; margin-top:8px; }}
    .section-card {{ background:var(--white); border:1px solid var(--line); border-radius:16px; padding:24px; box-shadow:0 3px 12px rgba(13,27,42,.035); }}
    .section-title {{ color:var(--navy); font-size:19px; font-weight:700; margin-bottom:8px; }}
    .muted {{ color:var(--muted); font-size:14px; line-height:1.65; }}

    /* Labels and form text: dark, readable on the light page */
    .stApp label,
    .stApp [data-testid="stWidgetLabel"],
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stWidgetLabel"] label {{
        color:var(--ink) !important; opacity:1 !important; font-weight:600 !important;
    }}
    .stApp [data-testid="stTextArea"] label,
    .stApp [data-testid="stTextInput"] label,
    .stApp [data-testid="stSelectbox"] label {{ color:var(--ink) !important; }}

    /* Inputs / text areas */
    .stApp textarea,
    .stApp input,
    .stApp [data-baseweb="input"] input,
    .stApp [data-baseweb="textarea"] textarea {{
        background-color:#FFFFFF !important;
        color:#142235 !important;
        -webkit-text-fill-color:#142235 !important;
        caret-color:#142235 !important;
        border:1px solid #CFC5B0 !important;
        border-radius:10px !important;
        opacity:1 !important;
    }}
    .stApp textarea::placeholder,
    .stApp input::placeholder {{
        color:#68798B !important; -webkit-text-fill-color:#68798B !important; opacity:1 !important;
    }}
    .stApp textarea:focus,
    .stApp input:focus {{ border-color:#415A77 !important; box-shadow:0 0 0 2px rgba(65,90,119,.16) !important; }}

    /* Select boxes and dropdown options */
    .stApp [data-baseweb="select"] > div {{
        background:#FFFFFF !important; border-color:#CFC5B0 !important; border-radius:10px !important;
    }}
    .stApp [data-baseweb="select"] *,
    .stApp [role="option"],
    .stApp [role="listbox"] * {{ color:#142235 !important; }}

    /* Buttons including form submit: ensure text remains visible */
    .stApp [data-testid="stButton"] button,
    .stApp [data-testid="stFormSubmitButton"] button,
    .stApp div.stButton > button,
    .stApp button[kind="primary"] {{
        background:#0D1B2A !important;
        border:1px solid #0D1B2A !important;
        border-radius:10px !important;
        color:#FFFFFF !important;
        -webkit-text-fill-color:#FFFFFF !important;
        font-weight:600 !important;
        min-height:44px;
        transition:background .18s ease, border-color .18s ease, transform .18s ease;
        opacity:1 !important;
    }}
    .stApp [data-testid="stButton"] button *,
    .stApp [data-testid="stFormSubmitButton"] button *,
    .stApp div.stButton > button * {{ color:#FFFFFF !important; -webkit-text-fill-color:#FFFFFF !important; }}
    .stApp [data-testid="stButton"] button:hover,
    .stApp [data-testid="stFormSubmitButton"] button:hover,
    .stApp div.stButton > button:hover,
    .stApp button[kind="primary"]:hover {{
        background:#415A77 !important; border-color:#415A77 !important; color:#FFFFFF !important;
        -webkit-text-fill-color:#FFFFFF !important; transform:translateY(-1px);
    }}
    .stApp button:disabled {{ background:#D8DDE2 !important; border-color:#D8DDE2 !important; color:#536273 !important; -webkit-text-fill-color:#536273 !important; opacity:1 !important; }}

    /* Streamlit metrics, alerts, expanders and containers */
    div[data-testid="stMetric"] {{ background:#FFFFFF; border:1px solid var(--line); padding:18px; border-radius:14px; }}
    div[data-testid="stMetricLabel"], div[data-testid="stMetricLabel"] * {{ color:var(--muted) !important; }}
    div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {{ color:var(--navy) !important; }}
    div[data-testid="stAlert"] {{ border-radius:12px; }}
    [data-testid="stExpander"] {{ background:rgba(255,255,255,.72); border:1px solid var(--line); border-radius:12px; }}
    hr {{ border-color:var(--line); }}
    #MainMenu {{ visibility:hidden; }}
    footer {{ visibility:hidden; }}

    @media (max-width:768px) {{
        .page-title {{ font-size:28px; }}
        .metric-value {{ font-size:27px; }}
        .section-card {{ padding:18px; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar navigation

with st.sidebar:

    st.markdown(

        """

        <div class="brand">

            <div class="brand-mark">✦</div>

            <div>

                <div class="brand-name">WIFQ</div>

                <div class="brand-caption">RECRUITMENT INTELLIGENCE</div>

            </div>

        </div>

        """,

        unsafe_allow_html=True,

    )

    st.markdown("---")

    st.caption("WORKSPACE")

    pages = ["Overview", "Jobs & Requirements", "Candidates", "Review Pipeline"]

    if "requested_page" in st.session_state:

        requested_page = st.session_state.pop("requested_page")

        if requested_page in pages:

            st.session_state["page_navigation"] = requested_page

    page = st.radio(

        "Navigation",

        pages,

        key="page_navigation",

        label_visibility="collapsed",

    )

    st.markdown("---")

    st.markdown(

        """

        <div style="color:#B8C4D0;font-size:12px;line-height:1.8;">

            AI-assisted screening<br>Human-led decisions

        </div>

        """,

        unsafe_allow_html=True,

    )

# Load live data from FastAPI

jobs_response = fetch_api_data("/jobs")

candidates_response = fetch_api_data("/candidates")

jobs = as_list(jobs_response.get("jobs"))

candidates = as_list(candidates_response.get("candidates"))

page_copy = {

    "Overview": ("Overview", "A clearer, evidence-based view of your recruitment pipeline."),

    "Jobs & Requirements": (

        "Jobs & Requirements",

        "Review job descriptions and the requirements extracted for each role.",

    ),

    "Candidates": (

        "Candidates",

        "Compare match results and inspect the evidence behind each requirement.",

    ),

    "Review Pipeline": (

        "Review Pipeline",

        "Focus on records that need closer human review.",

    ),

}

title, subtitle = page_copy[page]

st.markdown('<div class="eyebrow">RECRUITMENT WORKSPACE</div>', unsafe_allow_html=True)

st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)

st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

if page == "Overview":

    strong_matches = sum(

        1 for c in candidates

        if isinstance(c.get("match_score"), (int, float))
        and c["match_score"] >= 80 and not has_unmet_must_have(c)

    )

    awaiting_review = sum(1 for c in candidates if has_unmet_must_have(c))

    metrics = [

        ("Active Jobs", len(jobs), "Jobs in your workspace"),

        ("Candidate Records", len(candidates), "Records returned by the API"),

        ("Strong Matches", strong_matches, "Score of 80% or higher"),

        ("Awaiting Review", awaiting_review, "Unmet Must-Have evidence"),

    ]

    columns = st.columns(4)

    for column, (label, value, note) in zip(columns, metrics):

        with column:

            st.markdown(

                f"""

                <div class="metric-card">

                    <div class="metric-label">{label}</div>

                    <div class="metric-value">{value}</div>

                    <div class="metric-note">{note}</div>

                </div>

                """,

                unsafe_allow_html=True,

            )

    st.write("")

    left, right = st.columns([1.5, 1])

    with left:

        st.markdown(

            """

            <div class="section-card">

                <div class="section-title">Your hiring workspace</div>

                <div class="muted">

                    Start with a job description, review extracted requirements,

                    and screen candidates against the role.

                </div>

            </div>

            """,

            unsafe_allow_html=True,

        )

        st.write("")

        if st.button("＋  Create a new job", use_container_width=True):

            st.session_state["requested_page"] = "Jobs & Requirements"

            st.rerun()

        st.write("")

        st.markdown("#### Active job openings")

        if jobs:

            for job in jobs:

                with st.container(border=True):

                    st.markdown(f"**{job.get('job_title', 'Untitled Job')}**")

                    st.caption(f"Job ID: {job.get('job_id', 'Not available')}")

                    st.write(job.get("description", "No description available.")[:280])

        else:

            st.info("No jobs were returned by the API.")

    with right:

        st.markdown(

            """

            <div class="section-card">

                <div class="section-title">How WIFQ works</div>

                <div class="muted">

                    <b>01</b> &nbsp; Define the role<br><br>

                    <b>02</b> &nbsp; Analyze CVs<br><br>

                    <b>03</b> &nbsp; Review evidence<br><br>

                    <b>04</b> &nbsp; Make an informed decision

                </div>

            </div>

            """,

            unsafe_allow_html=True,

        )

elif page == "Jobs & Requirements":

    st.markdown("### Create a job")

    st.write(

        "Paste the job description below. WIFQ will extract the role details "

        "and requirements so HR can review them before saving."

    )

    if "job_description_input" not in st.session_state:

        st.session_state["job_description_input"] = ""

    if "parsed_job_draft" not in st.session_state:

        st.session_state["parsed_job_draft"] = None

    with st.form("job_description_form"):

        description = st.text_area(

            "Job description",

            key="job_description_input",

            height=220,

            placeholder=(

                "Paste the complete job description here, including "

                "responsibilities, required skills, preferred skills, and education."

            ),

        )

        analyze_clicked = st.form_submit_button(

            "Analyze Job Description",

            use_container_width=True,

        )

    if analyze_clicked:

        if not description.strip():

            st.warning("Please enter a job description first.")

        else:

            try:

                with st.spinner("Analyzing the job description..."):

                    response = requests.post(

                        f"{API_BASE_URL}/jobs/parse",

                        json={"description": description.strip()},

                        timeout=120,

                    )

                    response.raise_for_status()

                    parsed = response.json()

                # Some API implementations wrap parsed fields in a "job" object.

                if isinstance(parsed, dict) and isinstance(parsed.get("job"), dict):

                    parsed = parsed["job"]

                if not isinstance(parsed, dict):

                    st.error("The API returned an unexpected response format.")

                    st.json(parsed)

                else:

                    st.session_state["parsed_job_draft"] = {

                        **parsed,

                        "description": description.strip(),

                    }

                    st.success("Analysis completed. Review the extracted details below.")

                    st.rerun()

            except requests.HTTPError as error:

                details = ""

                try:

                    details = response.text

                except Exception:

                    pass

                st.error(f"Job analysis failed: {error}")

                if details:

                    st.code(details)

            except requests.RequestException as error:

                st.error(

                    "Could not reach the job parser. Check that FastAPI is running. "

                    f"Details: {error}"

                )

            except ValueError as error:

                st.error(f"The API response was not valid JSON: {error}")

    draft = st.session_state.get("parsed_job_draft")

    if isinstance(draft, dict):

        st.divider()

        st.markdown("### Review extracted requirements")

        st.caption(

            "Review and edit the AI-extracted fields before saving. "

            "Do not treat extracted requirements as final until HR has checked them."

        )

        job_title = st.text_input(

            "Job title",

            value=str(draft.get("job_title") or ""),

            key="draft_job_title",

        )

        education = st.text_input(

            "Education",

            value=str(draft.get("education") or ""),

            key="draft_education",

        )

        experience = st.text_input(

            "Experience",

            value=str(draft.get("experience") or ""),

            key="draft_experience",

        )

        required_defaults = as_list(draft.get("required_skills"))

        preferred_defaults = as_list(draft.get("preferred_skills"))

        responsibilities_defaults = as_list(draft.get("responsibilities"))

        st.markdown("#### Must-Have requirements")

        required_text = st.text_area(

            "One requirement per line",

            value="\n".join(str(item) for item in required_defaults),

            key="draft_required_skills",

            height=140,

            help="These are treated as mandatory requirements during screening.",

        )

        st.markdown("#### Preferred requirements")

        preferred_text = st.text_area(

            "One preferred requirement per line",

            value="\n".join(str(item) for item in preferred_defaults),

            key="draft_preferred_skills",

            height=120,

            help="These are desirable but not mandatory.",

        )

        st.markdown("#### Responsibilities")

        responsibilities_text = st.text_area(

            "One responsibility per line",

            value="\n".join(str(item) for item in responsibilities_defaults),

            key="draft_responsibilities",

            height=120,

        )

        edited_description = st.text_area(

            "Original job description",

            value=str(draft.get("description") or ""),

            key="draft_description_review",

            height=160,

        )

        if st.button("Save Job", type="primary", use_container_width=True):

            cleaned_required = [

                line.strip() for line in required_text.splitlines() if line.strip()

            ]

            cleaned_preferred = [

                line.strip() for line in preferred_text.splitlines() if line.strip()

            ]

            cleaned_responsibilities = [

                line.strip()

                for line in responsibilities_text.splitlines()

                if line.strip()

            ]

            if not job_title.strip():

                st.warning("Please provide a job title before saving.")

            elif not edited_description.strip():

                st.warning("The job description cannot be empty.")

            else:

                job_payload = {

                    "job_title": job_title.strip(),

                    "description": edited_description.strip(),

                    "required_skills": cleaned_required,

                    "preferred_skills": cleaned_preferred,

                    "education": education.strip(),

                    "experience": experience.strip(),

                    "responsibilities": cleaned_responsibilities,

                }

                try:

                    with st.spinner("Saving job..."):

                        save_response = requests.post(

                            f"{API_BASE_URL}/jobs",

                            json=job_payload,

                            timeout=30,

                        )

                        save_response.raise_for_status()

                        saved_result = save_response.json()

                    st.session_state["parsed_job_draft"] = None

                    st.success("Job saved successfully.")

                    if isinstance(saved_result, dict):

                        st.json(saved_result)

                    st.rerun()

                except requests.HTTPError as error:

                    st.error(f"The API could not save this job: {error}")

                    try:

                        st.code(save_response.text)

                    except Exception:

                        pass

                    st.info(

                        "The save request may use a different schema. "

                        "If this happens, send me the POST /jobs Request body schema "

                        "from /docs and I will align the payload with it."

                    )

                except requests.RequestException as error:

                    st.error(f"Could not reach the save endpoint: {error}")

                except ValueError:

                    st.success("Job saved, but the API did not return JSON.")

    st.divider()

    st.markdown("### Saved jobs")

    if jobs:

        selected_job_index = st.selectbox(

            "Select a saved job",

            options=range(len(jobs)),

            format_func=lambda i: jobs[i].get("job_title", "Untitled Job"),

            key="saved_job_selector",

        )

        job = jobs[selected_job_index]

        st.markdown(f"#### {job.get('job_title', 'Job details')}")

        st.write(job.get("description", "No job description available."))

        left, right = st.columns(2)

        with left:

            st.markdown("##### Must-Have requirements")

            required = as_list(job.get("required_skills"))

            if required:

                for item in required:

                    st.write(f"• {item}")

            else:

                st.info("No Must-Have requirements were returned.")

        with right:

            st.markdown("##### Preferred requirements")

            preferred = as_list(job.get("preferred_skills"))

            if preferred:

                for item in preferred:

                    st.write(f"• {item}")

            else:

                st.info("No Preferred requirements were returned.")

        st.caption(f"Job ID: {job.get('job_id', 'Not available')}")

    else:

        st.info("No saved jobs are currently returned by the API.")

elif page == "Candidates":

    if not candidates:

        st.info("No candidate records were returned by the API.")

    else:

        labels = [str(candidate_name(c, i)) for i, c in enumerate(candidates)]

        selected_index = st.selectbox(

            "Select a candidate",

            options=range(len(candidates)),

            format_func=lambda i: labels[i],

        )

        candidate = candidates[selected_index]

        score = candidate.get("match_score")

        similarity = candidate.get("semantic_similarity")

        recommendation = candidate.get("recommendation", "Not available")

        c1, c2, c3 = st.columns(3)

        c1.metric("Match Score", f"{score:.2f}%" if isinstance(score, (int, float)) else "N/A")

        c2.metric(

            "Semantic Similarity",

            f"{similarity:.2f}%" if isinstance(similarity, (int, float)) else "N/A",

        )

        c3.metric("Recommendation", recommendation)

        analyses = [
            item for item in as_list(candidate.get("requirements_analysis"))
            if isinstance(item, dict)
        ]
        unmet_items = unmet_must_haves(candidate)
        if unmet_items:
            st.warning(
                f"{len(unmet_items)} Must-Have requirement(s) are not marked as met. "
                "HR review is needed regardless of the overall score."
            )
            for item in unmet_items:
                st.write(f"• {item.get('requirement', 'Unnamed requirement')}")
        elif any(is_must_have(item) for item in analyses):
            st.success("No explicitly unmet Must-Have requirements were found.")
        else:
            st.info("Must-Have status could not be verified from this analysis.")

        st.markdown("### Matched skills")

        matched = as_list(candidate.get("matched_skills"))

        st.write(", ".join(matched) if matched else "No matched skills listed.")

        st.markdown("### Missing skills")

        missing = as_list(candidate.get("missing_skills"))

        st.write(", ".join(missing) if missing else "No missing skills listed.")

        st.markdown("### Requirement-by-requirement analysis")

        if analyses:

            for item in analyses:

                if not isinstance(item, dict):

                    continue

                requirement = item.get("requirement", "Unnamed requirement")

                req_type = item.get("type", "Unspecified")

                status = item.get("status", "Unknown")

                evidence = item.get("evidence", "No evidence provided.")

                with st.expander(f"{requirement} — {status} ({req_type})"):

                    st.write(f"**Status:** {status}")

                    st.write(f"**Type:** {req_type}")

                    st.write(f"**Evidence:** {evidence}")

                    req_similarity = item.get("semantic_similarity")

                    if isinstance(req_similarity, (int, float)):

                        st.caption(f"Semantic similarity: {req_similarity:.2f}%")

                    if item.get("semantic_review"):

                        st.warning("This requirement has been flagged for manual review.")

        else:

            st.info("Detailed requirement analysis is not available for this record.")

        concerns = as_list(candidate.get("concerns"))

        if concerns:

            st.markdown("### Review notes")

            for concern in concerns:

                st.warning(concern)

        st.caption(

            "Scores support HR review. Missing evidence does not necessarily mean "

            "the candidate lacks the skill."

        )


elif page == "Review Pipeline":

    # Keep the confirmation visible after Streamlit reruns the page.
    if st.session_state.get("review_save_message"):
        st.success(st.session_state["review_save_message"])

    review_candidates = [
        c for c in candidates
        if has_unmet_must_have(c) and c.get("job_id")
    ]

    st.write(
        f"**{len(review_candidates)} candidate record(s) need closer review.**"
    )

    if not review_candidates:
        st.success("No records with unmet Must-Have requirements were found.")

    else:
        for index, candidate in enumerate(review_candidates):
            name = candidate_name(candidate, index)
            job_id = candidate.get("job_id")
            email = candidate.get("email")
            current_status = candidate.get("hr_review_status", "Review Later")

            candidate_key = str(job_id) + "_" + str(email or name)

            with st.expander(str(name)):
                score = candidate.get("match_score")
                score_text = (
                    f"{score:.2f}%"
                    if isinstance(score, (int, float))
                    else "N/A"
                )
                st.write(f"**Match score:** {score_text}")

                for item in as_list(candidate.get("requirements_analysis")):
                    if not isinstance(item, dict):
                        continue
                    if is_must_have(item) and is_unmet(item):
                        st.warning(
                            f"{item.get('requirement', 'Requirement')}: "
                            f"{item.get('status', 'Unknown')}"
                        )
                        st.caption(
                            item.get("evidence", "No evidence provided.")
                        )

                if not email and not name:
                    st.warning("This record has no candidate email or name.")
                    continue

                st.write("**HR review decision**")
                status_options = ["Review Later", "Shortlist", "Reject"]

                selected_status = st.selectbox(
                    "Choose status",
                    options=status_options,
                    index=(
                        status_options.index(current_status)
                        if current_status in status_options
                        else 0
                    ),
                    key=f"review_status_{candidate_key}",
                )

                if st.button(
                    "Save HR decision",
                    key=f"save_review_{candidate_key}",
                    type="primary",
                ):
                    try:
                        payload = {
                            "job_id": job_id,
                            "candidate_email": email,
                            "candidate_name": name if not email else None,
                            "status": selected_status,
                        }
                        response = requests.post(
                            f"{API_BASE_URL}/candidates/review",
                            json=payload,
                            timeout=15,
                        )

                        if response.ok:
                            st.session_state["review_save_message"] = (
                                f"Saved decision: {selected_status}"
                            )
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            try:
                                detail = response.json().get(
                                    "detail", response.text
                                )
                            except ValueError:
                                detail = response.text
                            st.error(
                                f"Could not save decision "
                                f"({response.status_code}): {detail}"
                            )
                    except requests.RequestException as error:
                        st.error(
                            f"Could not connect to the API: {error}"
                        )
st.write("")

st.caption(

    "WIFQ supports human review. Match scores are decision-support signals, "

    "not automated hiring decisions."

)
