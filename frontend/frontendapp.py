import streamlit as st
import requests
import pandas as pd
import os
import requests
#configuration:

API_URL = os.getenv("API_URL", "https://movies-recommandation-fastapi.onrender.com")
st.set_page_config(page_title="Movie Recommender", layout="wide")

#   HEADER & DESCRIPTION


st.title("🎬 Movie Recommender")
st.markdown("""
Find movies similar to one you like ...
Just type a movie title and get great recommendations!
""")

#   SIDEBAR – CONTROLS

with st.sidebar:
    st.header("Settings")
    top_n = st.slider("Number of recommendations", 5, 30, 10, step=5)
    min_votes = st.slider("Minimum votes (popularity filter)", 0, 1000, 100, step=50)
    min_rating = st.slider("Minimum rating", 0.0, 10.0, 6.0, step=0.5)
    
    st.markdown("---")
    st.info("Tip: Try titles like 'Inception', 'The Matrix', 'Interstellar', 'Toy Story'")

#   MAIN INPUT AREA


col1, col2 = st.columns([3, 1])

with col1:
    movie_input = st.text_input(
        "Enter a movie title you like",
        placeholder="e.g. Inception, The Dark Knight, Parasite...",
        help="We use fuzzy matching — small typos are usually fine"
    )

with col2:
    search_button = st.button("Find Recommendations", type="primary", use_container_width=True)

#   SEARCH WHILE TYPING 
if movie_input and len(movie_input) >= 2 and not search_button:
    try:
        r = requests.get(f"{API_BASE_URL}/search", params={"query": movie_input, "limit": 8})
        if r.status_code == 200:
            suggestions = r.json()["results"]
            if suggestions:
                st.caption("Did you mean one of these?")
                for sug in suggestions:
                    st.caption(f"· {sug['title']} ({sug['rating']}/10)")
    except:
        pass

#   RECOMMENDATION LOGIC

if search_button and movie_input.strip():
    with st.spinner("Finding great movies for you..."):
        try:
            payload = {
                "title": movie_input.strip(),
                "top_n": top_n,
                "min_votes": min_votes,
                "min_rating": min_rating
            }
            response = requests.post(f"{API_URL}/recommend", json=payload, timeout=12)
            
            if response.status_code == 200:
                data = response.json()
                
                st.success(f"Recommendations for **{data['input_movie']}**")
                
                # Show results in nice table
                df = pd.DataFrame(data["recommendations"])
                df = df[["title", "rating", "votes", "similarity", "score"]]
                df.columns = ["Movie Title", "Rating", "Votes", "Similarity", "Combined Score"]
                
                st.dataframe(
                    df.style.format({
                        "Rating": "{:.1f}",
                        "Similarity": "{:.3f}",
                        "Combined Score": "{:.3f}",
                        "Votes": "{:,}"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
            elif response.status_code == 404:
                error_data = response.json()
                st.warning(f"Movie '{movie_input}' not found.")
                if "suggestions" in error_data:
                    st.info("Did you mean one of these?")
                    for sug in error_data.get("suggestions", []):
                        st.write(f"• {sug['title']} ({sug['rating']}/10)")
            else:
                st.error(f"Something went wrong (status {response.status_code})")
                st.json(response.json())
                
        except requests.exceptions.RequestException as e:
            st.error(f"Cannot connect to API → {str(e)}")
            st.info("Make sure the API is running (`uvicorn app:app --reload`)")

