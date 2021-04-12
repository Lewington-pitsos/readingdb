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
SAVE_NEW_ROUTE = "SaveNewRoute"
S3_EVENT_KEY = 'Records'

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

def get_key(event, key):
    err = None

    if not key in event:
        err = key_missing_error_response(key)

    return event[key], err

def decode_s3_event(event):
    records = event["Records"]

    if len(records) != 1:
        raise ValueError(f"expecetd only one record, got {records}")

    try:
        record = records[0]["s3"]

        bucket = record["bucket"]["name"]

        return bucket, record["object"]["key"]
    except Exception as e:
        raise ValueError(f"exception {e} encountered while parsing event {event}")


def handler(event: Dict[str, Any], context):
    logger.info('Event: %s', event)
    
    if EVENT_TYPE in event:
        event_name = event[EVENT_TYPE]
    elif S3_EVENT_KEY in event:
        event_name = SAVE_NEW_ROUTE
    else:
        return error_response("Invalid Event Syntax")

    if not EVENT_ACCESS_TOKEN in event:
        return error_response("Unauthenticated request, no Access Token Provided")

    auth: Auth = Auth(region_name=REGION_NAME)
    
    user_data: AuthResponse = auth.get_user(event[EVENT_ACCESS_TOKEN])
    if not user_data.is_authenticated():
        return error_response(f"Unauthenticated request, unrecognized Access Token {event[EVENT_ACCESS_TOKEN]}")


    if context == "TEST_STUB":
        endpoint = TEST_DYNAMO_ENDPOINT
    else:
        endpoint = DYNAMO_ENDPOINT

    api = API(endpoint, config=Config(
        region_name=REGION_NAME,
    ))

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

    elif event_name == SAVE_NEW_ROUTE:
        try:
            bucket, key = decode_s3_event(event)
        except Exception as e:
            return error_response(e)

        ecs_resp = api.save_new_route(bucket, key)
        return success_response(ecs_resp)

    else:
        return error_response(f"Unrecognized event type {event_name}")
    
