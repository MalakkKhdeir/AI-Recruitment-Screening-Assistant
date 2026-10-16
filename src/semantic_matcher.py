
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    """Load the embedding model once and reuse it."""
    return SentenceTransformer(MODEL_NAME)


def calculate_semantic_similarity(requirement, candidate_info):
    """
    Return cosine similarity between a job requirement
    and candidate information, as a float.
    """
    if not isinstance(requirement, str) or not requirement.strip():
        raise ValueError("Requirement text cannot be empty.")

    if not isinstance(candidate_info, str) or not candidate_info.strip():
        raise ValueError("Candidate information cannot be empty.")

    model = get_model()

    embeddings = model.encode(
        [requirement.strip(), candidate_info.strip()],
        normalize_embeddings=True,
    )

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]],
    )[0][0]

    return float(similarity)


if __name__ == "__main__":
    job_requirement = "Technical project management experience"

    candidate_information = """
    Managed technical projects and coordinated teams
    during software and AI projects.
    """

    similarity = calculate_semantic_similarity(
        job_requirement,
        candidate_information,
    )

    print("\n===== SEMANTIC MATCHING TEST =====")
    print(f"Job Requirement: {job_requirement}")
    print(f"Candidate Information: {candidate_information.strip()}")
    print(f"Cosine Similarity: {similarity:.4f}")
