import sys
import pymongo
import requests
from bs4 import BeautifulSoup

try:
    conn = pymongo.MongoClient()
    print "Connected to MongoDB successfully"
except pymongo.errors.ConnectionFailure, e:
   print "Could not connect to MongoDB: %s" % e
   sys.exit(0) 

db = conn['github-dump']
repos = db['repos']

with open('data/dump/github/repos.bson') as f:
    for i,line in enumerate(f):
        repos.insert(line)
        if i % 100 == 0:
            print "Request no. %s done" % str(i)
        if i == 1000:
            break