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

    def get_collaborators(self):

        split_url = self.repo_url.split('/')
        username, repo_name = split_url[-2], split_url[-1]
        contributor_url = "https://api.github.com/repos/{!s}/{!s}/contributors"\
        .format(username, repo_name)

        r = requests.get(contributor_url)
        if r.status_code != 200:
            return None
        else:
            return self.find_best_contributors(r.json())


    def find_best_contributors(self, contributors):        
        best_collabs = Counter({
            contributor['html_url']: \
            contributor['contributions'] \
            for contributor in contributors
            })
        return best_collabs.most_common(self.n_results)



    def fetch_user_metadata(self, user):
        user_url = user[0]
        split_url = user_url.split('/')
        username = split_url[-1]
        user_url = "https://api.github.com/users/{!s}"\
        .format(username)

        r = requests.get(user_url, auth=self.auth)
        if r.status_code != 200:
            return None
        else:
            return self.get_required_user_data(user[1], user_url, r.json())


    def get_required_user_data(self, user_contributions, user_url, user_json):
        return {"name": user_json.get('name', user_json['login']),
                "url": user_url,
                "picture": user_json['avatar_url'],
                "related_repo_name": [self.repo_name],
                "related_repo_url": [self.repo_url],
                "n_contributions": [str(user_contributions)],
                "location": user_json.get('location', "Location Unknown")
                }

    def merge_duplicates(self, collaborators):
        new_collabs = list()
        for user in collaborators:
            if user in new_collabs:
                pos = new_collabs.index(d)
                new_collabs[pos]['n_contributions'].append(user['n_contributions'])
                new_collabs[pos]['related_repo_name'].append(user['related_repo_name'])
                new_collabs[pos]['related_repo_url'].append(user['related_repo_url'])
            else:
                new_collabs.append(user)
        return new_collabs

    def create_statements(self, collaborators):
        statements = list()
        for i,collaborator in enumerate(collaborators):
            for repo_url, repo_name, n_contributions in zip(
                collaborator['related_repo_url'], collaborator['related_repo_name'],
                collaborator['n_contributions']):
                statement = "%s contributions to <a href=%s>%s</a><br>" % \
                (n_contributions, repo_url, repo_name)
                statements.append(statement)
            collaborators[i]['statements'] = statements
        return collaborators

    def find(self):
        collaborators = self.get_collaborators()
        collaborators = [self.fetch_user_metadata(user) \
        for user in collaborators if self.fetch_user_metadata(user) is not None]
        return self.create_statements(self.merge_duplicates(collaborators))


if __name__ == '__main__':
    collab_finder = FindCollaborators(
        repo_url="https://api.github.com/repos/mojombo/chronic",
        repo_name="chronic")

    print collab_finder.get_collaborators()

