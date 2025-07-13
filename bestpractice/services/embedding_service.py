
import asyncio
from typing import List
import numpy as np
from bestpractice.config import settings

class EmbeddingService:
    """Service for generating text embeddings using SentenceTransformer"""

    def __init__(self):
        self.model_name = "paraphrase-MiniLM-L3-v2"
        self.model = None
        self._model_lock = asyncio.Lock()

    async def _load_model(self):
        """Load the SentenceTransformer model"""
        if self.model is None:
            async with self._model_lock:
                if self.model is None:
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer(self.model_name)
                    print(f"Loaded SentenceTransformer model: {self.model_name}")

    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
        
        Returns:
            numpy array of embeddings
        """
        if not texts:
            return np.array([])

        await self._load_model()

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return np.array([])

    async def generate_single_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
        
        Returns:
            numpy array embedding
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if len(embeddings) > 0 else np.array([])

    async def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
        
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return max(0.0, min(1.0, similarity))
        except Exception as e:
            print(f"Error calculating similarity: {str(e)}")
            return 0.0

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model
        
        Returns:
            Embedding dimension
        """
        return 384  # Fixed for MiniLM models

