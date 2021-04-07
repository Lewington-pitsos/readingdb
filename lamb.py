import logging

from readingdb.api import API
from readingdb.constants import *
from readingdb.auth import Auth
from botocore.config import Config
from typing import Dict, Any

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

EVENT_NAME = "Name"
EVENT_GET_ROUTE = "GetRoute"



RESPONSE_ERROR = "Error"
RESPONSE_SUCCESS = "Success"

def handler(event: Dict[str, Any], context):
    logger.info('Event: %s', event)

    event_name = event[EVENT_NAME]

    api = API("https://dynamodb.ap-southeast-2.amazonaws.com", config=Config(
        region_name="ap-southeast-2",
    ))


    if event_name == EVENT_GET_ROUTE:
        route_id = event[ReadingRouteKeys.ROUTE_ID]
        route = api.get_route(route_id)

        return {}
    else:
        return {RESPONSE_ERROR: f"Unknown event name {event_name}"}
    


)

    response = {'result': readings}
    return response