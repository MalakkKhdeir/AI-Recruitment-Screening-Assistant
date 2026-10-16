
from src.matcher import STATUSES, get_requirements, candidate_text


def test_requirement_categories():
    job = {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Docker"],
        "education": "Diploma"
    }

    assert get_requirements(job) == [
        {"requirement": "Python", "type": "Must-Have"},
        {"requirement": "SQL", "type": "Must-Have"},
        {"requirement": "Docker", "type": "Preferred"},
        {"requirement": "Diploma", "type": "Education"}
    ]


def test_candidate_text():
    candidate = {
        "skills": ["Python", "SQL"],
        "experience": ["Built a database application"],
        "projects": ["Student management system"],
        "education": "Diploma"
    }

    text = candidate_text(candidate)

    assert "Python" in text
    assert "Built a database application" in text
    assert "Student management system" in text
    assert "Diploma" in text


def test_matching_statuses_exist():
    assert STATUSES == {
        "Meets",
        "Partially Meets",
        "Does Not Meet"
    }
