import unittest
import time

from readingdb.api import API 
from readingdb.constants import *

class TestAPI(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):    
        api = API("http://localhost:8000")