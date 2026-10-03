"""Build the trusted corpus index locally; API startup only loads artifacts."""
import json
from pathlib import Path
import faiss
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

BASE = Path(__file__).resolve().parent
INDEX_DIR = BASE / "index"

def build_index():
    documents = json.loads((BASE/"knowledge_base/guidance.json").read_text(encoding="utf-8"))
    vectorizer = TfidfVectorizer(ngram_range=(1,2),stop_words="english",max_features=4096,dtype=np.float32)
    vectors = vectorizer.fit_transform([item["content"] for item in documents]).toarray()
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    INDEX_DIR.mkdir(parents=True,exist_ok=True)
    faiss.write_index(index,str(INDEX_DIR/"energy.faiss"))
    joblib.dump(vectorizer,INDEX_DIR/"vectorizer.pkl")
    (INDEX_DIR/"chunks.json").write_text(json.dumps(documents,indent=2),encoding="utf-8")
    print(f"Indexed {len(documents)} sourced guidance sections; {vectors.shape[1]} TF-IDF dimensions")

if __name__=="__main__":
    build_index()
