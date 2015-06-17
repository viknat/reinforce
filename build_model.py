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


if __name__ == '__main__':
    readme_model = BuildReadmeModel()
    readme_model.get_readmes()
    readme_model.build_model()

    query = """Note: We're using Kramdown Markdown extensions, such as definition lists.

JSON Responses

We specify the JSON responses in Ruby so that we don't have to write them by hand all over the docs. You can render the JSON for a resource like this:

<%= json :issue %>
This looks up GitHub::Resources::ISSUE in lib/resources.rb.

Some actions return arrays. You can modify the JSON by passing a block:

<%= json(:issue) { |hash| [hash] } %>
Terminal blocks

You can specify terminal blocks with pre.terminal elements. (It'd be nice if Markdown could do this more cleanly.)

<pre class="terminal">
$ curl foobar
....
</pre>
This is not a curl tutorial though. Not every API call needs to show how to access it with curl.

Development

Nanoc compiles the site into static files living in ./output. It's smart enough not to try to compile unchanged files:

$ bundle exec nanoc compile
Loading site data...
Compiling site...
   identical  [0.00s]  output/css/960.css
   identical  [0.00s]  output/css/pygments.css
   identical  [0.00s]  output/css/reset.css
   identical  [0.00s]  output/css/styles.css
   identical  [0.00s]  output/css/uv_active4d.css
      update  [0.28s]  output/index.html
      update  [1.31s]  output/v3/gists/comments/index.html
      update  [1.92s]  output/v3/gists/index.html
      update  [0.25s]  output/v3/issues/comments/index.html
      update  [0.99s]  output/v3/issues/labels/index.html
      update  [0.49s]  output/v3/issues/milestones/index.html
      update  [0.50s]  output/v3/issues/index.html
      update  [0.05s]  output/v3/index.html

Site compiled in 5.81s.
You can setup whatever you want to view the files. If using the adsf gem (as listed in the Gemfile), you can start Webrick:

$ bundle exec nanoc view
$ open http://localhost:3000
Compilation times got you down? Use autocompile!

$ bundle exec nanoc autocompile
This starts a web server too, so there's no need to run nanoc view. One thing: remember to add trailing slashes to all nanoc links!

Deploy

$ bundle exec rake publish

"""
    print readme_model.make_recommendation(query)

    readme_model.build_doc2vec_model()
    print readme_model.make_doc2vec_recommendation(query)


    