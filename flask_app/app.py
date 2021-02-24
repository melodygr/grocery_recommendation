from flask import Flask, request, render_template
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.snowball import SnowballStemmer
from user_functions import *
import pandas as pd
import numpy as np
import pickle

app = Flask(__name__)

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
    nlp0_id = ''
    nlp0_name = ''
    if request.method == 'POST' and 'searchwords' in request.form:
        nlp = stem_and_vectorize_products_based_on_metadata(request.form.get('searchwords'))
        if type(nlp) == NoneType:
            nlp=0
        else:    
            item_count = len(nlp)
            nlp0_id = nlp.index[0]
            nlp0_name = nlp.iloc[0]    
    return render_template('nlp.html',
                           nlp=nlp, 
                           nlp0_id=nlp0_id, 
                           nlp0_name=nlp0_name)    
                        

app.run()