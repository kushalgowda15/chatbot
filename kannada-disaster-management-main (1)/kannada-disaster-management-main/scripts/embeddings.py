import json
import faiss
import numpy as np
from pathlib import Path

from sentence_transformers import SentenceTransformer

DATASET_PATH = "dataset/final_clean_dataset.jsonl"

FAISS_INDEX_PATH = "vectorstore/disaster_index.faiss"
METADATA_PATH = "vectorstore/disaster_metadata.json"

# Ensure vectorstore directory exists
Path("vectorstore").mkdir(parents=True, exist_ok=True)

print("Loading multilingual embedding model...")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

documents = []
metadata = []

print("Loading dataset...\n")

with open(DATASET_PATH, "r", encoding="utf-8") as f:

    for line in f:

        data = json.loads(line)

        question = data["question"]
        answer = data["answer"]
        category = data["category"]

        # Combine question + answer
        combined_text = f"""
            Category: {category}

            Question:
            {question}

            Answer:
            {answer}
            """

        documents.append(combined_text)

        metadata.append({
            "question": question,
            "answer": answer,
            "category": category
        })

print(f"Loaded {len(documents)} documents")

print("\nCreating embeddings...")

embeddings = model.encode(
    documents,
    convert_to_numpy=True,
    show_progress_bar=True
)

# Convert to float32
embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]

print(f"Embedding dimension: {dimension}")

print("\nBuilding FAISS index...")

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

print(f"Stored vectors: {index.ntotal}")

print("\nSaving FAISS index...")

faiss.write_index(index, FAISS_INDEX_PATH)

with open(METADATA_PATH, "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

print("\nDONE")
print(f"Saved index -> {FAISS_INDEX_PATH}")
print(f"Saved metadata -> {METADATA_PATH}")