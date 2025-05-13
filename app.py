import pickle
import pandas as pd
import requests
import sqlite3
import streamlit as st

# Database connection
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Authentication Functions
def register_user(username, password):
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    return c.fetchone() is not None

def logout_user():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None

def fetch_poster_and_url(movie_id, api_key):
    """Fetch movie poster and TMDB URL using the movie ID."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path', '')
        poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        tmdb_url = f"https://www.themoviedb.org/movie/{movie_id}"
        return poster_url, tmdb_url
    except Exception:
        return None, None

def recommend(movie, movies, similarity, api_key):
    """Get movie recommendations based on similarity scores."""
    try:
        index = movies[movies['title'].str.lower() == movie.lower()].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        recommended_movies = []
        for i in distances[1:6]:
            movie_id = movies.iloc[i[0]].movie_id
            poster_url, tmdb_url = fetch_poster_and_url(movie_id, api_key)
            recommended_movies.append({
                "title": movies.iloc[i[0]].title,
                "poster_url": poster_url,
                "tmdb_url": tmdb_url
            })
        return recommended_movies
    except IndexError:
        return []

# Load Data
movies = pickle.load(open('movie_list.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))
TMDB_API_KEY = "8265bd1679663a7ea12ac168da84d2e8"

# Streamlit App
st.title("🎬 Movie Recommendation System with Authentication")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None

# Navbar
if st.session_state['logged_in']:
    st.sidebar.markdown(f"👤 Logged in as: **{st.session_state['username']}**")
    if st.sidebar.button("Log Out", key="logout_button"):
        logout_user()
        st.rerun()
else:
    nav_option = st.sidebar.radio("Navigation", ["Log In", "Register"])

# Authentication Pages
if not st.session_state['logged_in']:
    if nav_option == "Log In":
        st.subheader("Log In")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log In"):
            if authenticate_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    elif nav_option == "Register":
        st.subheader("Register")
        new_username = st.text_input("Create Username")
        new_password = st.text_input("Create Password", type="password")
        if st.button("Register"):
            if register_user(new_username, new_password):
                st.success("Registration successful! Please log in.")
            else:
                st.error("Username already exists. Please choose a different username.")
else:
    # Recommendation Section
    st.subheader("Welcome to Movie Recommendations!")
    movie_list = movies['title'].values
    selected_movie = st.selectbox("Type or select a movie:", movie_list)

    if st.button("Show Recommendations"):
        recommended_movies = recommend(selected_movie, movies, similarity, TMDB_API_KEY)
        if recommended_movies:
            cols = st.columns(5)
            for i, col in enumerate(cols):
                if i < len(recommended_movies):
                    movie = recommended_movies[i]
                    with col:
                        st.markdown(f"[![{movie['title']}]({movie['poster_url']})]({movie['tmdb_url']})")
                        st.caption(movie['title'])
        else:
            st.error("No recommendations found!")
