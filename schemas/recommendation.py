"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional


class RecommendationRequest(BaseModel):
    """Request schema for /recommend endpoint"""
    
    title: str = Field(..., description="Movie title", min_length=1, max_length=200)
    top_n: int = Field(10, description="Number of recommendations", ge=1, le=50)
    min_votes: int = Field(50, description="Minimum vote count", ge=0)
    min_rating: float = Field(6.0, description="Minimum rating", ge=0.0, le=10.0)
    
    @validator('title')
    def clean_title(cls, v):
        """Clean and validate title"""
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Iron Man",
                "top_n": 10,
                "min_votes": 50,
                "min_rating": 6.0
            }
        }


class MovieRecommendation(BaseModel):
    """Single movie recommendation"""
    
    title: str
    rating: float
    votes: int
    similarity: float
    score: float


class RecommendationResponse(BaseModel):
    """Response schema for /recommend endpoint"""
    
    input_movie: str
    total_recommendations: int
    recommendations: List[MovieRecommendation]
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_movie": "Iron Man",
                "total_recommendations": 10,
                "recommendations": [
                    {
                        "title": "Iron Man 3",
                        "rating": 6.8,
                        "votes": 8806,
                        "similarity": 0.892,
                        "score": 0.756
                    }
                ]
            }
        }


class SearchResult(BaseModel):
    """Single search result"""
    
    title: str
    match_score: float
    rating: float
    votes: int


class SearchResponse(BaseModel):
    """Response schema for /search endpoint"""
    
    query: str
    total_results: int
    results: List[SearchResult]
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "iron",
                "total_results": 5,
                "results": [
                    {
                        "title": "Iron Man",
                        "match_score": 95.0,
                        "rating": 7.6,
                        "votes": 12000
                    }
                ]
            }
        }


class MovieDetails(BaseModel):
    """Response schema for /movie/{title} endpoint"""
    
    title: str
    rating: float
    votes: int
    overview: str
    genres: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "The Matrix",
                "rating": 8.1,
                "votes": 9500,
                "overview": "A computer hacker learns...",
                "genres": "Action Science Fiction"
            }
        }


class HealthResponse(BaseModel):
    """Response schema for /health endpoint"""
    
    status: str
    model_loaded: bool
    total_movies: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "model_loaded": True,
                "total_movies": 4803
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    
    error: str
    detail: Optional[str] = None
    suggestions: Optional[List[SearchResult]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Movie not found",
                "detail": "Movie 'xyz123' not found",
                "suggestions": [
                    {
                        "title": "Similar Movie",
                        "match_score": 80.0,
                        "rating": 7.5,
                        "votes": 5000
                    }
                ]
            }
        }