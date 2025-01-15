import numpy as np
from typing import List, Dict, Any
import openai
import json
import os

class KnowledgeBase:
    def __init__(self, cache_file: str = "embeddings_cache.json"):
        """Initialize knowledge base with caching."""
        self.cache_file = cache_file
        self.embeddings_cache = self._load_cache()
        self.dataset = None
        self.symptom_embeddings = None
        
    def _load_cache(self) -> Dict[str, List[float]]:
        """Load embeddings cache from file."""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save embeddings cache to file."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.embeddings_cache, f)

    def load_dataset(self, dataset: List[Dict[str, Any]]):
        """Load and process the dataset, creating embeddings for symptoms."""
        self.dataset = dataset
        symptoms = [entry['symptom'].lower() for entry in dataset]
        self.symptom_embeddings = self._get_embeddings(symptoms)

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings with batching and caching."""
        embeddings = []
        texts_to_embed = []
        indices = []

        # Check cache first
        for i, text in enumerate(texts):
            if text in self.embeddings_cache:
                embeddings.append(self.embeddings_cache[text])
            else:
                texts_to_embed.append(text)
                indices.append(i)

        # Batch process new embeddings
        if texts_to_embed:
            try:
                response = openai.Embedding.create(
                    input=texts_to_embed,
                    model="text-embedding-ada-002"
                )
                
                # Update cache with new embeddings
                for i, embedding_data in enumerate(response['data']):
                    text = texts_to_embed[i]
                    embedding = embedding_data['embedding']
                    self.embeddings_cache[text] = embedding
                    embeddings.insert(indices[i], embedding)
                
                # Save updated cache
                self._save_cache()
                
            except Exception as e:
                print(f"Error getting embeddings: {e}")
                return None

        return np.array(embeddings)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def get_relevant_entries(self, query: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Get relevant dataset entries based on semantic similarity."""
        query_embedding = self._get_embeddings([query.lower()])[0]
        
        relevant_entries = []
        for idx, entry in enumerate(self.dataset):
            similarity = self._cosine_similarity(query_embedding, self.symptom_embeddings[idx])
            if similarity >= threshold:
                relevant_entries.append({**entry, 'similarity': similarity})
        
        return sorted(relevant_entries, key=lambda x: x['similarity'], reverse=True)

    def get_relevant_questions(self, query: str, threshold: float = 0.7) -> List[str]:
        """Get relevant follow-up questions based on semantic similarity."""
        relevant_entries = self.get_relevant_entries(query, threshold)
        questions = []
        for entry in relevant_entries:
            questions.extend([q.strip() for q in entry['follow_up_questions'].split(';')])
        return list(dict.fromkeys(questions))  # Remove duplicates while preserving order

    def get_possible_conditions(self, query: str, threshold: float = 0.7) -> List[str]:
        """Get possible conditions based on semantic similarity."""
        relevant_entries = self.get_relevant_entries(query, threshold)
        conditions = []
        for entry in relevant_entries:
            conditions.extend([c.strip() for c in entry['conditions'].split(',')])
        return list(dict.fromkeys(conditions))  # Remove duplicates while preserving order
