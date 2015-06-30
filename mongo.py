import sys
import pymongo   

def init_mongo(database_name, collection_name):
    try:
        conn = pymongo.MongoClient()
        print "Connected to MongoDB successfully"
    except pymongo.errors.ConnectionFailure, e:
       print "Could not connect to MongoDB: %s" % e
       sys.exit(0) 

    db = conn[database_name]
    database = db[collection_name]