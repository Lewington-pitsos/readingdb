import json
import os
import argparse
import random
from typing import Any, Dict
import urllib.request
from readingdb.constants import *

from readingdb.endpoints import DYNAMO_ENDPOINT
from readingdb.api import API

parser = argparse.ArgumentParser()
parser.add_argument('name', help='a name to help remember the annotations', type=str)
parser.add_argument('aid', help='the id of the preferred annotator', type=str)
parser.add_argument('dir', help='the directory to save assessemnt data in', type=str)
parser.add_argument('routes', help='all route ids being assessed', nargs='+', default=[])

args = parser.parse_args()

if args.dir[-1] != '/':
    args.dir += '/'

directory = args.dir + args.name + '/'
os.mkdir(directory)

api = API(DYNAMO_ENDPOINT)
to_assess = []

def has_defect(reading: Dict[str, Any]) -> bool:
    for e in reading[Constants.READING][Constants.ENTITIES]:
        if e[Constants.PRESENT] and e[Constants.NAME] == 'D1001':
            return True
    return False

for rid in args.routes:
    all_readings = [r for r in api.all_route_readings(rid, annotator_preference=[args.aid]) if r[Constants.TYPE] == Constants.PREDICTION]
    print(f'count of readings for {rid}: {len(all_readings)}')

    fault_readings = []
    gc_readings = []

    for r in all_readings:
        if has_defect(r):
            gc_readings.append(r)
        else:
            fault_readings.append(r)

    to_assess.extend(random.sample(fault_readings, int(len(all_readings) / 100)))
    to_assess.extend(random.sample(gc_readings, int(len(all_readings) / 800)))

img_dir = directory + 'imgs/' 
os.mkdir(img_dir)

for r in to_assess:
    rid = r[Constants.READING_ID]
    print('saving', rid)
    urllib.request.urlretrieve(
        r[Constants.READING][Constants.PRESIGNED_URL], 
        img_dir + rid + '.jpg'
    )

with open(directory + 'readings.json', 'w') as f:
    json.dump(to_assess, f)