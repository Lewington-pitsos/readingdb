from readingdb.lamb import handler
import unittest
from unittest.mock import Mock

from readingdb.eventhandler import EventHandler

class TestEventHandler(unittest.TestCase):

    def test_register_event(self):
        handler = EventHandler()

        handler.register_event('dummy event', lambda event, context : {'Status': 'Success'})
        self.assertIn('dummy event', handler.event_handlers)

        with self.assertRaises(TypeError):
            handler.register_event('no callback', None)

        with self.assertRaises(TypeError):
            handler.register_event(1, lambda event, context : {'Status': 'Success'})

    def test_init_with_handlers(self):
        handler = EventHandler({
            'eventname1': lambda event, context : {'Status': 'Success'},
            'eventname2': lambda event, context : {'Status': 'Error'}
        })

        self.assertIn('eventname1', handler.event_handlers)
        self.assertIn('eventname2', handler.event_handlers)

        with self.assertRaises(TypeError):
            handler = EventHandler({
                'eventname1': lambda event, context : {'Status': 'Success'},
                1 : lambda event, context : {'Status': 'Error'}
            })

    def test_handler(self):
        handler = EventHandler({
            'eventname1': Mock(return_value={'Status':'Error'}),
            'eventname2': Mock(return_value={'Status':'Error'}),
        })
        handler.handler({'Type': 'eventname1'})
        handler.event_handlers['eventname1'].assert_called_with({'Type':'eventname1'})

        