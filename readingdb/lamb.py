import logging
from readingdb.geolocator import Geolocator
from readingdb.digester import Digester
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
EVENT_BUCKET = 'Bucket'
EVENT_OBJECT_KEY = 'Key'
EVENT_ROUTE_NAME = 'RouteName'
EVENT_POINTS = 'Points'

# Event Types -----------------------------------------------------

EVENT_UPLOAD_NEW_ROUTE = 'NotifyUploadComplete'
EVENT_PROCESS_UPLOADED_ROUTE = 'ProcessUpload'
EVENT_SAVE_PREDICTIONS = 'SavePredictions'
EVENT_BUCKET_KEY = 'BucketKey'
EVENT_ROAD_SNAP = 'SnapToRoads'

# User Permission Events
EVENT_GET_ROUTE = 'GetRoute'
EVENT_DELETE_ROUTE = 'DeleteRoute'
EVENT_GET_USER_ROUTES = 'GetUserRoutes'
EVENT_GET_READINGS = 'GetReadings'
EVENT_UPDATE_ROUTE_NAME = 'UpdateRouteName'

# Admin Permission Events
EVENT_ADD_USER = 'AddUser'
EVENT_ADD_ORG = 'AddOrg'

# End Event Types ---------------------------------------------------

# Generic Response Keys
RESPONSE_STATUS_KEY = 'Status'
RESPONSE_BODY_KEY = 'Body'
RESPONSE_SAVED_READINGS = 'SavedReadings'

# Response Statuses
RESPONSE_ERROR = 'Error'
RESPONSE_SUCCESS = 'Success'

def key_missing_error_response(key):
    return error_response(f'Bad Format Error: key {key} missing from event')

def unauthorized_route_response(user_id, route_id):
    return error_response(f'User {user_id} cannot access route {route_id}')

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
    return handler_request(event, context, DYNAMO_ENDPOINT, BUCKET, 2_400_000)

def test_handler(
    event: Dict[str, Any], 
    context,  
    endpoint: str=TEST_DYNAMO_ENDPOINT, 
    bucket: str=TEST_BUCKET,
    size_limit: int=25_000_000
):
    return handler_request(event, context, endpoint, bucket, size_limit)
    
