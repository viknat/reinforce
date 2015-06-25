import requests
import os
from collections import Counter
import ipdb

class FindCollaborators(object):

    def __init__(self, repo_url, repo_name, n_results=3):
        self.repo_url = repo_url
        self.repo_name = repo_name
        self.n_results = n_results
        self.auth = ('viknat', os.environ['GITHUB_ACCESS_TOKEN'])

    def make_request(self, url, payload={}):
        r = requests.get(url, auth=self.auth, params=payload)
        return r


    def get_collaborators(self):

        split_url = self.repo_url.split('/')
        username, repo_name = split_url[-2], split_url[-1]
        repo_url = "https://api.github.com/repos/{!s}/{!s}"\
        .format(username, repo_name)

        contributor_url = repo_url + "/contributors"        

        r = self.make_request(contributor_url)
        if r.status_code != 200:
            print "This repo has moved or is no longer available"
            return None
        else:
            self.contributors = r.json()
            best_collabs = Counter({
                contributor['html_url']: \
                contributor['contributions'] \
                for contributor in self.contributors
                })
            return best_collabs.most_common(self.n_results)

    def fetch_user_metadata(self, user):
        user_url = user[0]
        split_url = user_url.split('/')
        username = split_url[-1]
        user_url = "https://api.github.com/users/{!s}"\
        .format(username)
        print user_url

        r = self.make_request(user_url)
        if r.status_code != 200:
            print "This user's data could not be retrieved"
            return user_url
        else:
            results = r.json()
            try:
                name = results['name']
            except KeyError:
                name = results['login']

            return {"name": name,
                    "url": user_url,
                    "picture": results['avatar_url'],
                    "related_repo_name": self.repo_name,
                    "related_repo_url": self.repo_url,
                    "n_contributions": user[1],
                    "location": results['location']
                    }

    def run(self):
        return self.get_collaborators()



if __name__ == '__main__':
    collab_finder = FindCollaborators(
        repo_url="https://api.github.com/repos/mojombo/chronic")

    print collab_finder.get_collaborators()

