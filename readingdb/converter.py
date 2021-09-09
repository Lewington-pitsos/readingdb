from typing import Container
import xml.etree.ElementTree as elementTree
import time
from pathlib import Path
from readingdb.constants import *
from readingdb.reading import PredictionReading

class Converter():

    def XML_to_single_reading(xml_data: str, **additional_reading_data):
        root = elementTree.fromstring(xml_data)
        readingjson = {
            Constants.TIMESTAMP: int(time.time()),
            "MillisecondPrecision": True,
            "Accuracy": 0,
            "Speed": 0.0,
            "Bearing": 0.0,
            "Row": 0,
            Constants.ANNOTATION_TIMESTAMP: 0,
            Constants.ANNOTATOR_ID: DEFAULT_ANNOTATOR_ID,
            Constants.READING: {
                Constants.LATITUDE: -50,
                Constants.LONGITUDE: 140,
                Constants.ENTITIES: []
            }
        }

        readingjson['Reading'].update(additional_reading_data)

        for obj in root.findall('object'):
            readingjson[Constants.READING][Constants.ENTITIES].append(
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

        return readingjson
