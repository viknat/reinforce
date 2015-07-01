import pymongo
import numpy
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
import cPickle as pickle
from sklearn.metrics.pairwise import linear_kernel
import numpy as np
from string import punctuation, maketrans
from gensim.models.word2vec import Word2Vec
from gensim.models.doc2vec import Doc2Vec, LabeledSentence
from get_collaborators import FindCollaborators
from nltk.stem.snowball import SnowballStemmer
from sklearn.cluster import KMeans
import re
from code_scraper import GithubCodeScraper
from mongo import init_mongo

class BuildRepoModel(object):
    """
    Uses the readmes from the Github repositories to build a text-based model
    to find the most similar repo to the query repo.
    """

    def __init__(self, dbname='github-db', collection_name='python-repos', \
                doc_type='description'):
        """
        Opens a connection to the appropriate MongoDB database
        doc_type can be one of 'description', 'readme' or 'imports'
        The model will be built on the relevant document.
        """
        self.database = init_mongo(dbname, collection_name)

    def run_model(self, query):
        self.get_docs()
        self.build_model()

class BuildTFIDFModel(BuildRepoModel):

    def get_docs(self):
        """
        Finds all the non-null descriptions/imports from the MongoDB 
        database and stores them in a list.
        """
        print "Fetching repo metadata..."
        self.repos = list(self.database.find({self.doc_type: \
        {"$exists": True, "$ne": np.nan}}))
        self.docs = [repo[self.doc_type] \
        for repo in self.repos]
        print "Fetched"

    def build_model(self):
        """
        Turns the descriptions/imports into tfidfs and pickles them.
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



class KMeansModel(BuildRepoModel):
    '''
    KMeans clustering was tested but did not produce good clusters.
    '''

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
    '''
    I built and tested this Doc2Vec model but it did not produce results
    as good as those produced by TFIDF. I recommend the use of TFIDFS instead
    unless Doc2Vec can somehow be tuned to perform better.
    '''

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
        '''
        A Labeled Sentence consists of a sentence labeled by its document name/
        Doc2Vec needs these.
        '''
        repos = list(self.database.find({}, {"readme": 1}))
        sentences = list()
        for name, readme in [(repo['name'], \
        self.clean_doc(repo['readme'])) for repo in repos]:
            sentences.append(readme)
        return sentences

    def build_model(self):
        sentences = list()
        sentences = self.get_readmes()
        self.model = Doc2Vec(sentences, size=50, train_words=False)
        self.model.build_vocab(sentences)
        self.model.init_sims(replace=True)

    def make_recommendation(self, query):
        query = self.clean_doc(query)
        query = [word for word in query.split() if word in self.model.vocab]
        return self.model.most_similar(query)


if __name__ == '__main__':
    query = """https://github.com/astropy/astropy"""
    tfidf_model = BuildTFIDFModel(collection_name='python-repos', doc_type='imports')
    tfidf_model.get_docs()
    tfidf_model.build_model()


    