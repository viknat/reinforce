import sys
import requests
from bs4 import BeautifulSoup

def scrape_github_repos():
    results = list()
    for since_param in range(10):
        url = 'https://api.github.com/repositories?since=%s' % since_param
        try:
            r = requests.get(url)
        except:
            print "Bad request" 
            print sys.exc_info()[0]

        if r.status_code != 200:
            print "Error in handling request"
        else:
            results.append(r)
        print "Request %s complete" % str(since_param)
    return results

results = scrape_github_repos()
print results[0]

