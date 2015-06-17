import sys
import pymongo
import requests
from base64 import b64decode
from bs4 import BeautifulSoup
from requests_oauthlib import OAuth1
import os

class GithubScraper(object):

    def __init__(self, collection_name, n_requests=10, database_name='github-db'):

        self.n_requests = n_requests
        try:
            conn = pymongo.MongoClient()
            print "Connected to MongoDB successfully"
        except pymongo.errors.ConnectionFailure, e:
           print "Could not connect to MongoDB: %s" % e
           sys.exit(0) 

        db = conn[database_name]
        self.database = db[collection_name]
        # self.auth = ('e72cbb68c4eb3d42600a', \
        #     'a356cbb4c05e82290f33e7a8713e0dd40ab02a0b')
        self.auth = ('viknat', os.environ['GITHUB_ACCESS_TOKEN'])

    def get_readme(self, api_url):
        split_url = api_url.split('/')
        username, repo_name = split_url[-2], split_url[-1]
        repo_url = "https://github.com/{!s}/{!s}".format(username, repo_name)

        r = requests.get(repo_url, auth=self.auth)
        soup = BeautifulSoup(r.text)

        readme = soup.find_all(class_ = "markdown-body entry-content")[0].text

        return readme

    def get_readme_api(self, api_url):
        split_url = api_url.split('/')
        username, repo_name = split_url[-2], split_url[-1]
        readme_url = "https://api.github.com/repos/{!s}/{!s}/readme" \
        .format(username, repo_name)

        r = requests.get(readme_url, auth=self.auth)

        json_obj = r.json()

        try:
            return b64decode(json_obj['content'])
        except KeyError:
            return None


    def insert_into_mongo(self, response):
        json_repos = response.json()
        for repo in json_repos:
            #readme = self.get_readme(repo['url'])
            readme = self.get_readme_api(repo['url'])
            if readme is None:
                continue
            repo['readme'] = readme
            self.database.insert(repo)

    def insert_user_into_mongo(self, response):
        json_users = response.json()
        for user in json_users:
            keep_fields = ["url", "repos_url"]
            to_insert = {field: user[field] for field in keep_fields}
            self.database.insert(to_insert)



    def scrape_github_repos(self, url_type='users'):
        for since_param in range(self.n_requests):
            url = 'https://api.github.com/{!s}'\
            .format(url_type)

            payload = {"since": since_param}
            r = requests.get(url, auth=self.auth, params=payload)
            if r.status_code != 200:
                print "Error %s in handling request" % str(r.status_code)
            else:
                self.insert_into_mongo(r)
                print "Request %s complete" % str(since_param)


if __name__ == '__main__':
    # user_scraper = GithubScraper(collection_name='users')
    # user_scraper.scrape_github_repos(url_type='users')

    repo_scraper = GithubScraper(collection_name='repos')
    repo_scraper.scrape_github_repos(url_type='repositories')

