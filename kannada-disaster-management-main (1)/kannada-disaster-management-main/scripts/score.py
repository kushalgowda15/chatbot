import json

INPUT_FILE = "dataset/processed/categorized_dataset.jsonl"
OUTPUT_FILE = "dataset/clean_disaster_dataset.jsonl"

final_data = []

def quality_score(question, answer):

    score = 0

    # Good question length
    if 10 <= len(question) <= 120:
        score += 2

    # Good answer length
    if 20 <= len(answer) <= 250:
        score += 3

    # Actionable keywords
    good_words = [
        "ಕರೆ ಮಾಡಿ",
        "ಸುರಕ್ಷಿತ",
        "ತಕ್ಷಣ",
        "ದೂರವಿರಿ",
        "ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ",
        "ಆಫ್ ಮಾಡಿ",
        "ಸಹಾಯ",
        "ಎಚ್ಚರಿಕೆ"
    ]

    for word in good_words:
        if word in answer:
            score += 1

    # Penalize repetitive synthetic content
    bad_words = [
        "ಈ ಮಾಹಿತಿ ತಿಳಿದಿರಬೇಕು",
        "ಈ ಕ್ರಮಗಳು",
        "ಈ ಸಿದ್ಧತೆ",
        "ಅಪಾಯ ಹೆಚ್ಚು"
    ]

    for word in bad_words:
        if word in answer:
            score -= 3

    return score


print("Scoring dataset quality...\n")

with open(INPUT_FILE, "r", encoding="utf-8") as f:

    for line in f:

        try:
            data = json.loads(line)

            question = data["question"]
            answer = data["answer"]
            category = data["category"]

            score = quality_score(question, answer)

            # Keep only strong entries
            if score >= 4:

                final_data.append({
                    "category": category,
                    "question": question,
                    "answer": answer,
                    "quality_score": score
                })

        except Exception:
            continue


# Sort best first
final_data = sorted(
    final_data,
    key=lambda x: x["quality_score"],
    reverse=True
)

# Keep best 1000 max
final_data = final_data[:1000]

print(f"Final high-quality entries: {len(final_data)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    for item in final_data:

        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\nSaved FINAL dataset -> {OUTPUT_FILE}")