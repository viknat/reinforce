import sys
import pymongo
import requests
from bs4 import BeautifulSoup

class GithubScraper(object):

    def __init__(self, n_requests=10):

        self.n_requests = n_requests
        try:
            conn = pymongo.MongoClient()
            print "Connected to MongoDB successfully"
        except pymongo.errors.ConnectionFailure, e:
           print "Could not connect to MongoDB: %s" % e
           sys.exit(0) 

        db = conn['github-db']
        self.database = db['repos']

    def get_readme(self, api_url):
        split_url = api_url.split('/')
        username, repo_name = split_url[-2], split_url[-1]
        repo_url = "https://github.com/{!s}/{!s}".format(username, repo_name)

        r = requests.get(repo_url)
        soup = BeautifulSoup(r.text)

        readme = soup.find_all(class_ = "markdown-body entry-content")[0].text

        return readme

    def insert_into_mongo(self, response):
        json_repos = response.json()
        for repo in json_repos:
            try:
                readme = self.get_readme(repo['url'])
                repo['readme'] = readme
            except:
                repo['readme'] = None
            self.database.insert(repo)


    def scrape_github_repos(self):
        for since_param in range(self.n_requests):
            url = 'https://api.github.com/repositories?since=%s' % since_param
            r = requests.get(url)
            if r.status_code != 200:
                print "Error %s in handling request" % str(r.status_code)
            else:
                self.insert_into_mongo(r)
                print "Request %s complete" % str(since_param)


if __name__ == '__main__':
    scraper = GithubScraper()
    scraper.scrape_github_repos()

