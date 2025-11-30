import os
import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .utils import logger

class Retriever:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.units = []
        self.matrix = None
        self.use_openai = bool(os.environ.get("OPENAI_API_KEY"))
        
        if self.use_openai:
            logger.info("OPENAI_API_KEY found. In a real app, we would use embeddings here. For this demo, we stick to TF-IDF fallback to keep it simple and robust as requested, or we could implement hybrid.")
            # For the purpose of this specific prompt which asks for a fallback if key is missing, 
            # but allows richer answers if present. 
            # To keep the "ready-to-run" promise without complex dependency on `openai` package versions,
            # I will stick to TF-IDF for retrieval in both cases, but LLM generation will differ.
            pass

    def index_units(self, units: List[Dict[str, Any]]):
        self.units = units
        # Create a text representation for each unit
        corpus = [f"{u['name']} {u['kind']} {u.get('docstring', '')} {u['code']}" for u in units]
        
        if not corpus:
            logger.warning("No units to index.")
            return

        logger.info(f"Indexing {len(corpus)} units with TF-IDF...")
        self.matrix = self.vectorizer.fit_transform(corpus)

    def query_top_k(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        if self.matrix is None:
            return []
            
        query_vec = self.vectorizer.transform([query])
        # Calculate cosine similarity
        cosine_similarities = cosine_similarity(query_vec, self.matrix).flatten()
        
        # Get top k indices
        top_indices = cosine_similarities.argsort()[-k:][::-1]
        
        results = []
        for idx in top_indices:
            score = cosine_similarities[idx]
            if score > 0: # Filter out zero relevance
                results.append((self.units[idx]['id'], float(score)))
                
        return results
