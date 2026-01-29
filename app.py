from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from services.recommendation_service import get_service
from schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    MovieDetails,
    SearchResponse,
    HealthResponse
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Movie Recommender API",
    description="Content-based movie recommendation system using semantic embeddings",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Get service instance
service = get_service()


@app.get("/", tags=["Root"])
@limiter.limit("20/minute")
async def root(request: Request):
    """
    API welcome message with documentation links
    """
    return {
        "message": "🎬 Movie Recommender API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "POST /recommend": "Get movie recommendations",
            "GET /search": "Search for movies",
            "GET /movie/{title}": "Get movie details",
            "GET /health": "Health check"
        }
    }


@app.post("/recommend", response_model=RecommendationResponse, tags=["Recommendations"])
@limiter.limit("10/minute")
async def recommend(request: Request, req: RecommendationRequest):
    """
    Get movie recommendations with optional filters
    
    - **title**: Movie name (required)
    - **top_n**: Number of recommendations (default: 10, max: 50)
    - **min_votes**: Minimum vote count filter (default: 50)
    - **min_rating**: Minimum rating filter (default: 6.0)
    """
    try:
        logger.info(f"Recommendation request: {req.title}")
        
        # Get recommendations
        result = service.get_recommendations(
            movie_name=req.title,
            top_n=req.top_n,
            min_votes=req.min_votes,
            min_rating=req.min_rating
        )
        
        # Handle error case
        if 'error' in result:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": result['error'],
                    "suggestions": result.get('suggestions', [])
                }
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in recommend endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", response_model=SearchResponse, tags=["Search"])
@limiter.limit("30/minute")
async def search(request: Request, query: str, limit: int = 5):
    """
    Search for movies (autocomplete)
    
    - **query**: Search query
    - **limit**: Max results to return (default: 5, max: 20)
    """
    try:
        if not query or len(query) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
        
        if limit > 20:
            limit = 20
        
        results = service.search_movie(query, limit=limit)
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/movie/{title}", response_model=MovieDetails, tags=["Movies"])
@limiter.limit("30/minute")
async def get_movie(request: Request, title: str):
    """
    Get details for a specific movie
    
    - **title**: Movie title (fuzzy matching supported)
    """
    try:
        details = service.get_movie_details(title)
        
        if not details:
            raise HTTPException(
                status_code=404, 
                detail=f"Movie '{title}' not found"
            )
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_movie endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint (no rate limit)
    """
    try:
        # Check if service is loaded
        _ = service.model
        
        return {
            "status": "healthy",
            "model_loaded": True,
            "total_movies": len(service._df)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "model_loaded": False,
                "error": str(e)
            }
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc.detail)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    logger.error(f"Internal error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)