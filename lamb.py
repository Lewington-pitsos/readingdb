import logging

from readingdb.api import API
from readingdb.constants import LambdaEvents
from readingdb.cognito import CognitoAuth
from readingdb.auth import Auth
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):


    logger.info('Event: %s', event)
    
    a = Auth("fdsadmin", "CxfgD96VS7xndH", "4uqhqsooe43ebtq0obvn0lm7ui")
    ca = CognitoAuth(a)

    api = API("https://dynamodb.ap-southeast-2.amazonaws.com", ca, config=Config(
        region_name="ap-southeast-2"
    ))

    route_id = event[LambdaEvents.ROUTE_ID]
    readings = api.all_route_readings(route_id)

    logger.info(f"Found {len(readings)} for route {route_id} readings")

    response = {'result': readings}
    return response