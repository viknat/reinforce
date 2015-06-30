# Reinforce

## The 15-second intro

Got a Github open-source project and need more hands on deck? Visit http://gitforce.org/ and put in the link to your project's source. Reinforce will find people with the most relevant experience.

## The 2-minute intro

Open-source projects are in constant need of more help, whether with bug fixes, documentation or working on a new feature. Without people, projects stagnate. However, it can often be exceptionally difficult to find these people. There are plenty of Github users out there, and you need people with the right experience, especially if the work involves changing core features of the project.

Reinforce does just that. When you provide the link to your project, the app fetches some metadata on your project including its description and the libraries used in its source code. It then scans the database of active Github repos to find the most similar repos to yours. Finally, for each of those similar repos, it finds the most valuable contributors and makes them your recommendations. As such, each of your recommendation results is someone who has done significant work in at least one similar project.

## How it was built

####1. Getting the data

All data was obtained from [Google Big Query](https://bigquery.cloud.google.com/table/publicdata:samples.github_timeline), where the Github timeline is a free public dataset. I extracted all the unique Python repositories with at least two watchers using a SQL query. The limit on the number of watchers was to exclude all low quality repos. Functionality for this part is in scraping.py

####2. Processing the data

All data was stored in a local MongoDB database. The repository description was included with the dataset. I also collected the READMEs for all the repos using the Github API, as well as all the import statements. The latter were collected by downloading the repo as a zipfile (this can be done by appending /zipball/master to the repo URL). Using Python's [zipfile](https://docs.python.org/2/library/zipfile.html) module, I found all the files containing Python code and used a regular expression to extract all the import statements. Functionality for this part is in code_scraper.py.

####3. Model building

I initially tried building a Word2Vec model and then a TF-IDF model on the READMEs, but unfortunately, they were not consistent enough to make good recommendations. I hypothesize that this is because the structure of READMEs is not consistent, some have just installation instructions, for instance. I ended up running TF-IDF on the repo descriptions, as well as the repo import statements, to create two separate models. Functionality for this part is in build_model.py

####4. Recommendations

Step one was to find the repos 
