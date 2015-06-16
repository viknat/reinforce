import pymongo
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
import cPickle as pickle
from sklearn.metrics.pairwise import linear_kernel
import numpy as np
from string import punctuation, maketrans
from gensim.models.word2vec import Word2Vec
from gensim.models.doc2vec import Doc2Vec, LabeledSentence


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


if __name__ == '__main__':
    readme_model = BuildReadmeModel()
    readme_model.get_readmes()
    readme_model.build_model()

    query = """You didn't write that awful page. You're just trying to get some data out of it. Beautiful Soup is here to help. Since 2004, it's been saving programmers hours or days of work on quick-turnaround screen scraping projects.

Beautiful Soup

"A tremendous boon." -- Python411 Podcast

[ Download | Documentation | Hall of Fame | Source | Discussion group ]

If Beautiful Soup has saved you a lot of time and money, the best way to pay me back is to check out Constellation Games, my sci-fi novel about alien video games.
You can read the first two chapters for free, and the full novel starts at 5 USD. Thanks!
If you have questions, send them to the discussion group. If you find a bug, file it.

Beautiful Soup is a Python library designed for quick turnaround projects like screen-scraping. Three features make it powerful:

Beautiful Soup provides a few simple methods and Pythonic idioms for navigating, searching, and modifying a parse tree: a toolkit for dissecting a document and extracting what you need. It doesn't take much code to write an application
Beautiful Soup automatically converts incoming documents to Unicode and outgoing documents to UTF-8. You don't have to think about encodings, unless the document doesn't specify an encoding and Beautiful Soup can't detect one. Then you just have to specify the original encoding.
Beautiful Soup sits on top of popular Python parsers like lxml and html5lib, allowing you to try out different parsing strategies or trade speed for flexibility.
Beautiful Soup parses anything you give it, and does the tree traversal stuff for you. You can tell it "Find all the links", or "Find all the links of class externalLink", or "Find all the links whose urls match "foo.com", or "Find the table heading that's got bold text, then give me that text."

Valuable data that was once locked up in poorly-designed websites is now within your reach. Projects that would have taken hours take only minutes with Beautiful Soup.

Interested? Read more.

Download Beautiful Soup

The current release is Beautiful Soup 4.3.2 (October 2, 2013). You can install it with pip install beautifulsoup4 or easy_install beautifulsoup4. It's also available as the python-beautifulsoup4 package in recent versions of Debian, Ubuntu, and Fedora .

Beautiful Soup 4 works on both Python 2 (2.6+) and Python 3.

Beautiful Soup is licensed under the MIT license, so you can also download the tarball, drop the bs4/ directory into almost any Python application (or into your library path) and start using it immediately. (If you want to do this under Python 3, you will need to manually convert the code using 2to3.)

Beautiful Soup 3

Beautiful Soup 3 was the official release line of Beautiful Soup from May 2006 to March 2012. It is considered stable, and only critical bugs will be fixed. Here's the Beautiful Soup 3 documentation.

Beautiful Soup 3 works only under Python 2.x. It is licensed under the same license as Python itself.

The current release of Beautiful Soup 3 is 3.2.1 (February 16, 2012). You can install Beautiful Soup 3 with pip install BeautifulSoup or easy_install BeautifulSoup. It's also available as python-beautifulsoup in Debian and Ubuntu, and as python-BeautifulSoup in Fedora.

You can also download the tarball and use BeautifulSoup.py in your project directly.

Hall of Fame

Over the years, Beautiful Soup has been used in hundreds of different projects. There's no way I can list them all, but I do want to highlight a few high-profile projects. Beautiful Soup isn't what makes these projects interesting, but it did make their completion easier:

"Movable Type", a work of digital art on display in the lobby of the New York Times building, uses Beautiful Soup to scrape news feeds.
Reddit uses Beautiful Soup to parse a page that's been linked to and find a representative image.
Alexander Harrowell uses Beautiful Soup to track the business activities of an arms merchant.
The developers of Python itself used Beautiful Soup to migrate the Python bug tracker from Sourceforge to Roundup.
The Lawrence Journal-World uses Beautiful Soup to gather statewide election results.
The NOAA's Forecast Applications Branch uses Beautiful Soup in TopoGrabber, a script for downloading "high resolution USGS datasets."
If you've used Beautiful Soup in a project you'd like me to know about, please do send email to me or the discussion group.

Development

Development happens at Launchpad. You can get the source code or file bugs.

"""
    print readme_model.make_recommendation(query)

    readme_model.build_doc2vec_model()
    print readme_model.make_doc2vec_recommendation(query)


    