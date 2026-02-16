import streamlit as st
import pickle
import pandas as pd
import requests
import re


def is_valid_imdb_id(imdb_id: str) -> bool:
    """Return True if `imdb_id` matches IMDb ID pattern like tt1234567."""
    return bool(re.fullmatch(r'tt\d{7,8}', (imdb_id or '').strip()))


def get_poster_url(imdb_or_title: str, api_key: str = '17418ada') -> str | None:
    """Fetch poster URL from OMDb.

    - If `imdb_or_title` looks like an IMDb id (ttNNN) it will use `i=`.
    - Otherwise it will search by title using `t=`.
    Returns poster URL or None.
    """
    imdb_or_title = (imdb_or_title or '').strip()
    if not imdb_or_title:
        return None
    if is_valid_imdb_id(imdb_or_title):
        url = f'http://www.omdbapi.com/?i={imdb_or_title}&apikey={api_key}'
    else:
        # encode title for URL
        from urllib.parse import quote_plus

        q = quote_plus(imdb_or_title)
        url = f'http://www.omdbapi.com/?t={q}&apikey={api_key}'
    try:
        resp = requests.get(url, timeout=6)
        data = resp.json()
        if data.get('Response') == 'True' and data.get('Poster') and data.get('Poster') != 'N/A':
            return data.get('Poster')
    except Exception:
        return None
    return None


def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommendations = []
    for i in movie_list:
        recommendations.append(movies.iloc[i[0]].title)
    return recommendations


movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

similarity = pickle.load(open('similarity.pkl', 'rb'))

st.title("FILMO")

# Load TMDB overviews to show on hover (fallback to tags if not found)
try:
    tmdb = pd.read_csv('tmdb_5000_movies.csv')
    overview_map = pd.Series(tmdb.overview.values, index=tmdb.id).to_dict()
except Exception:
    overview_map = {}

# Inject CSS for poster hover overlay
st.markdown(
    """
    <style>
    [data-testid="stColumn"] { padding: 0 8px; }
    .poster-container { position: relative; width: 100%; aspect-ratio: 2/3; margin: 0; display: inline-block; }
    .poster-img { width: 100%; height: 100%; object-fit: cover; display: block; transition: opacity 0.25s ease-in-out; }
    .poster-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: white; text-align: center; padding: 8px; background: rgba(0,0,0,0.75); opacity: 0; transition: opacity 0.25s ease-in-out; overflow: hidden; }
    .poster-overlay-text { font-size: 12px; line-height: 1.4; overflow: hidden; max-height: 100%; word-wrap: break-word; }
    .poster-container:hover .poster-img { opacity: 0.5; }
    .poster-container:hover .poster-overlay { opacity: 1; }
    .poster-title { font-size: 13px; font-weight: 600; margin-top: 6px; word-wrap: break-word; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Poster fetch by IMDb ID ---
# Poster UI removed per request; recommender UI only below.

# --- Existing recommender UI ---
selected_movie = st.selectbox('Search Movie Name', movies['title'].values)

if st.button('Recommend'):
    recommendations = recommend(selected_movie)
    cols = st.columns(5, gap='small')
    import html as _html
    for idx, movie_title in enumerate(recommendations):
        # find movie_id to get overview
        try:
            movie_id = int(movies[movies['title'] == movie_title].movie_id.iloc[0])
        except Exception:
            movie_id = None
        overview = overview_map.get(movie_id) if movie_id in overview_map else None
        if not overview:
            # fallback to tags column if available
            try:
                overview = movies[movies['title'] == movie_title].tags.iloc[0]
            except Exception:
                overview = ''
        poster = get_poster_url(movie_title)
        with cols[idx]:
            if poster:
                safe_overview = _html.escape(overview)
                html_block = f'''<div class="poster-container">
                    <img class="poster-img" src="{poster}" alt="{_html.escape(movie_title)}" />
                    <div class="poster-overlay"><div class="poster-overlay-text">{safe_overview}</div></div>
                </div>
                <div class="poster-title">{_html.escape(movie_title)}</div>'''
                st.markdown(html_block, unsafe_allow_html=True)
            else:
                st.write(movie_title)
