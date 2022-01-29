
This program will request cryptocurrency comments from
the reddit api, and assign a score and a tally for each comment that mentions a coin of interest

** Note ** 
See AlgorithmBlogPost for detailed instructions on setting up Reddit API access.

To run, enter `python classifer.py` into command line.
Inside of your .env file... Adjust `n` variable to be desired number of posts to request.

install the virtual environment:

`python -m venv venv`

activate the virtual environment:

`source ./venv/bin/activate`

to leave the virtual environment:

`deactivate`

Once inside virtual environment, use the requirements.txt to install dependencies:

`pip install -r requirements.txt`

If requirements change use the following command to keep `requirements.txt` updated:

`pip freeze > requirements.txt`

