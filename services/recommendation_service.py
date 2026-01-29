"""
Movie Recommendation Service
Handles model loading, movie search, and recommendations
"""

import pickle
import logging
from pathlib import Path
from typing import Optional, Dict, List
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz, process

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationService:

    def __init__(self, model_path: str = "./model/movie_recommender_model.pkl"):
        self.model_path = model_path
        self._model = None
        self._df = None
        self._embeddings = None
        self._movie_titles = None
        
    @property
    def model(self):
    
        if self._model is None:
            self._load_model()
        return self._model
    
    def _load_model(self):
        """Load pickle file with all model components"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            with open(self.model_path, 'rb') as f:
                self._model = pickle.load(f)
            
            self._df = self._model['dataframe']
            self._embeddings = self._model['embeddings']
            self._movie_titles = self._model['movie_titles']
            
            logger.info(f"✅ Model loaded: {len(self._df)} movies")
        except FileNotFoundError:
            logger.error(f"Model file not found: {self.model_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def search_movie(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for movies using fuzzy matching
        """
        # Ensure model is loaded
        _ = self.model
        
        # Fuzzy search
        matches = process.extract(
            query, 
            self._movie_titles, 
            scorer=fuzz.ratio,
            limit=limit
        )
        
        results = []
        for match, score, idx in matches:
            movie = self._df.iloc[idx]
            results.append({
                'title': movie['title'],
                'match_score': round(score, 1),
                'rating': round(movie['vote_average'], 1),
                'votes': int(movie['vote_count'])
            })
        
        return results
    
    def find_movie(self, title: str, threshold: int = 60) -> Optional[str]:
        """
        Find closest matching movie title
        """
        # Ensure model is loaded
        _ = self.model
        
        # Fuzzy match
        match = process.extractOne(
            title, 
            self._movie_titles, 
            scorer=fuzz.ratio
        )
        
        if match and match[1] >= threshold:
            return match[0]
        return None
    
    def get_recommendations(
        self, 
        movie_name: str, 
        top_n: int = 10,
        min_votes: int = 50,
        min_rating: float = 6.0
    ) -> Dict:
        """
        Get movie recommendations
        """
        # Ensure model is loaded
        _ = self.model
        
        # Find matching movie
        matched_title = self.find_movie(movie_name)
        
        if not matched_title:
            return {
                'error': f"Movie '{movie_name}' not found",
                'suggestions': self.search_movie(movie_name, limit=3)
            }
        
        # Get movie index
        movie_idx = self._df[self._df['title'] == matched_title].index[0]
        
        # Calculate similarity
        movie_embedding = self._embeddings[movie_idx].reshape(1, -1)
        similarities = cosine_similarity(movie_embedding, self._embeddings)[0]
        
        # Create working dataframe
        df_work = self._df.copy()
        df_work['similarity'] = similarities
        
        # Quality score
        df_work['quality_score'] = (
            (df_work['vote_average'] / 10) * 0.7 +
            (np.log1p(df_work['vote_count']) / np.log1p(df_work['vote_count'].max())) * 0.3
        )
        
        # Combined score
        df_work['final_score'] = df_work['similarity'] * 0.6 + df_work['quality_score'] * 0.4
        
        # Filter
        filtered = df_work[
            (df_work['vote_count'] >= min_votes) &
            (df_work['vote_average'] >= min_rating) &
            (df_work.index != movie_idx)
        ]
        
        # Get top recommendations
        recommendations = filtered.nlargest(top_n, 'final_score')
        
        # Format results
        results = []
        for idx, row in recommendations.iterrows():
            results.append({
                'title': row['title'],
                'rating': round(row['vote_average'], 1),
                'votes': int(row['vote_count']),
                'similarity': round(row['similarity'], 3),
                'score': round(row['final_score'], 3)
            })
        
        logger.info(f"Generated {len(results)} recommendations for '{matched_title}'")
        
        return {
            'input_movie': matched_title,
            'total_recommendations': len(results),
            'recommendations': results
        }
    
    def get_movie_details(self, title: str) -> Optional[Dict]:
        """
        Get details for a specific movie
        """
        # Ensure model is loaded
        _ = self.model
        
        # Find movie
        matched_title = self.find_movie(title)
        if not matched_title:
            return None
        
        movie = self._df[self._df['title'] == matched_title].iloc[0]
        
        return {
            'title': movie['title'],
            'rating': round(movie['vote_average'], 1),
            'votes': int(movie['vote_count']),
            'overview': movie.get('overview', ''),
            'genres': movie.get('genres', '')
        }


# Singleton instance
_service_instance = None

def get_service() -> RecommendationService:
    """Get or create service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = RecommendationService()
    return _service_instance