def handler_request(
    event: Dict[str, Any], 
    context, endpoint: str, 
    bucket: str, 
    size_limit: int
    ):

    logger.info('Event: %s', event)

    if EVENT_TYPE in event:
        event_name = event[EVENT_TYPE]
    else:
        return error_response('Invalid Event Syntax')

    if not EVENT_ACCESS_TOKEN in event:
        return error_response('Unauthenticated request, no Access Token Provided')

    api = API(
        endpoint, 
        size_limit=size_limit, 
        bucket=bucket, 
        tmp_bucket=bucket, 
        config=Config(
            region_name=REGION_NAME,
        )
    )
    geolocator = Geolocator()
    digester = Digester(endpoint, api=api)
    
    auth: Auth = Auth(region_name=REGION_NAME)
    
    user_data: AuthResponse = auth.get_user(event[EVENT_ACCESS_TOKEN])
    if not user_data.is_authenticated():
        return error_response(f'Unauthenticated request, unrecognized Access Token {event[EVENT_ACCESS_TOKEN]}')

    #  ------------ Per-Event-Type handling -------------
    if event_name == EVENT_GET_ROUTE:
        route_id, err_resp = get_key(event, Constants.ROUTE_ID)
        if err_resp:
            return err_resp

        route = api.get_route(route_id)
        if route is None:
            return error_response(f'Route {route_id} does not exist')

        if not api.can_access_route(user_data.user_sub, route_id):
            return unauthorized_route_response(user_data.user_sub, route_id)

        return success_response(route)

    if event_name == EVENT_DELETE_ROUTE:
        route_id, err_resp = get_key(event, Constants.ROUTE_ID)
        if err_resp:
            return err_resp

        if not api.can_access_route(user_data.user_sub, route_id):
            return unauthorized_route_response(user_data.user_sub, route_id)

        api.delete_route(route_id)
        return success_response('')

    if event_name == EVENT_GET_USER_ROUTES:
        routes = api.routes_for_user(user_data.user_sub)
        return success_response(routes)

    elif event_name == EVENT_GET_READINGS:

        route_id, missing_route_id = get_key(event, Constants.ROUTE_ID)
        geohashes, missing_geohash = get_key(event, Constants.GEOHASH)

        if missing_route_id and missing_geohash:
            return error_response(f'Bad Format Error: event {EVENT_GET_READINGS} requires one of {Constants.ROUTE_ID}, {Constants.GEOHASH}')
        elif not missing_route_id and not missing_geohash:
            return error_response(f'Bad Format Error: event {EVENT_GET_READINGS} cannot be specified with both {Constants.ROUTE_ID} AND {Constants.GEOHASH}')
        elif not missing_geohash:
            if isinstance(geohashes, list):
                if len(geohashes) == 0:
                    return error_response(f'Value Error: event {EVENT_GET_READINGS} cannot be passed empty {Constants.GEOHASH} list')
                elif not all(isinstance(elem, str) for elem in geohashes):
                    return error_response(f'Type Error: event GetReadings by {Constants.GEOHASH} must pass a string or list of strings')
            elif not isinstance(geohashes,str):
                return error_response(f'Type Error: event GetReadings by {Constants.GEOHASH} must pass a string or list of strings')

            readings = api.get_geohash_readings_by_user(geohashes, user_data.user_sub)

            return success_response({Constants.READING_TABLE_NAME: readings})
        elif not missing_route_id:
            pred_only, missing = get_key(event, EVENT_PREDICTION_ONLY)
            if missing:
                pred_only = True

            if not api.can_access_route(user_data.user_sub, route_id):
                return unauthorized_route_response(user_data.user_sub, route_id)

            if EVENT_BUCKET_KEY in event:
                key = event[EVENT_BUCKET_KEY]
            else:
                key = None

            annotator_preference, missing = get_key(event, EVENT_ANNOTATOR_PREFERENCE)
            if missing:
                annotator_preference = ANNOTATOR_PREFERENCE
            else:
                annotator_preference += ANNOTATOR_PREFERENCE

            readings = api.all_route_readings(
                route_id,
                key,
                predictions_only=pred_only,
                annotator_preference=annotator_preference
            )

            return success_response({Constants.READING_TABLE_NAME: readings})
        
    elif event_name == EVENT_PROCESS_UPLOADED_ROUTE:
        # Event Format:
        # Type: 'ProcessUpload',
        # AccessToken: the access token obtained from cognito,
        # Bucket: the name of the bucket where the files are uploaded to,
        # Key: the common prefix shared by all the uploaded route files,
        # RouteName (optional): the name we wish to save as the name for the newly created route
        # See the test_integrates_uploaded_files test in test_lambda.py
        # for details.
        #
        # Returns Format:
        # Status: 'Success' | 'Error'
        # Body: {
        #   'RouteID': The id of the route that was just created
        # } 
        # 
        # File Format
        # All Files must be sitting in the same bucket directory (i.e. 
        # the common prefix, which is the value of the Key field in the
        # Event Format), with no subdirectories permitted. 
        #
        # All image files must be named according to
        #       img_<ts>-<num>.jpg
        # e.g   img_1621394116949-64.jpg
        # ts: the unix timestamp in UTC milliseconds of when the file was saved
        # num: can be any integer value. Originally its purpose was to provide a 
        # guarentee of filename uniqueness.
        # 
        # The GPS readings must be stored in GPS.txt
        #
        # Currently any additional files will be ignored.

        bucket, err_resp = get_key(event, EVENT_BUCKET)
        if err_resp:
            return err_resp
        key, err_resp = get_key(event, EVENT_OBJECT_KEY)
        if err_resp:
            return err_resp
  
        group_id, err_resp = get_key(event, Constants.GROUP_ID)
        if err_resp:
            return err_resp

        name, missing = get_key(event, EVENT_ROUTE_NAME)
        if missing:
            name = None
        
        route = digester.process_upload(
            user_id=user_data.user_sub,
            group_id=group_id,
            key=key,
            bucket=bucket,
            name=name,
            snap_to_roads=True,
        )

        return success_response({Constants.ROUTE_ID: route.id})

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
        route_id, err_resp = get_key(event, Constants.ROUTE_ID)
        if err_resp:
            return err_resp
        readings, err_resp = get_key(event, EVENT_PREDICTIONS)
        if err_resp:
            return err_resp

        api.save_predictions(
            readings, 
            route_id,
            user_data.user_sub,
            save_imgs=True
        )
        return success_response({RESPONSE_SAVED_READINGS: readings})

    elif event_name == EVENT_UPDATE_ROUTE_NAME:
        route_id, err_resp = get_key(event, Constants.ROUTE_ID)
        if err_resp:
            return err_resp 
        name, err_resp = get_key(event, Constants.NAME)
        if err_resp:
            return err_resp 

        if not api.can_access_route(user_data.user_sub, route_id):
            return unauthorized_route_response(user_data.user_sub, route_id)

        api.update_route_name(route_id, name)

        return success_response(None)

    elif event_name == EVENT_ADD_USER:
        user_id, err_resp = get_key(event, Constants.USER_ID)
        if err_resp:
            return err_resp

        if len(user_id) < 20:
            return error_response(f'User ID {user_id} was too short, must be at least 20 characters long')

        org_name, err_resp = get_key(event, Constants.ORG_NAME)
        if err_resp:
            return err_resp

        data_access_groups, not_found = get_key(event, Constants.GROUPS)

        if not_found:
            api.save_user(org_name, user_id)
        else:
            api.save_user(org_name, user_id, data_access_groups)
        return success_response(None)
    
    elif event_name == EVENT_ADD_ORG:
        org_name, err_resp = get_key(event, Constants.ORG_NAME)
        if err_resp:
            return err_resp

        existing_org = api.get_org(org_name)

        if existing_org is not None:
            return error_response(f'Org {org_name} already exists')

        org = api.put_org(org_name)

        return success_response(org)

    elif event_name == EVENT_ROAD_SNAP:
        points, err_resp = get_key(event, EVENT_POINTS)
        if err_resp:
            return err_resp

        if len(points) < 2:
            return error_response(f'Not Enough Points Given ({len(points)})')

        return success_response({
            EVENT_POINTS: geolocator.geolocate(points, replacement=True)
        })

    else:
        return error_response(f'Unrecognized event type {event_name}')
    
