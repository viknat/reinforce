import requests
import ipdb
from base64 import b64decode
import os
import json
import pymongo

class GithubCodeScraper(object):

    def __init__(self, database_name='github-db', collection_name='repos-google'):
        self.auth = ('viknat', os.environ['GITHUB_ACCESS_TOKEN'])

        try:
            conn = pymongo.MongoClient()
            print "Connected to MongoDB successfully"
        except pymongo.errors.ConnectionFailure, e:
           print "Could not connect to MongoDB: %s" % e
           sys.exit(0) 

        db = conn[database_name]
        self.database = db[collection_name]

    def scrape_repo_contents(self, repo_url):
        split_url = repo_url.split('/')
        username, repo_name = split_url[-2], split_url[-1]
        tree_url = "https://api.github.com/repos/{!s}/{!s}/git/trees/master" \
        .format(username, repo_name)
        payload = {"recursive": 1}

        r = requests.get(tree_url, auth=self.auth, params=payload)

        return r, username, repo_name

    def get_file_contents(self, path, username, repo_name):
        file_url = "https://api.github.com/repos/" + username + '/' \
        + repo_name + '/contents/' + path

        r = requests.get(file_url, auth=self.auth)

        return r



    def get_files(self, repo_url, extension=".py"):
        repo_contents, username, repo_name = self.scrape_repo_contents(repo_url)
        if repo_contents.status_code != 200:
            print "Getting contents failed %s" % str(repo_contents.status_code)
            return ""
        repo_contents = repo_contents.json()['tree']
        file_subset = [doc['path'] for doc in repo_contents \
        if doc['path'].endswith(extension)]

        aggregated_code = ""
        print "%s files to get" % str(len(file_subset))
        for f in file_subset:
            r = self.get_file_contents(f, username, repo_name)

            if r.status_code != 200:
                print "Failed" + str(r.status_code)
                continue
            else:
                code = b64decode(json.loads(r.text)['content'])
                aggregated_code += code 
                aggregated_code += '\n'
        return aggregated_code

    # def get_aggregated_code(self, repo_url):
    #     content_response = self.scrape_repo_contents(repo_url)
    #     if content_response.status_code == 200:
    #         content_paths = content_response.json()
    #         return self.get_files(repo_url)
    #     else:
    #         return None

    def insert_code_into_repos(self):
        for i, entry in enumerate(self.database.find()):
            if "code" in entry:
                print "Entry %s already updated" % str(i)
                continue
            code = self.get_files(entry['url'])
            if code != "":
                self.database.update({
                    '_id': entry['_id']
                    },{
                    "$set": {"code": code}
                    })
                print "Request %s complete" % str(i)


if __name__ == '__main__':
    scraper = GithubCodeScraper(collection_name='python-repos')
    print scraper.insert_code_into_repos()



