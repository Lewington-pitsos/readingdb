from typing import Any, Dict, Callable

from botocore.config import Config

from readingdb.api import API
from readingdb.constants import *
from readingdb.auth import Auth, AuthResponse

#discuss extra coupling here
from readingdb.lambda_event_handlers import error_response

class EventHandler():

    def __init__(
        self, 
        endpoint: str,
        bucket: str,
        size_limit: str,
        handlers: Dict[str, Callable[[str], Dict[str, Any]]] = dict()
        ) -> None:
        
        for eventname, callback in handlers.items():
            if not isinstance(eventname, str): 
                raise TypeError('event type must be a string')
            elif not callable(callback):
                raise TypeError('must pass in a valid handler function')
        self.__event_handlers = handlers

        self.api = API(
            endpoint, 
            size_limit=size_limit, 
            bucket=bucket, 
            tmp_bucket=bucket, 
            config=Config(
                region_name=REGION_NAME,
            )
        )
        self.auth: Auth = Auth(region_name=REGION_NAME)

    def __event_validate(self,event):
        if Constants.EVENT_TYPE in event:
                event_name = event[Constants.EVENT_TYPE]
        else:
            return error_response('Invalid Event Syntax')

        if not Constants.EVENT_ACCESS_TOKEN in event:
            return error_response('Unauthenticated request, no Access Token Provided')
        
        user_data: AuthResponse = self.auth.get_user(event[Constants.EVENT_ACCESS_TOKEN])
        if not user_data.is_authenticated():
            return error_response(f'Unauthenticated request, unrecognized Access Token {event[Constants.EVENT_ACCESS_TOKEN]}')
        else:
            return user_data

    def register_event(self, event_type: str, handler_function: Callable[[str], Dict[str, Any]]) -> None:
        if not isinstance(event_type, str): 
            raise TypeError('event type must be a string')
        elif not callable(handler_function):
            raise TypeError('must pass in a valid handler function')

        self.__event_handlers[event_type] = handler_function

    def handler(self, event: Dict[str, Any]) -> Dict[str, Any]:
        user_data = self.__event_validate(event)
        if event[Constants.EVENT_TYPE] in self.__event_handlers:
            return self.__event_handlers[event[Constants.EVENT_TYPE]](event, self.api, user_data)
        else:
            return {'an error': 'todo'}

    @property
    def event_handlers(self):
        return self.__event_handlers.copy()