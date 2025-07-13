import faiss
import numpy as np
from typing import List, Dict, Any, Tuple

class VectorStore:
    """FAISS-based vector store for similarity search"""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine after normalization)
        self.texts: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        print(f"Initialized FAISS vector store with dimension {self.dimension}")

    def add_documents(self, texts: List[str], embeddings: np.ndarray, metadata: List[Dict[str, Any]] = None):
        if len(texts) != embeddings.shape[0]:
            raise ValueError("Number of texts and embeddings must match")
        
        # Normalize embeddings for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized_embeddings = embeddings / norms

        self.index.add(normalized_embeddings.astype(np.float32))
        self.texts.extend(texts)

        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{} for _ in texts])

        print(f"Added {len(texts)} documents to FAISS vector store")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        if self.index.ntotal == 0:
            return []

        # Normalize query embedding
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

        distances, indices = self.index.search(query_embedding, k)
        results = []

        for idx, score in zip(indices[0], distances[0]):
            if idx < len(self.texts):
                results.append((self.texts[idx], float(score), self.metadata[idx]))

        return results

    def clear(self):
        self.index.reset()
        self.texts = []
        self.metadata = []
        print("Cleared FAISS vector store")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.texts),
            "dimension": self.dimension,
            "index_type": "FAISS"
        }
