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

class BuildReadmeModel(object):
    """
    Uses the readmes from the Github repositories to build a text-based model
    to find the most similar repo to the query repo.
    """

    def __init__(self, dbname='github-db', collection_name='repos-description', doc_type='description'):
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

    def clean_doc(self, doc):
        """
        For each readme:
        1. Converts from unicode to utf-8
        2. Replaces all punctuation with an empty string.
        3. Lowercases the string.
        """

        # html_doc = markdown(doc)
        # text_doc = BeautifulSoup(html_doc).text.encode('utf-8')
        doc = doc.encode('utf-8')
        cleaned_doc = doc.translate(None, punctuation)
        cleaned_doc = cleaned_doc.replace('\n', ' ')\
        .replace('.', ' ').lower()

        # stemmer = SnowballStemmer('english')
        # stemmed_doc = ' '.join([stemmer.stem(word.decode('utf-8')) \
        #     for word in cleaned_doc.split()])
        return cleaned_doc

    def get_imports_from_code(self, code):
        import_pattern1 = 'import \w*\ *'
        import_pattern2 = 'from \w* import'
        patterns = '|'.join([import_pattern1, import_pattern2])
        prog = re.compile(patterns)
        imports = prog.findall(code)
        imported_libraries = list()
        for line in imports:
            return self.get_imports(line)

    def get_imports(self, line):
        lib = line.split()
        if len(lib) < 2:
            return None
        else:
            words = [word for word in query.split() \
            if word not in ['import','from','as']]
            imports = ' '.join(words)\
                        .replace('.', ' ')\
                        .translate(None, punctuation)
            return imports

        
    def suggest_collaborators(self, repo_url):
        collab_finder = FindCollaborators(
        repo_url=repo_url, n_results=3)

        return collab_finder.get_collaborators()

class KMeansModel(BuildReadmeModel):
    def get_readmes(self):
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

        sentences = self.get_readmes()
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

    def get_readmes(self, doc_type="readme"):
        """
        Finds all the non-null descriptions from the MongoDB database
        and stores them in a list.
        """
        # self.repos = list(self.database.find({self.doc_type: \
        #     {"$not": {"$type": 1}}}))
        print "step 1"
        self.repos = list(self.database.find({self.doc_type: \
        {"$exists": True}}))
        print "step 2"
        self.readmes = [repo[self.doc_type] \
        for repo in self.repos]
        print "step 3"

    def build_model(self):
        """
        Turns the descriptions into tfidfs
        """        
        print "step 4"
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
        ipdb.set_trace()

        matching_repos = [self.repos[i] for i in best_fit]
        results = list()
        print "Similar Repos"
        print "================="
        for repo in reversed(matching_repos):
            print repo['name']# + ': ' + repo[self.doc_type]
            print "Users that have contributed here: "
            print self.suggest_collaborators(repo['url'])
            results.append(repo['url'])
        return results


if __name__ == '__main__':


    query = """
    import pygame
    import batma
    from batma.maths.algebra import Vector2
    from batma.core.gameobject import GameObject
    from OpenGL import GL as gl
    from OpenGL import GLU as glu

    import pygame
    import batma
    import weakref
    from batma import gl
    from batma.maths.algebra import Vector2


    """

    query = [word for word in query.split() if word not in ['import','from','as']]
    query = ' '.join(query).replace('.', ' ')

    tfidf_model = TFIDFModel(collection_name='python-repos', doc_type='imports')
    tfidf_model.get_readmes()
    tfidf_model.build_model()
    tfidf_model.make_recommendation(query)

    # doc2vec_model = Doc2VecModel()
    # doc2vec_model.build_model()
    # print doc2vec_model.make_recommendation(query)

    # kmeans_model = KMeansModel()
    # kmeans_model.run_kmeans()


    