import json
import faiss
import numpy as np

from sentence_transformers import SentenceTransformer

FAISS_INDEX_PATH = "vectorstore/disaster_index.faiss"
METADATA_PATH = "vectorstore/disaster_metadata.json"

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

print("Loading FAISS index...")

index = faiss.read_index(FAISS_INDEX_PATH)

print("Loading metadata...")

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

print("Retriever ready!\n")


def search_disaster_info(query, top_k=3):

    # Convert query to embedding
    query_embedding = model.encode([query])

    query_embedding = np.array(query_embedding).astype("float32")

    # Search FAISS
    distances, indices = index.search(query_embedding, top_k)

    results = []

    for idx, distance in zip(indices[0], distances[0]):

        item = metadata[idx]

        # Skip weak matches
        if distance > 15:
            continue

        results.append({
            "question": item["question"],
            "answer": item["answer"],
            "category": item["category"],
            "score": float(distance)
        })
        
    return results


if __name__ == "__main__":

    while True:

        query = input("Ask in Kannada: ")

        if query.lower() == "exit":
            break

        results = search_disaster_info(query, top_k=5)

        print("\nTop Results:\n")

        for i, result in enumerate(results, 1):

            print(f"{i}. Category: {result['category']}")
            print(f"Score: {result['score']:.2f}")
            print(f"Q: {result['question']}")
            print(f"A: {result['answer']}")
            print()