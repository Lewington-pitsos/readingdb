## Installation

First install the local [dynamodb server](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html)

Then install [Poetry](https://python-poetry.org/docs/), it's better than virtualenv and way better than anaconda.

Finally start the local dynamodb server on port 8000, and confirm that everything is set up correctly by running unittests (some of which rely on the server running on that port):

    poetry run python -m unittest discover

Then you can start running scripts, e.g.:

    poetry run python at.py