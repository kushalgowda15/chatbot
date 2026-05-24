import json

INPUT_FILE = "dataset/processed/cleaned_dataset_v2.jsonl"
OUTPUT_FILE = "dataset/processed/categorized_dataset.jsonl"

categorized_data = []

CATEGORY_KEYWORDS = {

    "flood": [
        "ನೆರೆ",
        "ನೀರು",
        "ಪ್ರವಾಹ"
    ],

    "fire": [
        "ಬೆಂಕಿ",
        "ಅಗ್ನಿ",
        "ಸುಟ್ಟು"
    ],

    "earthquake": [
        "ಭೂಕಂಪ",
        "ಕಂಪನ"
    ],

    "landslide": [
        "ಭೂ ಕುಸಿತ",
        "ಗುಡ್ಡ",
        "ಮಣ್ಣು ಕುಸಿತ"
    ],

    "cyclone": [
        "ಚಂಡಮಾರುತ",
        "ಗಾಳಿ ಮಳೆ"
    ],

    "heatwave": [
        "ಬಿಸಿಗಾಳಿ",
        "ಹೆಚ್ಚು ಬಿಸಿ"
    ],

    "lightning": [
        "ಮಿಂಚು",
        "ಗುಡುಗು"
    ],

    "gas_leak": [
        "ಗ್ಯಾಸು",
        "ಅನಿಲ"
    ],

    "road_accident": [
        "ಅಪಘಾತ",
        "ರಸ್ತೆ"
    ],

    "first_aid": [
        "ಮೊದಲ ಸಹಾಯ",
        "ಗಾಯ",
        "ರಕ್ತ"
    ],

    "emergency_contact": [
        "108",
        "101",
        "100",
        "1077",
        "ಸಹಾಯ"
    ],

    "evacuation": [
        "ಸ್ಥಳಾಂತರ",
        "ಸುರಕ್ಷಿತ ಸ್ಥಳ"
    ]
}


def detect_category(question, answer):

    combined_text = (question + " " + answer).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():

        for keyword in keywords:

            if keyword.lower() in combined_text:
                return category

    return "general"


print("Categorizing dataset...\n")

with open(INPUT_FILE, "r", encoding="utf-8") as f:

    for line in f:

        try:
            data = json.loads(line)

            question = data["question"]
            answer = data["answer"]

            category = detect_category(question, answer)

            categorized_data.append({
                "category": category,
                "question": question,
                "answer": answer
            })

        except Exception:
            continue

print(f"Categorized entries: {len(categorized_data)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    for item in categorized_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\nSaved categorized dataset -> {OUTPUT_FILE}")