## Installation

First install the local [dynamodb server](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html)

Then install [Pipenv](https://realpython.com/pipenv-guide/), it's better than virtualenv and way better than anaconda.

Finally start the local dynamodb server on port 8000, and confirm that everything is set up correctly by running unittests (some of which rely on the server running on that port):

    python -m unittest discover

Then you can start running scripts, e.g.:

    python maketable.py

## API

The API can be found at `readingdb/readingdb.py`