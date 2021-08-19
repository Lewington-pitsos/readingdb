import logging
from readingdb.geolocator import Geolocator
from readingdb.digester import Digester
from typing import Dict, Any

from readingdb.constants import *

logger = logging.getLogger('main')
logger.setLevel(logging.INFO)

# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -------------------------- helpers ------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------

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
        resp = {LambdaConstants.RESPONSE_STATUS_KEY: LambdaConstants.RESPONSE_SUCCESS}
    else:
        resp = {LambdaConstants.RESPONSE_STATUS_KEY: LambdaConstants.RESPONSE_ERROR}

    resp[LambdaConstants.RESPONSE_BODY_KEY] = body
    return resp

def get_key(event, key):
    if not key in event:
        return None, key_missing_error_response(key)

    return event[key], None

def arg_check(*args,**kwargs_to_check):
    outputs = []
    for a in args:
        if a in kwargs_to_check:
            outputs.append(kwargs_to_check[a])
        else:
            raise ValueError(f'"{a}" object not passed from EventHandler event_setup function')

    return outputs

# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# ---------------------- Event Functions --------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------

def get_route(event: Dict[str,Any], **kwargs):
    route_id, err_resp = get_key(event, Constants.ROUTE_ID)
    if err_resp:
        return err_resp

    api, user_data = arg_check('api', 'user_data', **kwargs)

    route = api.get_route(route_id)
    if route is None:
        return error_response(f'Route {route_id} does not exist')

    if not api.can_access_route(user_data.user_sub, route_id):
        return unauthorized_route_response(user_data.user_sub, route_id)

    return success_response(route)

def delete_route(event: Dict[str,Any], **kwargs): 
    route_id, err_resp = get_key(event, Constants.ROUTE_ID)
    if err_resp:
        return err_resp

    api, user_data = arg_check('api', 'user_data', **kwargs)

    if not api.can_access_route(user_data.user_sub, route_id):
        return unauthorized_route_response(user_data.user_sub, route_id)

    api.delete_route(route_id)
    return success_response('')

def get_user_routes(event, **kwargs):
    api, user_data = arg_check('api', 'user_data', **kwargs)
    routes = api.routes_for_user(user_data.user_sub)
    return success_response(routes)

def get_user_layers(event, **kwargs):
    return success_response('oop')

def get_readings(event, **kwargs):
    route_id, missing_route_id = get_key(event, Constants.ROUTE_ID)
    geohashes, missing_geohash = get_key(event, Constants.GEOHASH)

    api, user_data = arg_check('api', 'user_data', **kwargs)

    if missing_route_id and missing_geohash:
        return error_response(f'Bad Format Error: event {LambdaConstants.EVENT_GET_READINGS} requires one of {Constants.ROUTE_ID}, {Constants.GEOHASH}')
    elif not missing_route_id and not missing_geohash:
        return error_response(f'Bad Format Error: event {LambdaConstants.EVENT_GET_READINGS} cannot be specified with both {Constants.ROUTE_ID} AND {Constants.GEOHASH}')
    elif not missing_geohash:
        if isinstance(geohashes, list):
            if len(geohashes) == 0:
                return error_response(f'Value Error: event {LambdaConstants.EVENT_GET_READINGS} cannot be passed empty {Constants.GEOHASH} list')
            elif not all(isinstance(elem, str) for elem in geohashes):
                return error_response(f'Type Error: event GetReadings by {Constants.GEOHASH} must pass a string or list of strings')
        elif not isinstance(geohashes,str):
            return error_response(f'Type Error: event GetReadings by {Constants.GEOHASH} must pass a string or list of strings')

        readings = api.get_geohash_readings_by_user(geohashes, user_data.user_sub)

        return success_response({Constants.READING_NAME: readings})
    elif not missing_route_id:
        pred_only, missing = get_key(event, LambdaConstants.EVENT_PREDICTION_ONLY)
        if missing:
            pred_only = True

        if not api.can_access_route(user_data.user_sub, route_id):
            return unauthorized_route_response(user_data.user_sub, route_id)

        if LambdaConstants.EVENT_BUCKET_KEY in event:
            key = event[LambdaConstants.EVENT_BUCKET_KEY]
        else:
            key = None

        annotator_preference, missing = get_key(event, LambdaConstants.EVENT_ANNOTATOR_PREFERENCE)
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

        return success_response({Constants.READING_NAME: readings})
        
def process_uploaded_route(event, **kwargs):
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

    bucket, err_resp = get_key(event, LambdaConstants.EVENT_BUCKET)
    if err_resp:
        return err_resp
    key, err_resp = get_key(event, LambdaConstants.EVENT_OBJECT_KEY)
    if err_resp:
        return err_resp

    group_id, err_resp = get_key(event, Constants.GROUP_ID)
    if err_resp:
        return err_resp

    name, missing = get_key(event, LambdaConstants.EVENT_ROUTE_NAME)
    if missing:
        name = None

    api, user_data = arg_check('api', 'user_data', **kwargs)
    
    digester = Digester('no url',api=api)
    route = digester.process_upload(
        user_id=user_data.user_sub,
        group_id=group_id,
        key=key,
        bucket=bucket,
        name=name,
        snap_to_roads=True,
    )

    return success_response({Constants.ROUTE_ID: route.id})

def event_upload_new_route(event, **kwargs):
    api, *_ = arg_check('api', **kwargs)
    
    bucket, err_resp = get_key(event, LambdaConstants.EVENT_BUCKET)
    if err_resp:
        return err_resp
    key, err_resp = get_key(event, LambdaConstants.EVENT_OBJECT_KEY)
    if err_resp:
        return err_resp

    routeName = event[LambdaConstants.EVENT_ROUTE_NAME] if LambdaConstants.EVENT_ROUTE_NAME in event else None

    readings = api.save_new_route(bucket, key, routeName)
    return success_response(readings)

def event_save_predictions(event, **kwargs):
    api, user_data = arg_check('api', 'user_data', **kwargs)

    route_id, err_resp = get_key(event, Constants.ROUTE_ID)
    if err_resp:
        return err_resp
    readings, err_resp = get_key(event, LambdaConstants.EVENT_PREDICTIONS)
    if err_resp:
        return err_resp

    api.save_predictions(
        readings, 
        route_id,
        user_data.user_sub,
        save_imgs=True
    )
    return success_response({LambdaConstants.RESPONSE_SAVED_READINGS: readings})

def event_update_route_name(event, **kwargs):
    api, user_data = arg_check('api', 'user_data', **kwargs)
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

def event_add_user(event, **kwargs): 
    api, *_ = arg_check('api', **kwargs)
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
 
def event_add_org(event, **kwargs):
    api, *_ = arg_check('api', **kwargs)
    org_name, err_resp = get_key(event, Constants.ORG_NAME)
    if err_resp:
        return err_resp

    existing_org = api.get_org(org_name)

    if existing_org is not None:
        return error_response(f'Org {org_name} already exists')

    org = api.put_org(org_name)

    return success_response(org)

def event_road_snap(event, **kwargs):
    points, err_resp = get_key(event, LambdaConstants.EVENT_POINTS)

    if err_resp:
        return err_resp

    if len(points) < 2:
        return error_response(f'Not Enough Points Given ({len(points)})')

    geolocator = Geolocator()
    return success_response({
        LambdaConstants.EVENT_POINTS: geolocator.geolocate(points, replacement=True)
    })