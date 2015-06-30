# Reinforce: Find Your Team

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

Step one was to find the repos that were most similar to the query repo. I did this by computing cosine similarity between the query and the repos in my dataset, and finding the top 10 most similar repos. Once the app has that, it obtains the most valuable contributors for each of these repos. I apply a bonus for collaborators that have contributed to more than one repo, and display these people on my results page. Functionality for this part is in recommendations.py and get_collaborators.py

####5. Web app

My app was deployed using Flask and Bootstrap. Check out the static and templates folders for the design elements, and my_app.py for the Flask functionality.

## Validation

As an unsupervised problem, it is difficult to validate or quantify the results with any sort of metric. The best way to measure its success is using some sort of experimental framework, i.e. performing an A/B test on how many of the recommended users who get contacted end up making a contribution to that repo. Do contact me if you want to discuss this further.

## Next steps

* Extend functionality to all programming languages (currently works only for Python). This wouldn't be too difficult to do, all that would have to be done would be to write a new regex to grab the imports for each programming langauge and then re-run the scraper and code scraper.

* Graph theory applications. It's not too hard to see that the collaborators and repos together form a directed graph. It would be interesting to explore various applications of that, for example, detecting communities of users who have similar interests.

## Credits

* [Github](https://github.com/) and their incredibly rich [API](https://developer.github.com/v3/). The source of all the data.

* [Google Big Query](https://bigquery.cloud.google.com/table/publicdata:samples.github_timeline) and their publicly available Github dataset. Processes terabytes of data in seconds, and uses the familiar SQL syntax.

* Python's excellent [Requests](http://docs.python-requests.org/en/latest/) module. An convenient, high-level abstraction of urllib3. I used it extensively for scraping purposes.

* [Scikit-learn](http://scikit-learn.org/stable/) and [NLTK](http://www.nltk.org/) for natural language processing and model building.

* [Flask](http://flask.pocoo.org/) and [Bootstrap](http://getbootstrap.com/) for developing my app (back-end and front-end respectively)

* [Galvanize](http://www.galvanize.com/courses/data-science/)'s data science program, for which this was my capstone project.

## License

This project is licensed under the terms of the MIT license.

