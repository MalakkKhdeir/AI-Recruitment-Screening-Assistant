from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def calculate_semantic_similarity(requirement, candidate_info):
    requirement_embedding = model.encode([requirement])
    candidate_embedding = model.encode([candidate_info])

    similarity = cosine_similarity(
        requirement_embedding,
        candidate_embedding
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
        candidate_information
    )

    print("\n===== SEMANTIC MATCHING TEST =====")
    print(f"Job Requirement: {job_requirement}")
    print(f"Candidate Information: {candidate_information.strip()}")
    print(f"\nCosine Similarity: {similarity:.4f}")