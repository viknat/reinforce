from flask import Flask, render_template
from flask import request
import cPickle as pickle
import ipdb
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel
from build_model import *


app = Flask(__name__)

# OUR HOME PAGE
#============================================
@app.route('/')
def welcome():
    myname = "Vikram"
    return render_template('index.html', data=myname)

# My word counter app
#==============================================
# create the page the form goes to
@app.route('/recommend_results', methods=['POST'] )
def recommend_users():

    # get data from request form, the key is the name you set in your form
    query = request.form['link']

    # convert data from unicode to string
    query = str(query)

    # run classifier

    results = list()
    tfidf_model = TFIDFModel()
    results = tfidf_model.run_model(query)

    # #return result['title'] + ', ' + result['author'] + "         " + result['summary']
    return render_template('index2.html', data=query)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6969, debug=True)
