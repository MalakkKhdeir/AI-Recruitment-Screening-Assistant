
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_FILE = BASE_DIR / "results.json"


def is_qualified(candidate):
    """Check whether the candidate meets every Must-Have requirement."""
    analysis = candidate.get("requirements_analysis", [])

    must_have = [
        item for item in analysis
        if item.get("type") == "Must-Have"
    ]

    # Qualification cannot be established without Must-Have requirements.
    if not must_have:
        return False

    return all(
        item.get("status") == "Meets"
        and isinstance(item.get("evidence"), str)
        and item.get("evidence").strip()
        and item.get("evidence").strip()
        != "No evidence found in the provided candidate information."
        for item in must_have
    )


def rank_candidates(candidates, top_n=20):
    """Classify candidates and rank qualified candidates by match score."""
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n < 1:
        raise ValueError("top_n must be a positive integer.")

    qualified = []
    needs_review = []

    for candidate in candidates:
        if is_qualified(candidate):
            candidate["screening_status"] = "Qualified"
            qualified.append(candidate)
        else:
            candidate["screening_status"] = "Needs HR Review"
            needs_review.append(candidate)

        # Keep an existing HR decision; otherwise initialize it.
        candidate.setdefault("hr_decision", "Pending")

    qualified.sort(
        key=lambda candidate: (
            candidate.get("match_score")
            if isinstance(candidate.get("match_score"), (int, float))
            and not isinstance(candidate.get("match_score"), bool)
            else -1
        ),
        reverse=True,
    )

    return {
        "qualified_candidates": qualified[:top_n],
        "needs_hr_review": needs_review,
        "shortlist_limit": top_n,
        "qualified_count": len(qualified),
        "needs_review_count": len(needs_review),
    }


def main():
    if not RESULTS_FILE.is_file():
        print(f"Results file not found: {RESULTS_FILE}")
        return

    try:
        with RESULTS_FILE.open("r", encoding="utf-8") as file:
            candidates = json.load(file)

        if not isinstance(candidates, list):
            raise ValueError("results.json must contain a JSON list.")

        results = rank_candidates(candidates, top_n=20)

        # Save to a temporary file first, then replace results.json.
        # This reduces the risk of leaving a partially written JSON file.
        temporary_file = RESULTS_FILE.with_suffix(".tmp")
        try:
            with temporary_file.open("w", encoding="utf-8") as file:
                json.dump(candidates, file, indent=2, ensure_ascii=False)
                file.write("\n")

            temporary_file.replace(RESULTS_FILE)
        except OSError:
            if temporary_file.exists():
                temporary_file.unlink()
            raise

    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Could not rank candidates: {error}")
        return

    print("\n===== QUALIFIED CANDIDATES =====")
    print(f"Total qualified: {results['qualified_count']}")

    for position, candidate in enumerate(
        results["qualified_candidates"], start=1
    ):
        print(
            f"{position}. {candidate.get('name', 'Unknown')} | "
            f"Score: {candidate.get('match_score')} | "
            f"HR decision: {candidate.get('hr_decision')}"
        )

    print("\n===== NEEDS HR REVIEW =====")
    print(f"Total candidates needing review: {results['needs_review_count']}")

    for candidate in results["needs_hr_review"]:
        print(
            f"{candidate.get('name', 'Unknown')} | "
            f"Score: {candidate.get('match_score')} | "
            f"HR decision: {candidate.get('hr_decision')}"
        )

    print(f"\nShortlist limit: {results['shortlist_limit']}")
    print(f"Saved screening statuses to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()
