import logging
from readingdb.authresponse import AuthResponse

from readingdb.api import API
from readingdb.constants import *
from readingdb.auth import Auth
from botocore.config import Config
from typing import Dict, Any

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

# Generic Event Keys
EVENT_TYPE = "Type"
EVENT_ACCESS_TOKEN = "AccessToken"

# Event Types
EVENT_GET_ROUTE = "GetRoute"
EVENT_GET_READINGS = "GetReadings"

# Generic Response Keys
RESPONSE_STATUS_KEY = "Status"
RESPONSE_BODY_KEY = "Body"

# Response Statuses
RESPONSE_ERROR = "Error"
RESPONSE_SUCCESS = "Success"

# MISC constants
REGION_NAME = "ap-southeast-2"

def key_missing_error_response(key):
    return error_response(f"Bad Format Error: key {key} missing from event")

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

    if not EVENT_TYPE in event:
        return error_response("Invalid Event Syntax")

    event_name = event[EVENT_TYPE]

    if not EVENT_ACCESS_TOKEN in event:
        return error_response("Unauthenticated request, no Access Token Provided")

    auth: Auth = Auth(region_name=REGION_NAME)
    
    user_data: AuthResponse = auth.get_user(event[EVENT_ACCESS_TOKEN])
    if not user_data.is_authenticated():
        return error_response(f"Unauthenticated request, unrecognized Access Token {event[EVENT_ACCESS_TOKEN]}")

    api = API("https://dynamodb.ap-southeast-2.amazonaws.com", config=Config(
        region_name=REGION_NAME,
    ))

    #  ------------ Per-Event-Type handling -------------

    if event_name == EVENT_GET_ROUTE:
        if not ReadingRouteKeys.ROUTE_ID in event:
            return key_missing_error_response(ReadingRouteKeys.ROUTE_ID)

        route_id = event[ReadingRouteKeys.ROUTE_ID]
        user_id = user_data.user_sub
        route = api.get_route(route_id, user_id)
        return success_response(route)

    elif event_name == EVENT_GET_READINGS:
        if not ReadingRouteKeys.ROUTE_ID in event:
            return key_missing_error_response(ReadingRouteKeys.ROUTE_ID) 

        route_id = event[ReadingRouteKeys.ROUTE_ID]
        readings = api.all_route_readings(route_id)

        return success_response(readings)

    else:
        return error_response(f"Unrecognized event type {event_name}")
    
