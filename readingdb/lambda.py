import logging

from readingdb.api import API

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info('Event: %s', event)

    api = API("https://dynamodb.ap-southeast-2.amazonaws.com")

    api.

    
    logger.info('Calculated result of %s', result)

    response = {'result': result}
    return response