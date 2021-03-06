import requests
import ipdb
from base64 import b64decode
import os
import json
import pymongo
import zipfile
import StringIO
import re
from string import punctuation
import ipdb
from mongo import init_mongo


class GithubCodeScraper(object):
    '''
    This class provides the functionality to scrape all the files in a repo
    containing code.
    '''

    def __init__(self, database_name='github-db',
                collection_name='repos-google'):

        '''
        Inits the object with a given MongoDB collection to begin scraping.
        '''

        self.auth = ('viknat', os.environ['GITHUB_ACCESS_TOKEN'])
        self.database = init_mongo(database_name, collection_name)
        import_pattern1 = 'import \w*\ *'
        import_pattern2 = 'from \w* import'
        patterns = '|'.join([import_pattern1, import_pattern2])
        self.prog = re.compile(patterns)

    def scrape_repo_contents(self, repo_url):
        '''
        INPUT: The link to a project's repository.
        OUTPUT: The response from the Github API, the username of the repo,
                the repo name.

        Uses the Github API to recursively obtain all the files in a repo.
        Due to API limits, I recommend using scrape_files instead.
        '''

        split_url = repo_url.split('/')
        username, repo_name = split_url[-2], split_url[-1]
        tree_url = "https://api.github.com/repos/{!s}/{!s}/git/trees/master" \
        .format(username, repo_name)
        payload = {"recursive": 1}
        r = requests.get(tree_url, auth=self.auth, params=payload)
        return r, username, repo_name

    def get_file_contents_api(self, path, username, repo_name):
        '''
        INPUT: The path to a file in a repo, the repo owner's username,
         the repo name
        OUTPUT: The response from the Github API containing the file contents.

        Uses the Github API to get a file's contents.
        '''

        file_url = "https://api.github.com/repos/" + username + '/' \
        + repo_name + '/contents/' + path
        return requests.get(file_url, auth=self.auth)

    def get_files_api(self, repo_url, extension=".py"):
        '''
        INPUT: Link to a repo, a file extension
        OUTPUT: The concatenated contents of all the files 
        with the specified extention.

        Loops through all the files, decodes the contents and concatenates
        them together. 
        Due to Github API limits, I recommend using scrape_files instead.
        '''

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

    def strip_punctuation_lowercase(self, doc):
        '''
        INPUT: A string representing a document.
        OUTPUT: The same string, after:
                - Converting from unicode to string
                - Removing all punctuation
                - Replacing all newline characters with spaces
                - Replacing all periods with spaces
        '''

        doc = doc.encode('utf-8')
        cleaned_doc = doc.translate(None, punctuation)\
                         .replace('\n', ' ')\
                         .replace('.', ' ').lower()
        return cleaned_doc

    def stem_doc(self, doc):
        '''
        Stems each word in the document using a snowball stemmer.
        '''

        stemmer = SnowballStemmer('english')
        stemmed_doc = ' '.join([stemmer.stem(word.decode('utf-8')) \
            for word in cleaned_doc.split()])
        return stemmed_doc

    def get_import_statements_from_code(self, code):
        '''
        INPUT: A string representing all the code of a repository.
        OUTPUT: A string containing all the libraries imported by the repo.
        
        Uses a regular expression to identify all the import statements
        '''

        import_pattern1 = 'import \w*\ *'
        import_pattern2 = 'from \w* import'
        patterns = '|'.join([import_pattern1, import_pattern2])
        prog = re.compile(patterns)
        imports = prog.findall(code)
        for line in imports:
            return self.get_imports(line)

    def get_libraries_from_imports(self, line):
        '''
        INPUT: A line of code representing an import statement.
        OUTPUT: The names of all the libraries and methods in the statement.

        Example:
        Given: from sklearn.feature_extraction.text import TfidfVectorizer
        The output would be "sklearn feature_extraction text TfidfVectorizer"
        '''

        libs = line.split()
        if len(libs) < 2:
            return None
        else:
            excluded = ['import','from','as']
            words = [word for word in libs if word not in excluded]
            imports = ' '.join(words)\
                         .replace('.', ' ')\
                         .translate(None, punctuation)
            return imports

    def scrape_files(self, repo_url, extension=".py"):
        '''
        INPUT: Link to a repo, a file extension
        OUTPUT: The concatenated contents of all the files 
        with the specified extension.

        Does the same thing as get_files_api, but without using
        any Github API calls. 
        '''

        archive_url = repo_url + '/zipball/master'
        print archive_url
        r = requests.get(archive_url, auth=self.auth)
        if r.status_code != 200:
            print "Getting archive failed %s" % str(r.status_code)
            return ""
        else:
            zf = zipfile.ZipFile(StringIO.StringIO(r.content))
        aggregated_imports = ""
        for filename in zf.namelist():
            if filename.endswith(extension):
                aggregated_imports += self._get_file_contents(zf, filename)
        return aggregated_imports

    def _get_file_contents(self, zf, filename):
        '''
        INPUT: A Python zipfile object, a filename within the archive.
        OUTPUT: The import statements within the file.

        Helper method called by scrape_files
        '''

        aggregated_imports = ""
        with zf.open(filename) as f:
            for line in f:
                if self.prog.match(line):
                    imports = self.get_libraries_from_imports(line)
                    if imports is not None:
                        aggregated_imports += (imports + " ")
        return (aggregated_imports + " ")


    def insert_code_into_repos(self):
        '''
        For every repo in the MongoDB database, extracts all the code
        in the repo, uses a regular expression to find all the imports
        and adds them to the database.
        '''

        for i, entry in enumerate(self.database.find().batch_size(30)):
            if "imports" in entry.keys():
                print "Entry %s already updated" % str(i)
                continue
            imports = self.scrape_files(entry['url'])
            if imports != "":
                self.database.update(
                    {'_id': entry['_id']},
                    {"$set": {"imports": imports}}
                    )
                print "Request %s complete" % str(i)
            else:
                print "Empty repo"


if __name__ == '__main__':
    scraper = GithubCodeScraper(collection_name='python-repos')
    scraper.insert_code_into_repos()



