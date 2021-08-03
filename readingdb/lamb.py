import logging
from typing import Dict, Any

from botocore.config import Config

from readingdb.constants import *
from readingdb.endpoints import BUCKET, DYNAMO_ENDPOINT, TEST_BUCKET, TEST_DYNAMO_ENDPOINT
from readingdb.eventhandler import EventHandler
from readingdb.lambda_event_handlers import *

event_handler = EventHandler(DYNAMO_ENDPOINT,BUCKET, 2_400_000)
event_handler.register_event(Constants.EVENT_GET_ROUTE, get_route)

def handler(event: Dict[str, Any], context):
    return event_handler.handler(event)

def test_handler(
    event: Dict[str, Any], 
    context,  
    endpoint: str=TEST_DYNAMO_ENDPOINT, 
    bucket: str=TEST_BUCKET,
    size_limit: int=25_000_000
):
    test_event_handler = EventHandler(TEST_DYNAMO_ENDPOINT,TEST_BUCKET,2_400_00)
    test_event_handler.register_event(Constants.EVENT_GET_ROUTE, get_route)
    return test_event_handler.handler(event)
    