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
import ipdb
import numpy


class BuildReadmeModel(object):
    """
    Uses the readmes from the Github repositories to build a text-based model
    to find the most similar repo to the query repo.
    """

    def __init__(self):
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

        db = conn['github-db']
        self.database = db['repos-description']

    def clean_doc(self, doc):
        """
        For each readme:
        1. Converts from unicode to utf-8
        2. Replaces all punctuation with an empty string.
        3. Lowercases the string.
        """
        try:
            doc = doc.encode('utf-8')
        except:
            return None
        html_readme = markdown(doc)
        text_readme = BeautifulSoup(html_readme).text
        cleaned_doc = doc.translate(maketrans("", ""), punctuation)
        cleaned_doc = cleaned_doc.replace('\n', ' ')
        return cleaned_doc.lower()

        
    def suggest_collaborators(self):
        collab_finder = FindCollaborators(
        repo_url="https://api.github.com/repos/kennethreitz/requests")

        collab_finder.get_collaborators()

class Doc2VecModel(BuildReadmeModel):

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

        sentences = self.get_descriptions()
        self.model = Doc2Vec(sentences, size=50, train_words=False)
        self.model.build_vocab(sentences)
        self.model.init_sims(replace=True)

    def make_recommendation(self, query):
        query = self.clean_doc(query)
        ipdb.set_trace()
        print query
        query = [word for word in query.split() if word in self.model.vocab]
        print query

        return self.model.most_similar(query)

        


class TFIDFModel(BuildReadmeModel):

    def get_readmes(self):
        """
        Finds all the non-null descriptions from the MongoDB database
        and stores them in a list.
        """
        self.repos = list(self.database.find({"description": \
            {"$not": {"$type": 1}}}))
        self.readmes = [self.clean_doc(repo['description']) \
        for repo in self.repos if self.clean_doc(repo['description']) is not None]

    def build_model(self):
        """
        Turns the descriptions into tfidfs
        """
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

        """
        Finds the top five most similar repos to the query 
        using cosine similarity
        """

        query = self.clean_doc(query)
        vectorized_query = self.vectorizer.transform([query])
        cos_sims = linear_kernel(vectorized_query, self.tfidfs)

        best_fit = np.argsort(cos_sims)[:,-5:][0]
        print query

        matching_repos = [self.repos[i] for i in best_fit]
        print "Similar Repos"
        print "================="
        for repo in reversed(matching_repos):
            print repo['name'] + ': ' + repo['description']




if __name__ == '__main__':


    query = """A 3D graphics engine for gaming"""

    tfidf_model = TFIDFModel()
    tfidf_model.get_readmes()
    tfidf_model.build_model()
    tfidf_model.make_recommendation(query)

    # doc2vec_model = Doc2VecModel()
    # doc2vec_model.build_model()
    # print doc2vec_model.make_recommendation(query)


    