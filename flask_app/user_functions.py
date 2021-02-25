from flask import Flask, request, render_template
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.snowball import SnowballStemmer
import pandas as pd
import numpy as np
import pickle
import sys

# sys.setrecursionlimit(2000)

products_desc = pickle.load(open("Pickle/products_desc_stemmed.p", "rb"))
stem_count_vec = pickle.load(open("Pickle/stem_count_vec.p", "rb"))
stem_count_vec_matrix = pickle.load(open("Pickle/stem_count_vec_matrix.p", "rb"))
stemmer = SnowballStemmer("english")   

def stem_and_vectorize_products_based_on_metadata(product_input):

    word_list = nltk.word_tokenize(product_input)
    
    input_stemmed = ' '.join([stemmer.stem(word) for word in word_list])
    
    vec = stem_count_vec.transform(pd.Series(input_stemmed))
    
    simil = cosine_similarity(vec, stem_count_vec_matrix)
    
    simil_scores = pd.DataFrame(simil.reshape(stem_count_vec_matrix.shape[0],), 
                                index = products_desc.index, columns=['score'])
    
    # Don't return scores of zero, only as many positive scores as exist
    non_zero_scores = simil_scores[simil_scores['score'] > 0]
    
    if len(non_zero_scores) == 0:
        return
    
    if len(non_zero_scores) < 10:
        item_count = len(non_zero_scores)
    else:
        item_count = 10
    
    similarity_scores = simil_scores.sort_values(['score'], ascending=False)[:item_count]
    
    return (products_desc['product_name'].iloc[similarity_scores.index])