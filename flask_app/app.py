from flask import Flask, request, render_template
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.snowball import SnowballStemmer
from user_functions import stem_and_vectorize_products_based_on_metadata
import pandas as pd
import numpy as np
import pickle

app = Flask(__name__)
app.config['DEBUG'] = True

@app.route('/', methods=['GET', 'POST'])
def rootpage():
    name = ''
    if request.method == 'POST' and 'username' in request.form:
        name = request.form.get('username')
    return render_template('index.html',
                            name=name)

def calc_bmi(weight, height):
    return round((weight/height/height)*703, 2)  

@app.route('/bmi', methods=['GET', 'POST'])
def bmipage():
    bmi = ''
    if request.method == 'POST' and 'userheight' in request.form:
        height = float(request.form.get('userheight'))
        weight = float(request.form.get('userweight'))
        bmi = calc_bmi(weight, height)
    return render_template('bmi.html',
                            bmi=bmi)
                         

@app.route('/nlp', methods=['GET', 'POST'])
def nlppage():
    nlp = ''
    if request.method == 'POST' and 'searchwords' in request.form:
        nlp = stem_and_vectorize_products_based_on_metadata(request.form.get('searchwords'))
        print(type(nlp))
        print(type(nlp[0])
        print(type(nlp).shape())
        if type(nlp)().shape == None:
            nlp=0
    return render_template('nlp.html',
                           nlp=nlp, 
                           num_results=len(nlp)) 

@app.route('/svd', methods=['GET', 'POST'])
def svdpage():
    svd = ''
    # if request.method == 'POST' and 'userheight' in request.form:
        # height = float(request.form.get('userheight'))
        # weight = float(request.form.get('userweight'))
        # svd = generate_new_user_recommendations(n_to_rate, n_to_rec, percent_diverse, rate_aisle=None, rec_aisle=None)
    return render_template('svd.html',
                            svd=svd)                              
                        

app.run()