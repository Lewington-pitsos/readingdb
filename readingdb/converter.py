import xml.etree.ElementTree as elementTree
import time
from pathlib import Path
from readingdb.constants import *

class Converter():

    def XML_to_single_reading(xml_data: str, image_uri: str = None):
        root = elementTree.fromstring(xml_data)
        reading = {
            "Timestamp": int(time.time()),
            "MillisecondPrecision": True,
            "Accuracy": 0,
            "Speed": 0.0,
            "Bearing": 0.0,
            "Row": 0,
            "AnnotationTimestamp": 0,
            "AnnotatorID": DEFAULT_ANNOTATOR_ID,
            "Reading": {
                "Latitude": -50,
                "Longitude": 140,
                Constants.FILENAME: image_uri,
                "Entities": []
            }
        }

        for obj in root.findall('object'):
            reading[Constants.READING][Constants.ENTITIES].append(
                {
                    Constants.ENTITY_NAME : obj.find('name').text,
                    Constants.CONFIDENCE : 0,
                    Constants.SEVERITY : obj.find('severity').text,
                    Constants.PRESENT : True,
                    Constants.BOUNDING_BOX : {
                        'xmin' : obj.find('./bndbox/xmin').text,
                        'ymin' : obj.find('./bndbox/ymin').text,
                        'xmax' : obj.find('./bndbox/xmax').text,
                        'ymax' : obj.find('./bndbox/ymax').text,
                    }
                }
            )

        return reading
