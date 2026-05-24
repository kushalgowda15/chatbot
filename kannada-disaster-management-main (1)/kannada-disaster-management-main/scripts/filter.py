import json
import re

INPUT_FILE = "dataset/processed/cleaned_dataset_v1.jsonl"
OUTPUT_FILE = "dataset/processed/cleaned_dataset_v2.jsonl"

filtered_data = []

# Kannada Unicode Range
KANNADA_PATTERN = re.compile(r'[\u0C80-\u0CFF]')

def contains_enough_kannada(text):
    """
    Check Kannada character ratio
    """

    kannada_chars = len(KANNADA_PATTERN.findall(text))

    total_chars = len(text)

    if total_chars == 0:
        return False

    ratio = kannada_chars / total_chars

    return ratio >= 0.35


def looks_ai_generated(answer):
    """
    Remove weird synthetic responses
    """

    bad_patterns = [
        "ಈ ಮಾಹಿತಿ ತಿಳಿದಿರಬೇಕು",
        "ಈ ಕ್ರಮಗಳು ಪ್ರಾಣ ರಕ್ಷಣೆಗೆ ಸಹಾಯಕ",
        "ಈ ತಪ್ಪುಗಳನ್ನು ಮಾಡಿದರೆ ಪರಿಸ್ಥಿತಿ ಇನ್ನೂ ಗಂಭೀರವಾಗಬಹುದು",
        "ಎಚ್ಚರಿಕೆ:",
        "ಸಿದ್ಧತೆಯ ಮಾಹಿತಿ",
        "ಈ ಸಿದ್ಧತೆಗಳನ್ನು ಮೊದಲೇ ಮಾಡಿ",
        "ಸಿದ್ಧತೆಯಿಲ್ಲದೆ ಅಪಾಯ ಹೆಚ್ಚು",
    ]

    for pattern in bad_patterns:
        if pattern in answer:
            return True

    return False


print("Filtering Kannada quality dataset...\n")

with open(INPUT_FILE, "r", encoding="utf-8") as f:

    for line in f:

        try:
            data = json.loads(line)

            question = data["question"].strip()
            answer = data["answer"].strip()

            # Kannada quality check
            if not contains_enough_kannada(question):
                continue

            if not contains_enough_kannada(answer):
                continue

            # Remove AI synthetic junk
            if looks_ai_generated(answer):
                continue

            filtered_data.append({
                "question": question,
                "answer": answer
            })

        except Exception:
            continue

print(f"High-quality Kannada entries: {len(filtered_data)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    for item in filtered_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\nSaved filtered dataset -> {OUTPUT_FILE}")