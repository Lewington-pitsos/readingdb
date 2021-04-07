import logging

from readingdb.api import API
from readingdb.constants import LambdaEvents
from readingdb.auth import Auth
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info('Event: %s', event)

    api = API("https://dynamodb.ap-southeast-2.amazonaws.com", config=Config(
        region_name="ap-southeast-2",
    ))

    route_id = event[LambdaEvents.ROUTE_ID]
    readings = api.all_route_readings(route_id)

    logger.info(f"Found {len(readings)} for route {route_id} readings")
    logger.info(f"First Reading: {readings[0]}")

    response = {'result': readings}
    return response