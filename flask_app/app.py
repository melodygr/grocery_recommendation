from flask import Flask, request, render_template
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.snowball import SnowballStemmer
from user_functions import stem_and_vectorize_products_based_on_metadata, generate_new_user_recommendations
import pandas as pd
import numpy as np
import pickle

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def rootpage():
    return render_template('index.html')


@app.route('/nlp', methods=['GET', 'POST'])
def nlppage():
    nlp = ''
    num_results = ''
    if request.method == 'POST' and 'searchwords' in request.form:
        num_results, nlp = stem_and_vectorize_products_based_on_metadata(request.form.get('searchwords'))
    if nlp is None:
        nlp = 0    
    return render_template('nlp.html',
                           nlp=nlp, 
                           num_results=num_results)

@app.route('/svd', methods=['GET', 'POST'])
def svdpage():
    svd_recs = ''
    num_results = ''
    if request.method == 'POST' and 'num_to_rate' in request.form:
        rate_aisle = request.form.get('rate_aisle')
        n_to_rate = float(request.form.get('num_to_rate'))
        rec_aisle = request.form.get('rec_aisle')
        n_to_rec = float(request.form.get('num_to_rec'))
        percent_diverse = float(request.form.get('diversity_index'))
        num_results, svd_recs = generate_new_user_recommendations(n_to_rate, n_to_rec, percent_diverse, rate_aisle=rate_aisle, rec_aisle=rec_aisle)
    return render_template('svd.html',
                            svd_recs=svd_recs,
                            num_results=num_results)                              
                        

if __name__ == "__main__":
    app.run(debug=True)