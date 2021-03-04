from flask import Flask, request, render_template
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.snowball import SnowballStemmer
import pandas as pd
import numpy as np
import pickle
import sys
from surprise import Dataset
from surprise import Reader
from surprise import SVD


rec_columns = pickle.load(open('Pickle/rec_columns.p','rb'))
rec_index = pickle.load(open('Pickle/rec_index.p', 'rb'))
rec_user = pickle.load(open('Pickle/rec_user.p', 'rb'))
rec_rating = pickle.load(open('Pickle/rec_rating.p', 'rb'))
rec_prod_id = pickle.load(open('Pickle/rec_prod_id.p', 'rb'))
new_rec_df = pd.DataFrame(np.column_stack([rec_user, rec_prod_id, rec_rating]), index=rec_index, columns=rec_columns)

short_head = pickle.load(open("Pickle/short_head.p", "rb"))
reader = pickle.load(open("Pickle/reader.p", "rb"))
new_stem_count_vec = pickle.load(open("Pickle/new_stem_count_vec.p", "rb"))
new_stem_count_vec_matrix = pickle.load(open("Pickle/new_stem_count_vec_matrix.p", "rb"))
stemmer = SnowballStemmer("english")   

products_desc_stemmed = pd.read_pickle("Pickle/products_desc_stemmed.p")
prod_columns = pickle.load(open("Pickle/prod_columns.p", "rb"))
prod_index = pickle.load(open("Pickle/prod_index.p", "rb"))
prod_name = pickle.load(open("Pickle/prod_name.p", "rb"))
prod_aisle = pickle.load(open("Pickle/prod_aisle.p", "rb"))
prod_id = pickle.load(open("Pickle/prod_id.p", "rb"))
products_desc = pd.DataFrame(np.column_stack([prod_name, prod_aisle, prod_id]), index=prod_index, columns=['Product Name', 'Aisle', 'Product ID'])

def stem_and_vectorize_products_based_on_metadata(product_input):

    word_list = nltk.word_tokenize(product_input)
    input_stemmed = ' '.join([stemmer.stem(word) for word in word_list])
    vec = new_stem_count_vec.transform(np.array(input_stemmed).reshape(1,))
    
    simil = cosine_similarity(vec, new_stem_count_vec_matrix)
    simil_shape = simil.reshape(new_stem_count_vec_matrix.shape[0],)
    simil_scores = pd.DataFrame(data=simil_shape, index=prod_index, columns=['score'])

    # Don't return scores of zero, only as many positive scores as exist
    non_zero_scores = simil_scores[simil_scores['score'] > 0]
    
    if len(non_zero_scores) == 0:
        return 0, 'None'
    
    if len(non_zero_scores) < 10:
        item_count = len(non_zero_scores)
    else:
        item_count = 10
    
    similarity_scores = simil_scores.sort_values(['score'], ascending=False)[:item_count]

    return item_count, (products_desc.iloc[list(similarity_scores.index)]).to_html(index=False, justify='center', classes='table1', border=2)

def get_sample_product(aisle=None):
    if aisle:
        product = products_desc[products_desc['Aisle'].str.contains(aisle)].sample(1)
    else:
        product = products_desc.sample(1)
    name = product['Product Name'].iloc[0]
    prod_aisle = product['Aisle'].iloc[0]
    prod_id = product['Product ID'].iloc[0]  
    return name, prod_aisle, prod_id

def generate_recs(ratings_list, n_to_rec, percent_diverse, rec_aisle=None):
    # Convert ratings list to user_ratings
    userID = 300000
    user_rating =[]
    for product, rating in ratings_list:
        rating_one_product = {'user_id':userID,'product_id':product,'rating':rating}
        user_rating.append(rating_one_product) 

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
        product_name = products_desc[products_desc['Product ID'] == product]['Product Name'].iloc[0]
        product_aisle = products_desc[products_desc['Product ID'] == product]['Aisle'].iloc[0]
        list_of_products.append((product, round(new_user_svd.predict(300000, product)[3], 3), product_name, product_aisle))
    
    # order the predictions from highest to lowest rated
    ranked_products = sorted(list_of_products, key=lambda x:x[1], reverse=True)
    
    # return the top n recommendation
    num_results, svd_recs = recommend_diverse_products(ranked_products, n_to_rec, aisle=rec_aisle, percent_diverse=percent_diverse)
    print('Complete')
    return num_results, svd_recs

def grocery_rater(df, num, aisle=None):
    userID = 300000
    rating_list = []
    while num > 0:
        if aisle:
            product = df[df['Aisle'].str.contains(aisle)].sample(1)
        else:
            product = df.sample(1)
        print('\n', product['Product Name'].iloc[0])
        rating = input('How do you rate this product on a scale of 1-5, choose 0 to rate a different product:\n')
        if rating == '0':
            continue
        else:
            rating_one_product = {'user_id':userID,'product_id':product['Product ID'].iloc[0],'rating':int(rating)}
            rating_list.append(rating_one_product) 
            num -= 1
    return rating_list

# return the top n diverse recommendations 
def recommend_diverse_products(ranked_products, n, aisle=None, percent_diverse=.20):
    
    num_diverse = round(n * percent_diverse)
    recs = []
    
    if n < 1:
        print('Number of recommended products must be 1 or more')
        return 0, "None"
    
    for idx, rec in enumerate(ranked_products):
        
        if n == 0:
            recommendation = pd.DataFrame(recs, columns=['Product ID', 'Rating', 'Product Name', 'Aisle'])
            return len(recs), recommendation.to_html(index=False, justify='center', classes='table1', border=2)
            
        prod_id, _, prod_name, aisle_name = [*rec]
        
               
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
        product_name = products_desc[products_desc['Product ID'] == product]['Product Name'].iloc[0]
        product_aisle = products_desc[products_desc['Product ID'] == product]['Aisle'].iloc[0]
        list_of_products.append((product, round(new_user_svd.predict(300000, product)[3], 3), product_name, product_aisle))
    
    # order the predictions from highest to lowest rated
    ranked_products = sorted(list_of_products, key=lambda x:x[1], reverse=True)
    
    # return the top n recommendation
    num_results, svd_recs = recommend_diverse_products(ranked_products, n_to_rec, aisle=rec_aisle, percent_diverse=percent_diverse)
    return num_results, svd_recs