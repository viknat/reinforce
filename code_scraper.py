import requests

class GithubCodeScraper(object):

    def __init__():
        pass

def scrape_code(url):
    split_url = url.split('/')
    username, repo_name = split_url[-2], split_url[-1]
    tree_url = "https://api.github.com/repos/{!s}/{!s}/git/trees/master" \
    .format(username, repo_name)
    payload = {"recursive": 1}

    r = requests.get(tree_url, params=payload)

    if r.status_code != 200:
        return "Failed request"
    else:
        return r.json()