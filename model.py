import numpy as np
import pandas as pd

movies = pd.read_csv('tmdb_5000_movies.csv')
credits = pd.read_csv('tmdb_5000_credits.csv')

movies = movies.merge(credits, on='title')

#IMPORTANT COLUMNS for CONTENT BASED RECOMMENDER SYSTEM

#id(important for fetching posters on website)
#title
#genre
#keywords
#overview
#cast
#crew

#content based hai isliye ham numerical columns like vote_average aur vote_count ko skip karenge
#collaborative filtering based me ham numerical values ke basis pe hi saari rows ka ek n-dimensional vector banaate hai aur phir euclidean distance calculate karte hain

movies = movies[['movie_id', 'title', 'genres', 'keywords', 'overview', 'cast', 'crew']]

movies.dropna(inplace=True) #we can drop because only 3 rows have NAs , not a big number in comparison to total 4800 rows

#print(movies.iloc[0].genres)
#[{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}, {"id": 14, "name": "Fantasy"}, {"id": 878, "name": "Science Fiction"}]
#genres column me ye format hai ise ['Action', 'Adventure', ...] is format me badalna hai

#genres me jo data hai vo list nahi balki string of a list aur hamko list chahiye keywords nikaalne ke liye
#uske liye ham us string of list pe ye function laga sakte hain ast.literal_eval() from ast module

import ast

def convert(obj):
    L = []
    for i in ast.literal_eval(obj):
        L.append(i['name'])
    return L

def convert3(obj):
    L = []
    for i in ast.literal_eval(obj)[0:3]:
        L.append(i['name'])
    return L

def fetchDir(obj):
    L = []
    for i in ast.literal_eval(obj):
        if i['job'] == 'Director':
            L.append(i['name'])
            break
    return L

#helper function genres me se keywords nikaalne ke liye

#is function ko dataframe ke poore column pe ek saath applly kar denge

movies['genres'] = movies['genres'].apply(convert) 

#keywords column ka bhi same hi structure hai , we will do same with that also

movies['keywords'] = movies['keywords'].apply(convert)

movies['cast'] = movies['cast'].apply(convert3)

movies['crew'] = movies['crew'].apply(fetchDir)

movies['overview'] = movies['overview'].apply(lambda x : x.split())

#removing spaces to make proper tags
movies['genres'] = movies['genres'].apply(lambda x : [i.replace(" ", "") for i in x])
movies['keywords'] = movies['keywords'].apply(lambda x : [i.replace(" ", "") for i in x])
movies['cast'] = movies['cast'].apply(lambda x : [i.replace(" ", "") for i in x])
movies['crew'] = movies['crew'].apply(lambda x : [i.replace(" ", "") for i in x])

#make new column tags to concatenate all the lists
movies['tags'] = movies['overview'] + 3 * movies['genres'] + movies['keywords'] + 5 * movies['cast'] + 5 * movies['crew']

#making new dataframe containing only movie_id, title, and tags

new_df_movies = movies[['movie_id', 'title', 'tags']]

new_df_movies['tags'] = new_df_movies['tags'].apply(lambda x : " ".join(x))
new_df_movies['tags'] = new_df_movies['tags'].apply(lambda x : x.lower())

#for performing stemming over the tags
#Eg:- dancing, dancer, danced, dance all will change to the stem dance
from nltk.stem.porter import PorterStemmer
ps = PorterStemmer()

def stem(text):
    y = []

    for i in text.split():
        y.append(ps.stem(i))

    return " ".join(y)

new_df_movies['tags'] = new_df_movies['tags'].apply(stem)

#Vectorization(count of words)

from sklearn.feature_extraction.text import CountVectorizer
cv = CountVectorizer(max_features=5000, stop_words='english')


vectors = cv.fit_transform(new_df_movies['tags']).toarray()
#har movie ab vector ki form me aa chuki hai , the closer the vectors of two movies the similar the movies will be
#euclidean distance fails in high dimension planes
#isliye we will not calculate the euclidean distance instead we will calculate the cosine distance
#har movie ka har movie ke saath cosine distance

from sklearn.metrics.pairwise import cosine_similarity

similarity = cosine_similarity(vectors)

def recommend(movie):
    movie_index = new_df_movies[new_df_movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x : x[1])[1:6]

    for i in movie_list:
        print(new_df_movies.iloc[i[0]].title)

import pickle

pickle.dump(new_df_movies.to_dict(), open('movie_dict.pkl', 'wb'))

pickle.dump(similarity, open('similarity.pkl', 'wb'))
