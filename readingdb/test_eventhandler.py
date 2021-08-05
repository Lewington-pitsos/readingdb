from readingdb.lamb import handler
import unittest
from unittest.mock import Mock

from readingdb.eventhandler import EventHandler

class TestEventHandler(unittest.TestCase):

    def test_init_with_handlers(self):
        handler = EventHandler(
            event_setup= lambda event: {'userdata': 'nope'},
            validator= lambda event : True, 
            handlers={
                'eventname1': lambda event,  **kwargs: {'Status': 'Success'},
                'eventname2': lambda event,  **kwargs: {'Status': 'Error'}
        })

        self.assertIn('eventname1', handler.event_handlers)
        self.assertIn('eventname2', handler.event_handlers)

        with self.assertRaises(TypeError):
            handler = EventHandler(handlers = {
                'eventname1': lambda event, context : {'Status': 'Success'},
                1 : lambda event, context : {'Status': 'Error'}
            })

    def test_handler(self):
        handler = EventHandler(handlers={
            'eventname1': Mock(return_value={'Status':'Error'}),
            'eventname2': Mock(return_value={'Status':'Error'}),
        })
        handler.handle({'Type': 'eventname1'}, api = 'not present yo')
        handler.event_handlers['eventname1'].assert_called_with({'Type':'eventname1'}, api = 'not present yo')

        