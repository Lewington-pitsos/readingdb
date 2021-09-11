## Installation

First install the local [dynamodb server](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.DownloadingAndRunning.html)

Once it is installed, run it with a command like:

    java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb

with the aws cli tool, the local DynamoDB instance can be accessed with the --endpoint-url flag on each command, e.g.:

    aws dynamodb list-tables --endpoint-url http://localhost:8000

Then install [Poetry](https://python-poetry.org/docs/), it's better than virtualenv and way better than anaconda.

Finally start the local dynamodb server on port 8000, and confirm that everything is set up correctly by running unittests (some of which rely on the server running on that port):

    poetry run python -W ignore:unclosed:ResourceWarning -m unittest -c

    [-f/--failfast](https://docs.python.org/3/library/unittest.html#cmdoption-unittest-f) option can be used to have it stop running at the first failure/error
    [-c/--catch](https://docs.python.org/3/library/unittest.html#cmdoption-unittest-c) should be used for graceful exits when exiting with ctrl-c
        Be warned however, a second ctrl-c will still cause an immediate exit
    [-W](https://docs.python.org/3.8/using/cmdline.html#cmdoption-w) allows some options for error handling:
        In this case we ignore unclosed socket warnings as boto3 was causing them to be thrown likely due to the way that it handles connection pooling.
        They have the form: 
            ResourceWarning: unclosed <socket.socket fd=1, family=AddressFamily.AF_INET, type=2049, proto=6, laddr=[local address], raddr=[remote address]>

Then you can start running scripts, e.g.:

    poetry run python at.py