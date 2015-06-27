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
    tfidf_model = TFIDFModel(collection_name='python-repos-more', doc_type='imports')
    tfidf_model.get_readmes()
    tfidf_model.build_model()
    query_imports = tfidf_model.fetch_query_repo_data(query)
    results = tfidf_model.make_recommendation(query_imports)
    users = [tfidf_model.suggest_collaborators(repo) for repo in results]
    users = [user[0] for user in users if user is not None]

    # #return result['title'] + ', ' + result['author'] + "         " + result['summary']
    return render_template('results.html', data=users)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6969, debug=True)
