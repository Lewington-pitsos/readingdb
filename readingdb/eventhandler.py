from typing import Any, Dict, Callable

from botocore.config import Config

from readingdb.api import API
from readingdb.constants import *
from readingdb.auth import Auth, AuthResponse

#TODO: go full generic
from readingdb.lambda_event_functions import error_response

class EventHandler():

    def __init__(
        self, 
        validator: Callable[[], Dict] = None,
        event_setup: Callable[[], Dict] = None,
        handlers: Dict[str, Callable[[str], Dict[str, Any]]] = dict(),
        ) -> None:
        
        for eventname, callback in handlers.items():
            if not isinstance(eventname, str): 
                raise TypeError('event type must be a string')
            elif not callable(callback):
                raise TypeError('must pass in a valid handler function')
        self.__event_handlers = handlers

        self.__validator = validator
        self.__event_setup = event_setup

    def handle(self, event: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        if self.__validator:
            is_valid, err_resp = self.__validator(event)
            if not is_valid:
                return err_resp
    
        if self.__event_setup:
            setup_data = self.__event_setup(event)
        else:
            setup_data = {}

        event_name = event[LambdaConstants.EVENT_TYPE]
        if event_name in self.__event_handlers:
            return self.__event_handlers[event[LambdaConstants.EVENT_TYPE]](event, *args, **kwargs, **setup_data)
        else:
            return error_response(f'There is no handler registered for event {event_name}')

    @property
    def event_handlers(self):
        return self.__event_handlers.copy()