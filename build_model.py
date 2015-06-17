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


class BuildReadmeModel(object):

    def __init__(self, ):
        try:
            conn = pymongo.MongoClient()
            print "Connected to MongoDB successfully"
        except pymongo.errors.ConnectionFailure, e:
           print "Could not connect to MongoDB: %s" % e
           sys.exit(0) 

        db = conn['github-db']
        self.database = db['repos']

    def clean_doc(self, doc):
        doc = doc.encode('utf-8')
        cleaned_doc = doc.translate(maketrans("", ""), punctuation)
        return cleaned_doc.lower()

    def get_readmes(self):
        repos = list(self.database.find({}, {"readme": 1}))
        self.readmes = [repo['readme'].lower() \
        for repo in repos]

    def get_doc2vec_readmes(self):
        repos = list(self.database.find({}, {"readme": 1}))
        for repo_id, readme in [(repo['_id'], self.clean_doc(repo['readme'])) \
        for repo in repos]:
            yield LabeledSentence(words=readme.split(), labels=repo_id)


    def build_model(self):
        vectorizer = TfidfVectorizer(stop_words='english')

        print "Starting TF-IDFS...."
        tfidfs = vectorizer.fit_transform(self.readmes)
        print "Done TF-IDFS."

        print "Starting pickling of vectorizer"
        with open("vectorizer.pkl","wb") as f:
            pickle.dump(vectorizer, f)

        print "Starting pickling of tfidfs"
        with open("tfidfs.pkl","wb") as f:
            pickle.dump(tfidfs, f)
        self.tfidfs = tfidfs
        self.vectorizer = vectorizer

    def build_doc2vec_model(self):
        sentences = list()
        for readme in self.readmes:
            split_readme = readme.split('.')
            list_readme = [sen.split() for sen in split_readme]
            sentences.extend(list_readme)

        self.model = Word2Vec(sentences, size=50)
        self.model.init_sims(replace=True)

    def make_doc2vec_recommendation(self, query):
        query = [word for word in query.split() if word in self.model.vocab]


        



    def make_recommendation(self, query):

        vectorized_query = self.vectorizer.transform([query])
        cos_sims = linear_kernel(vectorized_query, self.tfidfs)

        best_fit = np.argmax(cos_sims)
        print query

        return self.readmes[best_fit]

    def suggest_collaborators(self):
        collab_finder = FindCollaborators(
        repo_url="https://api.github.com/repos/kennethreitz/requests")

        collab_finder.get_collaborators()


if __name__ == '__main__':
    readme_model = BuildReadmeModel()
    readme_model.get_readmes()
    readme_model.build_model()

    query = """
    HTTP server request URL network internet API request HTTP TCP connection port install

"""
    print readme_model.make_recommendation(query)

    # readme_model.build_doc2vec_model()
    # print readme_model.make_doc2vec_recommendation(query)


    