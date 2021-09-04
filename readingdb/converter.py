import xml.etree.ElementTree as elementTree
import time
from constants import *

class Converter():

    def XML_to_single_reading(xml_data: str):
        root = elementTree.fromstring(xml_data)
        reading = {
            "Timestamp": int(time.time()),
            "MillisecondPrecision": True,
            "Accuracy": 0,
            "Speed": 0.0,
            "Bearing": 0.0,
            "Row": 0,
            "AnnotationTimestamp": 0,
            "AnnotatorID": "xmldefault",
            "Reading": {
                "Latitude": -50,
                "Longitude": 140,
                "ImageFileName": None,
                "Entities": [
                    {
                        "Name": "LongCrack",
                        "Confidence": 0.6557837,
                        "Severity": 1.3,
                        "Present": False
                    }
                ]
            }
        }

        for obj in root.findall('object'):
            reading[ReadingKeys.READING][PredictionReadingKeys.ENTITIES].append(
                {
                    EntityKeys.NAME : obj.find('name').text,
                    EntityKeys.CONFIDENCE : 0,
                    EntityKeys.SEVERITY : obj.find('severity').text,
                    'boundingbox' : {
                        'xmin' : obj.find('./bndbox/xmin').text,
                        'ymin' : obj.find('./bndbox/ymin').text,
                        'xmax' : obj.find('./bndbox/xmax').text,
                        'ymax' : obj.find('./bndbox/ymax').text,
                    }
                }
            )
