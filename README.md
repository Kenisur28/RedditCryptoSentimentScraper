# ML

This program will request n posts from /r/WallStreetBets and associated comments from
the reddit api, and assign a score and a tally for each company that is mentioned.

Companies are determined from pre-made list "companies"

To run, enter `python SentClassifier.py` into command line.
Adjust `n` variable to be desired number of posts to request. File will output a JSON file.
JSON output name can be adjusted on line 96.

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

