import json
from sentence_transformers import SentenceTransformer, util

print("Loading medical model...")
model = SentenceTransformer("sentence-transformers/embeddinggemma-300m-medical")
print("Model loaded!\n")

# Load dataset
with open("medical_data.json", "r") as f:
    medical_data = json.load(f)

# Build searchable text
documents = [
    f"{item['condition']}. Symptoms: {item['symptoms']}. Causes: {item['causes']}. Precautions: {item['precautions']}. Doctor advice: {item['see_doctor']}"
    for item in medical_data
]

# Encode disease database
doc_embeddings = model.encode(documents, convert_to_tensor=True)

# Input
user_input = input("Enter patient symptoms: ").strip().lower()

# Encode user symptoms
query_embedding = model.encode(user_input, convert_to_tensor=True)

# Find best match
scores = util.cos_sim(query_embedding, doc_embeddings)[0]
best_match_idx = scores.argmax().item()
best_match = medical_data[best_match_idx]

# Output
print("\n==============================")
print("      LIFELINE AI REPORT      ")
print("==============================\n")
print(f"Entered Symptoms   : {user_input}")
print(f"Possible Condition : {best_match['condition']}")
print(f"Causes             : {best_match['causes']}")
print(f"Precautions        : {best_match['precautions']}")
print(f"When to See Doctor : {best_match['see_doctor']}")
print(f"Confidence Score   : {scores[best_match_idx]:.4f}")
print("\n⚠️ Disclaimer: This is an AI-assisted suggestion, not a final medical diagnosis.")