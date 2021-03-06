import cPickle as pickle   
import sys
from code_scraper import GithubCodeScraper
import pymongo
import numpy as np
from sklearn.metrics.pairwise import linear_kernel
from get_collaborators import FindCollaborators
from mongo import init_mongo


class MakeRecommendations(object):
    '''
    This class is initialized with the URL provided by the user.
    It provides the functionality to find similar repos and return
    the list of relevant contributors.
    '''

    def __init__(self, query_url, doc_type='imports', dbname='github-db', \
                collection_name='python-repos'):
        self.query_url = query_url
        self.database = init_mongo(database_name, collection_name)

    def load_models(self):
        '''
        Loads the TF-IDF matrix and vectorizer from pickled format
        '''

        with open('tfidfs.pkl', 'rb') as f:
            self.tfidfs = pickle.load(f)
        with open('vectorizer.pkl') as f:
            self.vectorizer = pickle.load(f)

    def fetch_query_repo_data(self):
        '''
        Fetches metadata on the query repo using the Github API.
        '''

        scraper = GithubCodeScraper()
        self.imports = scraper.scrape_files(self.query_url)

    def find_similar_repos(self):
        '''
        Using cosine similarity, finds the 10 most similar repos.
        Creates a new class variable matching_repos.
        '''
        self.repos = list(self.database.find({self.doc_type: \
        {"$exists": True, "$ne": np.nan}}))
        vectorized_query = self.vectorizer.transform([self.imports])
        cos_sims = linear_kernel(vectorized_query, self.tfidfs)
        best_fit = np.argsort(cos_sims)[:,-10:][0]
        self.matching_repos = [self.repos[i] for i in best_fit]
        

    def suggest_collaborators(self, repo):
        '''
        Instantiates the FindCollaborators class with one of the related 
        repository's URL. Returns metadata on the repostory.
        '''

        collab_finder = FindCollaborators(
        repo_name=repo[0], repo_url=repo[1], n_results=1)

        users = collab_finder.get_collaborators()
        if users is None:
            return None
        else:
            return [collab_finder.fetch_user_metadata(user) for user in users \
                if user is not None]

    def display_results(self, display=False):
        '''
        Displays the metadata for each of the recommended results
        on the command line if display is True.
        Returns a list of json objects, where each json object corresponds to
        metadata on one of the users recommended.
        '''
        
        if display:
            print "Similar Repos"
            print "================="
        results = list()
        for i,repo in enumerate(reversed(self.matching_repos)):
            if display:
                print repo['name']# + ': ' + repo[self.doc_type]
                print "Users that have contributed here: "
                print self.suggest_collaborators((repo['name'], repo['url']))
            results.append(self.suggest_collaborators((repo['name'], repo['url'])))
        return results

    def run(self):
        self.load_models()
        self.fetch_query_repo_data()
        self.find_similar_repos()
        results = self.display_results()
        return [result[0] for result in results if result is not None]

if __name__ == '__main__':
    query_url = "https://github.com/astropy/astropy" # Example
    recommender = MakeRecommendations(query_url)
    print recommender.run()