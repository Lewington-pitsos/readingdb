import logging
from readingdb.clean import encode_bool
from typing import Dict, Any

from botocore.config import Config

from readingdb.api import API
from readingdb.constants import *
from readingdb.auth import Auth
from readingdb.endpoints import DYNAMO_ENDPOINT, TEST_DYNAMO_ENDPOINT
from readingdb.authresponse import AuthResponse

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

# Generic Event Keys
EVENT_TYPE = "Type"
EVENT_ACCESS_TOKEN = "AccessToken"

# Event Types
EVENT_GET_ROUTE = "GetRoute"
EVENT_GET_USER_ROUTES = "GetUserRoutes"
EVENT_GET_READINGS = "GetReadings"
EVENT_UPDATE_ROUTE_NAME = "UpdateRouteName"
EVENT_UPLOAD_NEW_ROUTE = 'NotifyUploadComplete'

# Generic Response Keys
RESPONSE_STATUS_KEY = "Status"
RESPONSE_BODY_KEY = "Body"

# Response Statuses
RESPONSE_ERROR = "Error"
RESPONSE_SUCCESS = "Success"

# Event Keys
EVENT_BUCKET = "Bucket"
EVENT_OBJECT_KEY = "Key"

def key_missing_error_response(key):
    return error_response(f"Bad Format Error: key {key} missing from event")

def error_response(body: Any) -> Dict[str, Any]:
    logger.info('Error response: %s', body)
    return response(body, False)

def success_response(body: Any) -> Dict[str, Any]:
    logger.info('Success response: %s', body)
    return response(body, True)

def response(body: Any, success: bool) -> Dict[str, Any]:
    if success:
        resp = {RESPONSE_STATUS_KEY: RESPONSE_SUCCESS}
    else:
        resp = {RESPONSE_STATUS_KEY: RESPONSE_ERROR}

    resp[RESPONSE_BODY_KEY] = body
    return resp

def get_key(event, key):
    err = None

    if not key in event:
        return None, key_missing_error_response(key)

    return event[key], None
    
def handler(event: Dict[str, Any], context):
    if context == "TEST_STUB":
        endpoint = TEST_DYNAMO_ENDPOINT
    else:
        endpoint = DYNAMO_ENDPOINT

    api = API(endpoint, size_limit=640000, config=Config(
        region_name=REGION_NAME,
    ))

    logger.info('Event: %s', event)
    
    if EVENT_TYPE in event:
        event_name = event[EVENT_TYPE]
    else:
        return error_response("Invalid Event Syntax")

    if not EVENT_ACCESS_TOKEN in event:
        return error_response("Unauthenticated request, no Access Token Provided")

    auth: Auth = Auth(region_name=REGION_NAME)
    
    user_data: AuthResponse = auth.get_user(event[EVENT_ACCESS_TOKEN])
    if not user_data.is_authenticated():
        return error_response(f"Unauthenticated request, unrecognized Access Token {event[EVENT_ACCESS_TOKEN]}")

    #  ------------ Per-Event-Type handling -------------
    
    if event_name == EVENT_GET_ROUTE:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp

        route = api.get_route(route_id, user_data.user_sub)
        return success_response(route)

    if event_name == EVENT_GET_USER_ROUTES:
        routes = api.routes_for_user(user_data.user_sub)
        return success_response(routes)

    elif event_name == EVENT_GET_READINGS:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp

        route_id = event[ReadingRouteKeys.ROUTE_ID]
        readings = api.all_route_readings(route_id)

        return success_response(readings)

    elif event_name == EVENT_UPLOAD_NEW_ROUTE:
        bucket, err_resp = get_key(event, EVENT_BUCKET)
        if err_resp:
            return err_resp
        key, err_resp = get_key(event, EVENT_OBJECT_KEY)
        if err_resp:
            return err_resp

        readings = api.save_new_route(bucket, key)

        return success_response(readings)

    elif event_name == EVENT_UPDATE_ROUTE_NAME:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp 
        name, err_resp = get_key(event, RouteKeys.NAME)
        if err_resp:
            return err_resp 

        route_id = event[ReadingRouteKeys.ROUTE_ID]
        api.update_route_name(route_id, user_data.user_sub, name)

        return success_response(None)

    else:
        return error_response(f"Unrecognized event type {event_name}")
    
