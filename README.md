#  Movie Recommender API & Web App

## Goal of the Program

Recommend movies you’ll likely love based on one you already enjoy — using semantic similarity of plot, genres, cast, and director, plus quality/popularity filtering.

**Simple analogy**  
Imagine asking a movie expert friend:  
“I loved Inception — what else should I watch?”  
→ The app instantly suggests 10–20 similar movies that feel the same (story + vibe), but skips bad or obscure ones.

## What the Program Does 

1. You type a movie title (even with typos)
2. App finds the closest match
3. Returns ranked recommendations with ratings & vote counts
4. Clean Streamlit interface with filters (how many recs, min rating/votes)

## Main Features

- Semantic understanding with Sentence Transformers
- Fuzzy title search (handles misspellings)
- Boosts high-rated & popular movies
- FastAPI backend with health check & search endpoints
- Streamlit frontend with loading spinner & nice display
- Works with ~4800 movies (title, genres, cast, director, overview)

## Tech Stack

- Backend: FastAPI
- Model: Sentence Transformers + cosine similarity
- Fuzzy matching: rapidfuzz
- Frontend: Streamlit
- Data: ~4800 movies from TMDB-style dataset

## Model Performance & Limitations

Offline evaluation (genre overlap Precision@10): ~0.06–0.35
Strength: Captures plot + cast + director similarity well
Why some results aren't accurate:
Small dataset (~4800 movies) — misses many recent or niche titles
Content-based only (no user ratings) — can't capture personal taste or "surprise hits"
Overview text dominates → sometimes ignores genres/keywords, leading to odd matches
No handling for sequels/series — might recommend too similar or unrelated
Fuzzy matching can pick wrong movie if title is very common


Bottom line
Good for discovering similar vibes, but not as accurate as Netflix-style systems with millions of user ratings.
How It Can Be Improved Later

Add user ratings / collaborative filtering → hybrid model for personalized recs
Use larger dataset (e.g. 50k+ movies from TMDB API)
Stronger weighting: boost genres/keywords 5x over overview text
Add diversity re-ranking (MMR) → avoid recommending only sequels or same director
Integrate real-time data (e.g. trending movies, user reviews)
Better evaluation: user testing + A/B metrics instead of just offline Precision