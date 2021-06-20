import json
import os
import argparse
import random
import urllib.request
from readingdb.constants import *

from readingdb.endpoints import DYNAMO_ENDPOINT
from readingdb.api import API


parser = argparse.ArgumentParser()
# parser.add_argument('uid', help='user id', type=str)
parser.add_argument('name', help='a name to help remember the annotations', type=str)
parser.add_argument('dir', help='the directory to save assessemnt data in', type=str)
parser.add_argument('routes', help='all route ids being assessed', nargs='+', default=[])

args = parser.parse_args()

if args.dir[-1] != '/':
    args.dir += '/'

directory = args.dir + args.name + '/'
os.mkdir(directory)

api = API(DYNAMO_ENDPOINT)
to_assess = []

for rid in args.routes:
    all_readings = [r for r in api.all_route_readings(rid) if r[ReadingKeys.TYPE] == ReadingTypes.PREDICTION]

    to_assess.extend(random.sample(all_readings, int(len(all_readings) / 100)))

img_dir = directory + 'imgs/' 
os.mkdir(img_dir)

for r in to_assess:
    rid = r[ReadingKeys.READING_ID]
    print('saving', rid)
    urllib.request.urlretrieve(
        r[ReadingKeys.READING][ImageReadingKeys.PRESIGNED_URL], 
        img_dir + rid + '.jpg'
    )

with open(directory + 'readings.json', 'w') as f:
    json.dump(to_assess, f)