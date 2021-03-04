from flask import Flask, request, render_template, session
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.snowball import SnowballStemmer
from user_functions import stem_and_vectorize_products_based_on_metadata, generate_new_user_recommendations, generate_recs, get_sample_product
import pandas as pd
import numpy as np
import pickle

app = Flask(__name__)
app.secret_key = 'any random string'

@app.route('/', methods=['GET', 'POST'])
def rootpage():
    return render_template('index.html')

@app.route('/nlp', methods=['GET', 'POST'])
def nlppage():
    nlp = ''
    num_results = 0
    if request.method == 'POST' and 'searchwords' in request.form:
        num_results, nlp = stem_and_vectorize_products_based_on_metadata(request.form.get('searchwords')) 
    return render_template('nlp.html',
                           nlp=nlp, 
                           num_results=num_results)

@app.route('/svd', methods=['GET', 'POST'])
def svdpage():
    svd_recs = ''
    num_results = 0
    session['n_left_to_rate'] = None
    if request.method == 'POST' and 'num_to_rate' in request.form:
        session['rate_aisle'] = request.form.get('rate_aisle')
        session['n_to_rate'] = float(request.form.get('num_to_rate'))
        session['rec_aisle'] = request.form.get('rec_aisle')
        session['n_to_rec'] = float(request.form.get('num_to_rec'))
        session['percent_diverse'] = float(request.form.get('diversity_index'))
        session['prod_name'], session['prod_aisle'], session['prod_id'] = get_sample_product(session['rate_aisle'])
        session['n_left_to_rate'] = session['n_to_rate'] -1
        session['ratings_list'] = []
        return render_template('rating.html')
    else:
        return render_template('svd.html',
                            svd_recs=svd_recs,
                            num_results=num_results)                                                                                                                   
                        
@app.route('/rating', methods=['GET', 'POST'])
def ratingpage():
    if session['n_to_rate'] == None:
        return render_template('svd.html',
                                svd_recs='',
                                num_results=0)     
    
    if session['n_left_to_rate'] == 0:
        num_results, svd_recs = generate_recs(session['ratings_list'], session['n_to_rec'], session['percent_diverse'], rec_aisle=session['rec_aisle'])
        return render_template('svd.html',
                                svd_recs=svd_recs,
                                num_results=num_results)
    elif 'rate_product' in request.form:
        rating = float(request.form.get('rate_product'))
        session['ratings_list'].append([session['prod_id'], rating])
        session['n_left_to_rate'] -= 1
        session['prod_name'], session['prod_aisle'], session['prod_id'] = get_sample_product(session['rate_aisle'])
        return render_template('rating.html')
    else:
        return render_template('rating.html')    


if __name__ == "__main__":
    app.run(debug=True)