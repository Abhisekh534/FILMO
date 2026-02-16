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

# --- Poster fetch by IMDb ID ---
# Poster UI removed per request; recommender UI only below.

# --- Existing recommender UI ---
selected_movie = st.selectbox('Search Movie Name', movies['title'].values)

if st.button('Recommend'):
    recommendations = recommend(selected_movie)
    cols = st.columns(5)
    for idx, movie_title in enumerate(recommendations):
        poster = get_poster_url(movie_title)
        with cols[idx]:
            if poster:
                st.image(poster, width=180)
                st.caption(movie_title)
            else:
                st.write(movie_title)