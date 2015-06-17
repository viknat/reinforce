import requests
import os
from collections import Counter

class FindCollaborators(object):

    def __init__(self, repo_url, n_results=3):
        self.repo_url = repo_url
        self.auth = ('viknat', os.environ['GITHUB_ACCESS_TOKEN'])

    def get_collaborators(self):
        pull_url = self.repo_url + "/pulls"
        payload = {"state": "closed"}
        r = requests.get(pull_url, auth=self.auth, params=payload)

        self.pullees = r.json()
        best_collabs = Counter([pullee['user']['html_url'] for pullee in self.pullees])
        return best_collabs.most_common(3)

if __name__ == '__main__':
    collab_finder = FindCollaborators(
        repo_url="https://api.github.com/repos/macournoyer/thin")

    print collab_finder.get_collaborators()

