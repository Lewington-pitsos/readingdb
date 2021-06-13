import logging
from typing import Dict, Any

from botocore.config import Config

from readingdb.api import API
from readingdb.constants import *
from readingdb.auth import Auth
from readingdb.endpoints import BUCKET, DYNAMO_ENDPOINT, TEST_BUCKET, TEST_DYNAMO_ENDPOINT
from readingdb.authresponse import AuthResponse

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)

# Generic Event Keys
EVENT_TYPE = 'Type'
EVENT_ACCESS_TOKEN = 'AccessToken'
EVENT_PREDICTIONS = 'Predictions'
EVENT_ANNOTATOR_PREFERENCE = 'AnnotatorPreference'
EVENT_PREDICTION_ONLY = 'PredictionOnly'

# Event Types
EVENT_GET_ROUTE = 'GetRoute'
EVENT_DELETE_ROUTE = 'DeleteRoute'
EVENT_GET_USER_ROUTES = 'GetUserRoutes'
EVENT_GET_READINGS = 'GetReadings'
EVENT_GET_PAGINATED_READINGS = 'GetPaginatedReadings'
EVENT_GET_READINGS_ASYNC = 'GetReadingsAsync'
EVENT_UPDATE_ROUTE_NAME = 'UpdateRouteName'
EVENT_UPLOAD_NEW_ROUTE = 'NotifyUploadComplete'
EVENT_SAVE_PREDICTIONS = 'SavePredictions'
EVENT_BUCKET_KEY = 'BucketKey'
EVENT_ADD_USER = 'AddUser'

# Generic Response Keys
RESPONSE_STATUS_KEY = 'Status'
RESPONSE_BODY_KEY = 'Body'

# Response Statuses
RESPONSE_ERROR = 'Error'
RESPONSE_SUCCESS = 'Success'

# Event Keys
EVENT_BUCKET = 'Bucket'
EVENT_OBJECT_KEY = 'Key'
EVENT_ROUTE_NAME = 'RouteName'

def key_missing_error_response(key):
    return error_response(f'Bad Format Error: key {key} missing from event')

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
    if not key in event:
        return None, key_missing_error_response(key)

    return event[key], None
    
def handler(event: Dict[str, Any], context):
    if context == 'TEST_STUB':
        endpoint = TEST_DYNAMO_ENDPOINT
        bucket = TEST_BUCKET
    else:
        endpoint = DYNAMO_ENDPOINT
        bucket = BUCKET

    api = API(
        endpoint, 
        size_limit=0, 
        bucket=bucket, 
        tmp_bucket=bucket, 
        config=Config(
            region_name=REGION_NAME,
        )
    )

    logger.info('Event: %s', event)
    
    if EVENT_TYPE in event:
        event_name = event[EVENT_TYPE]
    else:
        return error_response('Invalid Event Syntax')

    if not EVENT_ACCESS_TOKEN in event:
        return error_response('Unauthenticated request, no Access Token Provided')

    auth: Auth = Auth(region_name=REGION_NAME)
    
    user_data: AuthResponse = auth.get_user(event[EVENT_ACCESS_TOKEN])
    if not user_data.is_authenticated():
        return error_response(f'Unauthenticated request, unrecognized Access Token {event[EVENT_ACCESS_TOKEN]}')

    #  ------------ Per-Event-Type handling -------------
    
    if event_name == EVENT_GET_ROUTE:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp

        route = api.get_route(route_id, user_data.user_sub)
        return success_response(route)

    if event_name == EVENT_DELETE_ROUTE:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp

        api.delete_route(route_id, user_data.user_sub)
        return success_response('')

    if event_name == EVENT_GET_USER_ROUTES:
        routes = api.routes_for_user(user_data.user_sub)
        return success_response(routes)

    elif event_name == EVENT_GET_READINGS:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp

        if EVENT_BUCKET_KEY in event:
            key = event[EVENT_BUCKET_KEY]
        else:
            key = None

        readings = api.all_route_readings(route_id, key)

        return success_response(readings)

    elif event_name == EVENT_GET_PAGINATED_READINGS:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp

        route = api.get_route(route_id, user_data.user_sub)

        if route is None:
            return success_response(None)

        pagination_key, missing = get_key(event, Database.PAGINATION_KEY_NAME)
        if missing:
            pagination_key = None

        annotator_preference, missing = get_key(event, EVENT_ANNOTATOR_PREFERENCE)
        if missing:
            annotator_preference = [DEFAULT_ANNOTATOR_ID]

        pred_only, missing = get_key(event, EVENT_PREDICTION_ONLY)
        if missing:
            pred_only = True

        readings, pagination_key = api.paginated_route_readings(
            route_id,
            last_key=pagination_key,
            predictions_only=pred_only,
            annotator_preference=annotator_preference, 
        )

        return success_response({
            Database.READING_TABLE_NAME: readings,
            Database.PAGINATION_KEY_NAME: pagination_key,
        })

    elif event_name == EVENT_GET_READINGS_ASYNC:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp

        access_token, err_resp = get_key(event, EVENT_ACCESS_TOKEN)
        if err_resp:
            return err_resp

        s3_uri = api.all_route_readings_async(route_id, access_token)
        return success_response(s3_uri)

    elif event_name == EVENT_UPLOAD_NEW_ROUTE:
        bucket, err_resp = get_key(event, EVENT_BUCKET)
        if err_resp:
            return err_resp
        key, err_resp = get_key(event, EVENT_OBJECT_KEY)
        if err_resp:
            return err_resp

        routeName = event[EVENT_ROUTE_NAME] if EVENT_ROUTE_NAME in event else None

        readings = api.save_new_route(bucket, key, routeName)
        return success_response(readings)

    elif event_name == EVENT_SAVE_PREDICTIONS:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp
        user_id, err_resp = get_key(event, RouteKeys.USER_ID)
        if err_resp:
            return err_resp
        readings, err_resp = get_key(event, EVENT_PREDICTIONS)
        if err_resp:
            return err_resp

        readings = api.save_predictions(
            readings, 
            route_id,
            user_id,
            save_imgs=True
        )
        return success_response(readings)

    elif event_name == EVENT_UPDATE_ROUTE_NAME:
        route_id, err_resp = get_key(event, ReadingRouteKeys.ROUTE_ID)
        if err_resp:
            return err_resp 
        name, err_resp = get_key(event, RouteKeys.NAME)
        if err_resp:
            return err_resp 

        api.update_route_name(route_id, user_data.user_sub, name)

        return success_response(None)

    elif event_name == EVENT_ADD_USER:
        user_id, err_resp = get_key(event, UserKeys.USER_ID)
        if err_resp:
            return err_resp 

        if len(user_id) < 20:
            return error_response(f'User ID {user_id} was too short, must be at least 20 characters long')

        data_access_groups, not_found = get_key(event, UserKeys.DATA_ACCESS_GROUPS)

        if not_found:
            saved_access_groups = api.save_user(user_id)
        else:
            saved_access_groups = api.save_user(user_id, data_access_groups)

        if not saved_access_groups:
            return error_response(f'User ID {user_id} has already been registered')

        return success_response({
            UserKeys.DATA_ACCESS_GROUPS: saved_access_groups
        })
    else:
        return error_response(f'Unrecognized event type {event_name}')
    
