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
    """
    Uses the readmes from the Github repositories to build a text-based model
    to find the most similar repo to the query repo.
    """

    def __init__(self, ):
        """
        Opens a connection to the appropriate MongoDB database
        """
        try:
            conn = pymongo.MongoClient()
            print "Connected to MongoDB successfully"
        except pymongo.errors.ConnectionFailure, e:
           print "Could not connect to MongoDB: %s" % e
           sys.exit(0) 

        db = conn['github-db']
        self.database = db['repos']

    def clean_doc(self, doc):
        """
        For each readme:
        1. Converts from unicode to utf-8
        2. Replaces all punctuation with an empty string.
        3. Lowercases the string.
        """
        doc = doc.encode('utf-8')
        cleaned_doc = doc.translate(maketrans("", ""), punctuation)
        return cleaned_doc.lower()

        
    def suggest_collaborators(self):
        collab_finder = FindCollaborators(
        repo_url="https://api.github.com/repos/kennethreitz/requests")

        collab_finder.get_collaborators()

class Doc2VecModel(BuildReadmeModel):

    def get_readmes(self):
        repos = list(self.database.find({}, {"full_name": 1, "readme": 1}))
        for name, readme in [(repo['full_name'], \
        self.clean_doc(repo['readme'])) for repo in repos]:
            yield LabeledSentence(words=readme, labels=[name])

    def build_model(self):
        sentences = list()
        # for readme in self.get_readmes():
        #     split_readme = readme.split('.')
        #     list_readme = [sen.split() for sen in split_readme]
        #     sentences.extend(list_readme)

        self.model = Doc2Vec(self.get_readmes(), size=50)
        self.model.init_sims(replace=True)

    def make_recommendation(self, query):
        query = [word for word in query.split() if word in self.model.vocab]
        feature_vector = sum([self.model[word] for word in query])

        return self.model.most_similar(query)

        


class TFIDFModel(BuildReadmeModel):
    def get_readmes(self):
        repos = list(self.database.find({}, {"readme": 1}))
        self.readmes = [repo['readme'].lower() \
        for repo in repos]

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

    def make_recommendation(self, query):

        vectorized_query = self.vectorizer.transform([query])
        cos_sims = linear_kernel(vectorized_query, self.tfidfs)

        best_fit = np.argmax(cos_sims)
        print query

        return self.readmes[best_fit]


if __name__ == '__main__':
    # readme_model = BuildReadmeModel()
    # readme_model.get_readmes()
    # readme_model.build_model()

    query = """
    Text based classifier TFIDF or word 2 vec natural language processing text

"""
    #print readme_model.make_recommendation(query)

    doc2vec_model = Doc2VecModel()
    doc2vec_model.build_model()
    print doc2vec_model.make_recommendation(query)


    