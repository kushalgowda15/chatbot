import json

INPUT_FILE = "dataset/clean_disaster_dataset.jsonl"
OUTPUT_FILE = "dataset/final_clean_dataset.jsonl"

filtered = []

BAD_PATTERNS = [

    # repetitive synthetic templates
    "ಪ್ರಥಮ ಕ್ರಮವಾಗಿ",
    "ತಕ್ಷಣ ಕೈಗೊಳ್ಳಬೇಕಾದ ಕ್ರಮ",
    "ಈ ಕ್ರಮವನ್ನು ಕಟ್ಟುನಿಟ್ಟಾಗಿ ಪಾಲಿಸಿ",
    "ತಜ್ಞರ ಸಲಹೆ ಪ್ರಕಾರ",
    "ಇದು ನಿಮ್ಮನ್ನು ಸುರಕ್ಷಿತ ಸ್ಥಳಕ್ಕೆ",
    "ಯಾವುದೇ ವಿಳಂಬ ಮಾಡಬೇಡಿ",

    # low-quality generic
    "ಕುಡಿಯುವ ನೀರಿನ ಸಂಗ್ರಹಣೆ ಮಾಡ",
    "ಪಾಕೆಟ್ ರೇಡಿಯೋದಲ್ಲಿ",
    "ಬೆಲ್ಟ್ ಅಥವಾ ದಾರವನ್ನು",

    # noisy regional spam
    "ಬಳ್ಳಾರಿ ಪ್ರದೇಶ",
    "ಕರ್ನಾಟಕದಲ್ಲಿ",
    "ಮಂಗಳೂರು ಪ್ರದೇಶ",
    "ಕರಾವಳಿ ಪ್ರದೇಶ",
    "ಕಲಬುರಗಿ ಪ್ರದೇಶ",
    "ರಾಯಚೂರುದಲ್ಲಿ",

    # pandemic unrelated
    "ಮುಖಕವಚ",
    "ಸಾಮಾಜಿಕ ಅಂತರ",
    "ಲಸಿಕೆ"
]


GOOD_KEYWORDS = [
    "ನೆರೆ",
    "ಬೆಂಕಿ",
    "ಭೂಕಂಪ",
    "ಮಿಂಚು",
    "ಚಂಡಮಾರುತ",
    "ಭೂ ಕುಸಿತ",
    "ಗ್ಯಾಸು",
    "ಅಗ್ನಿ",
    "108",
    "101",
    "1077",
    "ಸುರಕ್ಷಿತ",
    "ಸಹಾಯ"
]


def is_good_entry(question, answer):

    text = f"{question} {answer}"

    # Remove bad patterns
    for pattern in BAD_PATTERNS:
        if pattern in text:
            return False

    # Must contain at least one disaster keyword
    found_keyword = False

    for keyword in GOOD_KEYWORDS:
        if keyword in text:
            found_keyword = True
            break

    if not found_keyword:
        return False

    return True


with open(INPUT_FILE, "r", encoding="utf-8") as f:

    for line in f:

        data = json.loads(line)

        question = data["question"]
        answer = data["answer"]

        if is_good_entry(question, answer):
            filtered.append(data)


print(f"Final filtered entries: {len(filtered)}")


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    for item in filtered:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


print(f"Saved -> {OUTPUT_FILE}")