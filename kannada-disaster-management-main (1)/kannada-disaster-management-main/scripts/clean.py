import json
import re

INPUT_FILE = "dataset/processed/merged_dataset.jsonl"
OUTPUT_FILE = "dataset/processed/cleaned_dataset_v1.jsonl"

seen_questions = set()
cleaned_data = []

def normalize_text(text):
    """
    Basic text normalization
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def is_valid_entry(question, answer):
    """
    Filter bad/noisy entries
    """

    # Too short
    if len(question) < 8:
        return False

    if len(answer) < 15:
        return False

    # Too long (usually hallucinated)
    if len(answer) > 500:
        return False

    # Remove obvious junk
    junk_patterns = [
        "lorem ipsum",
        "asdf",
        "dummy",
        "test data",
        "example response",
    ]

    q_lower = question.lower()
    a_lower = answer.lower()

    for pattern in junk_patterns:
        if pattern in q_lower or pattern in a_lower:
            return False

    return True

print("Cleaning dataset...\n")

with open(INPUT_FILE, "r", encoding="utf-8") as f:

    for line in f:

        try:
            data = json.loads(line)

            question = normalize_text(data["question"])
            answer = normalize_text(data["answer"])

            # Skip invalid
            if not is_valid_entry(question, answer):
                continue

            # Duplicate detection
            question_key = question.lower()

            if question_key in seen_questions:
                continue

            seen_questions.add(question_key)

            cleaned_data.append({
                "question": question,
                "answer": answer
            })

        except Exception:
            continue

print(f"Final cleaned entries: {len(cleaned_data)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    for item in cleaned_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\nSaved cleaned dataset -> {OUTPUT_FILE}")