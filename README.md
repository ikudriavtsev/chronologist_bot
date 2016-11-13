# RESTful backend for the Chronologist Messenger chat bot

Simple backend to communicate with the Facebook ['Chronologist'](https://developers.facebook.com/sa/apps/1601541363492911) application. Uses Python 3.

## Installation

1. Create the python virtual environment: `python3 -m venv /path/to/virtualenv/`
2. Activate it: `source /path/to/virtualenv/bin/activate`
3. Install the dependencies: `pip install -r requirements.txt`

## Run

To run the application execute this command from the source directory:

`CHRONOLOGIST_BACKEND_SETTINGS=dev.cfg python app.py`

## Tests

To run the application's tests use this command:

`python -m unittest discover`

## Deploying to heroku

__Prerequisites__:

1. Download and install the heroku [toolbelt](https://toolbelt.heroku.com/)
2. Run `heroku login` and use the Gmail account credentials, associated with this app
3. Run this: `git remote add heroku https://git.heroku.com/rocky-hollows-30419.git`

__Actual deployment__:

1. Check that local changes work:
    * Run the tests
    * Run `heroku local`
2. Deploy: `git push heroku public_master:master`
