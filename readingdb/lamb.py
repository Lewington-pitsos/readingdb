import logging
from typing import Dict, Any, Callable, Tuple

from botocore.config import Config
from readingdb import lambda_event_functions

from readingdb.constants import *
from readingdb.endpoints import BUCKET, DYNAMO_ENDPOINT, TEST_BUCKET, TEST_DYNAMO_ENDPOINT
from readingdb.eventhandler import EventHandler
from readingdb.lambda_event_functions import *

api = API(
    DYNAMO_ENDPOINT, 
    bucket = BUCKET ,
    size_limit = 2_400_000,
    region_name= REGION_NAME
    )
auth = Auth(region_name=REGION_NAME)    

def get_auth_setup(auth) -> Callable:
    def event_setup(event) -> Dict:
        user_data: AuthResponse = auth.get_user(event[LambdaConstants.EVENT_ACCESS_TOKEN])
        if not user_data.is_authenticated():
            return error_response(f'Unauthenticated request, unrecognized Access Token {event[LambdaConstants.EVENT_ACCESS_TOKEN]}')
        else:
            return {'user_data':user_data}
    
    return event_setup

def validate_event(event) -> Tuple[bool, Dict[str, Any]]:
    if LambdaConstants.EVENT_TYPE in event:
        event_name = event[LambdaConstants.EVENT_TYPE]
    else:
        return False, error_response('Invalid Event Syntax')

    if not LambdaConstants.EVENT_ACCESS_TOKEN in event:
        return False, error_response('Unauthenticated request, no Access Token Provided')
    
    return True, None

event_handler = EventHandler(
    validate_event,
    get_auth_setup(auth),
    handlers = {
        LambdaConstants.EVENT_GET_ROUTE: get_route,
    }
)

def handler(event: Dict[str, Any], context):
    return event_handler.handle(event, api=api)

def test_handler(
    event: Dict[str, Any], 
    context,  
    endpoint: str=TEST_DYNAMO_ENDPOINT, 
    bucket: str=TEST_BUCKET,
    size_limit: int=25_000_000
):
    test_api = API(
        TEST_DYNAMO_ENDPOINT, 
        bucket = TEST_BUCKET ,
        size_limit = 2_400_000,
        region_name= REGION_NAME
        )
    auth = Auth(region_name=REGION_NAME) 

    test_event_handler = EventHandler(
        validate_event,
        get_auth_setup(auth),
        handlers = {
            LambdaConstants.EVENT_GET_ROUTE: get_route,
            LambdaConstants.EVENT_DELETE_ROUTE: delete_route,
            LambdaConstants.EVENT_GET_USER_ROUTES: get_user_routes,
            LambdaConstants.EVENT_GET_READINGS: get_readings,
            LambdaConstants.EVENT_PROCESS_UPLOADED_ROUTE: process_uploaded_route
        }
    )

    return test_event_handler.handle(event, api = test_api)
    