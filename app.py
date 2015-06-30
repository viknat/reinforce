from flask import Flask, render_template
from flask import request
import cPickle as pickle
import ipdb
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel
from build_model import *
from recommendations import MakeRecommendations


app = Flask(__name__)

# LANDING PAGE
#============================================
@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/recommend_results', methods=['POST'] )
def recommend_users():

    # get data from request form, the key is the name you set in your form
    query = request.form['link']

    # convert data from unicode to string
    query = str(query)


    # results = list()
    # tfidf_model = TFIDFModel(collection_name='python-repos', doc_type='imports')
    # tfidf_model.get_readmes()
    # tfidf_model.build_model()
    # query_imports = tfidf_model.fetch_query_repo_data(query)
    # results = tfidf_model.make_recommendation(query_imports)
    # users = [tfidf_model.suggest_collaborators(repo) for repo in results]

    recommender = MakeRecommendations(query)
    users = recommender.run()
    return render_template('results.html', data=users)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6969, debug=True)
