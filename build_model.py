import pymongo
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
import cPickle as pickle
from sklearn.metrics.pairwise import linear_kernel
import numpy as np
from string import punctuation, maketrans
from gensim.models.word2vec import Word2Vec
from gensim.models.doc2vec import Doc2Vec, LabeledSentence
from get_collaborators import FindCollaborators
from markdown2 import markdown
from nltk.stem.snowball import SnowballStemmer
import ipdb
import numpy
from sklearn.cluster import KMeans
import re
from code_scraper import GithubCodeScraper

class BuildRepoModel(object):
    """
    Uses the readmes from the Github repositories to build a text-based model
    to find the most similar repo to the query repo.
    """

    def __init__(self, dbname='github-db', collection_name='python-repos', doc_type='description'):
        """
        Opens a connection to the appropriate MongoDB database
        Or reads from the appropriate filename
        """
        try:
            conn = pymongo.MongoClient()
            print "Connected to MongoDB successfully"
        except pymongo.errors.ConnectionFailure, e:
           print "Could not connect to MongoDB: %s" % e
           sys.exit(0) 

        self.doc_type = doc_type
        db = conn[dbname]
        self.database = db[collection_name]

    def run_model(self, query):
        self.get_docs()
        self.build_model()



class KMeansModel(BuildRepoModel):
    def get_docs(self):
        """
        Finds all the non-null descriptions from the MongoDB database
        and stores them in a list.
        """
        self.repos = list(self.database.find({self.doc_type: \
            {"$not": {"$type": 1}}}))
        self.readmes = [self.clean_doc(repo[self.doc_type]) \
        for repo in self.repos if self.clean_doc(repo[self.doc_type]) is not None]

    def run_kmeans(self):
        kmeans = KMeans()
        self.get_readmes()

        vectorizer = TfidfVectorizer(stop_words='english')

        print "Starting TF-IDFS...."
        tfidfs = vectorizer.fit_transform(self.readmes)
        print "Done TF-IDFS."
        cluster_indices = kmeans.fit_predict(tfidfs)
        for cluster_index in cluster_indices:
            print "Cluster number %s" % str(cluster_index)
            print "======================="
            print '\n'.join(
            [self.repos[i]['name'] + ': ' + self.repos[i]['description'] \
            for i,doc in enumerate(self.readmes) \
             if cluster_indices[i] == cluster_index][:10])


class Doc2VecModel(BuildRepoModel):

    def get_readmes(self):
        repos = list(self.database.find({}, {"name": 1, "readme": 1}))
        print repos[:40]
        names_readmes = [(repo['name'], \
            self.clean_doc(repo['readme'])) for repo in repos]
        for name, readme in names_readmes:
            yield LabeledSentence(words=readme, labels=[name])

    def get_descriptions(self):
        repos = list(self.database.find({}, {"name": 1, "description": 1}))
        names_descs = [(repo['name'], \
            self.clean_doc(repo['description'])) for repo in repos if self.clean_doc(repo['description']) is not None]
        for name, description in names_descs:
            yield LabeledSentence(words=description, labels=[name])


    def get_list_readmes(self):
        repos = list(self.database.find({}, {"readme": 1}))
        sentences = list()
        for name, readme in [(repo['name'], \
        self.clean_doc(repo['readme'])) for repo in repos]:
            #sentences.append(LabeledSentence(words=readme, labels=[name]))
            sentences.append(readme)
        return sentences

    def build_model(self):
        sentences = list()
        # for readme in self.get_readmes():
        #     split_readme = readme.split('.')
        #     list_readme = [sen.split() for sen in split_readme]
        #     sentences.extend(list_readme)

        sentences = self.get_readmes()
        self.model = Doc2Vec(sentences, size=50, train_words=False)
        self.model.build_vocab(sentences)
        self.model.init_sims(replace=True)

    def make_recommendation(self, query):
        query = self.clean_doc(query)
        print query
        query = [word for word in query.split() if word in self.model.vocab]
        print query

        return self.model.most_similar(query)


class BuildTFIDFModel(BuildRepoModel):

    def get_docs(self):
        """
        Finds all the non-null descriptions from the MongoDB database
        and stores them in a list.
        """
        print "Fetching repo metadata..."
        self.repos = list(self.database.find({self.doc_type: \
        {"$exists": True, "$ne": np.nan}}))
        self.docs = [repo[self.doc_type] \
        for repo in self.repos]
        print "Fetched"

    def build_model(self):
        """
        Turns the descriptions into tfidfs
        """        
        print "Initializing vectorizer"
        vectorizer = TfidfVectorizer(stop_words='english')

        print "Starting TF-IDFS...."
        tfidfs = vectorizer.fit_transform(self.docs)
        print "Done TF-IDFS."

        print "Starting pickling of vectorizer"
        with open("vectorizer.pkl","wb") as f:
            pickle.dump(vectorizer, f)

        print "Starting pickling of tfidfs"
        with open("tfidfs.pkl","wb") as f:
            pickle.dump(tfidfs, f)
        self.tfidfs = tfidfs
        self.vectorizer = vectorizer







if __name__ == '__main__':


    query = """https://github.com/astropy/astropy"""

    # query = [word for word in query.split() if word not in ['import','from','as']]
    # query = ' '.join(query).replace('.', ' ')

    tfidf_model = BuildTFIDFModel(collection_name='python-repos', doc_type='imports')
    tfidf_model.get_docs()
    tfidf_model.build_model()
    #query_imports = tfidf_model.fetch_query_repo_data(query)
    #tfidf_model.make_recommendation(query_imports)

    # doc2vec_model = Doc2VecModel()
    # doc2vec_model.build_model()
    # print doc2vec_model.make_recommendation(query)

    # kmeans_model = KMeansModel()
    # kmeans_model.run_kmeans()


    