import os
from readingdb.digester import Digester
from readingdb.geolocator import Geolocator
from readingdb.endpoints import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('root', help='the directory containing all the images', type=str)
parser.add_argument('uid', help='the id of the user to upload the routes under', type=str)
args = parser.parse_args()

root = args.root

if root[-1] != '/':
    root += '/'

subdirs = [root + r for r in  os.listdir(root)]
files = []
for s in subdirs:
    if os.path.isdir(s):
        subsubdirs = [s + '/' + r for r in os.listdir(s)]
        for ss in subsubdirs:
            files.append(ss)
    else:
        files.append(s)

z = Digester(DYNAMO_ENDPOINT, region_name="ap-southeast-2")
z.process_local(
    args.uid,
    root.split("/")[-2],
    'mobileappsessions172800-main', 
    files,
    snap_to_roads=True
)