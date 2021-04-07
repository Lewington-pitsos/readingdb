import logging

from readingdb.api import API
from readingdb.constants import *
from readingdb.auth import Auth
from botocore.config import Config
from typing import Dict, Any

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

EVENT_TYPE = "Type"
EVENT_GET_ROUTE = "GetRoute"

RESPONSE_STATUS_KEY = "Status"
RESPONSE_BODY_KEY = "Status"

RESPONSE_ERROR = "Error"
RESPONSE_SUCCESS = "Success"

def error_response(body: Any) -> Dict[str, Any]:
    return response(body, False)

def success_response(body: Any) -> Dict[str, Any]:
    return response(body, True)

def response(body: Any, success: bool) -> Dict[str, Any]:
    if success:
        resp = {RESPONSE_STATUS_KEY: RESPONSE_SUCCESS}
    else:
        resp = {RESPONSE_STATUS_KEY: RESPONSE_ERROR}

    resp[RESPONSE_BODY_KEY] = body
    return resp

def handler(event: Dict[str, Any], context):
    logger.info('Event: %s', event)

    event_name = event[EVENT_TYPE]

    api = API("https://dynamodb.ap-southeast-2.amazonaws.com", config=Config(
        region_name="ap-southeast-2",
    ))

    if event_name == EVENT_GET_ROUTE:
        route_id = event[ReadingRouteKeys.ROUTE_ID]
        route = api.get_route(route_id)

        return success_response(route)
    else:
        return error_response(f"Unrecognized event type {event_name}")
    
