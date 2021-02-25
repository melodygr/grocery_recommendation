from flask import Flask, request, render_template
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.snowball import SnowballStemmer
import pandas as pd
import numpy as np
import pickle
import sys
from surprise import NormalPredictor
from surprise import Dataset
from surprise import Reader
from surprise.model_selection import cross_validate
from surprise import SVD
from surprise import KNNBaseline
from surprise import KNNBasic
from surprise.model_selection import train_test_split
from surprise.prediction_algorithms import knns
from surprise.similarities import cosine, msd, pearson
from surprise.prediction_algorithms import SVD, SVDpp
from surprise.model_selection import GridSearchCV
from surprise import accuracy

# sys.setrecursionlimit(2000)

products_desc = pickle.load(open("Pickle/products_desc_stemmed.p", "rb"))
new_rec_df = pickle.load(open("Pickle/new_rec_df.p", "rb"))
short_head = pickle.load(open("Pickle/short_head.p", "rb"))
reader = pickle.load(open("Pickle/reader.p", "rb"))
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


def grocery_rater(df, num, aisle=None):
    userID = 300000
    rating_list = []
    while num > 0:
        if aisle:
            product = df[df['aisle'].str.contains(aisle)].sample(1)
        else:
            product = df.sample(1)
        print('\n', product['product_name'].iloc[0])
        rating = input('How do you rate this product on a scale of 1-5, choose 0 to rate a different product:\n')
        if rating == '0':
            continue
        else:
            rating_one_product = {'user_id':userID,'product_id':product['product_id'].iloc[0],'rating':int(rating)}
            rating_list.append(rating_one_product) 
            num -= 1
    return rating_list

# return the top n diverse recommendations 
def recommend_diverse_products(ranked_products, n, aisle=None, percent_diverse=.20):
    
    num_diverse = round(n * percent_diverse)
    recs = []
    
    if n < 1:
        print('Number of recommended products must be 1 or more')
        return recs
    
    for idx, rec in enumerate(ranked_products):
        
        if n == 0:
            return recs
            
        prod_id, rating, prod_name, aisle_name = [*rec]
        
               
        if aisle:                                    # Did we specify an aisle? 
            if aisle in aisle_name:                  # Is it in the aisle we want?
                if n > num_diverse:                  # Are we looking for a long tail product? No
                    name = prod_name
                    print('Recommendation # ', idx+1, ': ', name, '\n')
                    recs.append(rec)
                    n-= 1
                else:                                 # Are we looking for a long tail product? Yes
                    if prod_id not in short_head:     # Is it NOT in the short_head list?
                        name = prod_name
                        print('Recommendation # ', idx+1, ': ', name, '\n')
                        recs.append(rec)
                        n-= 1
                    else:
                        continue
            elif idx == len(ranked_products)-1:
                print('No recommended products found')
                continue
        else:
            if n > num_diverse:                  # Are we looking for a long tail product? No
                name = prod_name
                print('Recommendation # ', idx+1, ': ', name, '\n')
                recs.append(rec)
                n-= 1
            else:                                 # Are we looking for a long tail product? Yes
                if prod_id not in short_head:     # Is it NOT in the short_head list?
                    name = prod_name
                    print('Recommendation # ', idx+1, ': ', name, '\n')
                    recs.append(rec)
                    n-= 1
                else:
                    continue

def generate_new_user_recommendations(n_to_rate, n_to_rec, percent_diverse, 
                                      rate_aisle=None, rec_aisle=None):
    # Get user ratings
    user_rating = grocery_rater(products_desc, n_to_rate, aisle=rate_aisle)

    # add the new ratings to the original ratings DataFrame
    print('Creating ratings dataset...')
    new_ratings_df = new_rec_df.append(user_rating, ignore_index=True)
    new_data = Dataset.load_from_df(new_ratings_df, reader)
    
    # train a model using the new combined DataFrame
    print('Training recommendation model...')
    new_user_svd = SVD(n_factors = 20, n_epochs = 10, lr_all = 0.005, reg_all = 0.4)
    new_user_svd.fit(new_data.build_full_trainset())
    
    # make predictions for the user
    print('Making predictions...')
    list_of_products = []
    for product in new_ratings_df['product_id'].unique():
        product_name = products_desc[products_desc['product_id'] == product]['product_name'].iloc[0]
        product_aisle = products_desc[products_desc['product_id'] == product]['aisle'].iloc[0]
        list_of_products.append((product, new_user_svd.predict(300000, product)[3], product_name, product_aisle))
    
    # order the predictions from highest to lowest rated
    ranked_products = sorted(list_of_products, key=lambda x:x[1], reverse=True)
    
    # return the top n recommendation
    return recommend_diverse_products(ranked_products, n_to_rec, aisle=rec_aisle, percent_diverse=percent_diverse)