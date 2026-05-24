import json
from pathlib import Path

INPUT_FILES = [
    "dataset/raw/kannada_disaster_7000.jsonl",
    "dataset/raw/kannada_disaster_dataset.jsonl",
    "dataset/raw/kannada_disaster_rag_dataset.jsonl"
]

OUTPUT_FILE = "dataset/processed/merged_dataset.jsonl"

merged = []

for file_path in INPUT_FILES:
    print(f"Reading: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                data = json.loads(line)

                question = None
                answer = None

                # Format 1
                if "instruction" in data and "output" in data:
                    question = data["instruction"]
                    answer = data["output"]

                # Format 2
                elif "query" in data and "response" in data:
                    question = data["query"]
                    answer = data["response"]

                # Format 3
                elif "question" in data and "answer" in data:
                    question = data["question"]
                    answer = data["answer"]

                if question and answer:
                    merged.append({
                        "question": question.strip(),
                        "answer": answer.strip()
                    })

            except Exception as e:
                continue

print(f"\nTotal merged entries: {len(merged)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for item in merged:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"\nSaved merged dataset -> {OUTPUT_FILE}")