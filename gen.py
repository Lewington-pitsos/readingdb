import random
import os
import json

from readingdb.format import *

def nxt_img(fname):
      return {
        "Timestamp": unix_from_key(fname),
        "Reading": {
            "ImageFileName": fname
        }
    }

def nxt_ts(prv_ts, prv_lat, prv_long):
    ts = prv_ts + random.randint(-400, 400)

    lat = prv_lat + random.randint(0, 400) / 10000.0
    long = prv_long + random.randint(0, 400) / 10000.0

    return {
        "Timestamp": ts,
        "Reading": {
            "Latitude": lat,
            "Longitude": long
        }
    }, lat, long

pth = "readingdb/test_data/route_imgs/route_2021_04_07_17_14_36_709/"
fnames = [pth + f for f in os.listdir(pth)]

entries = []

gps_entries = []

lat =  -37.8714232
long =  145.2450816

for f in fnames:
    entries.append(nxt_img(f))
    ts = unix_from_key(f)

    e, lat, long = nxt_ts(ts, lat, long)
    gps_entries.append(e)

    e, lat, long = nxt_ts(ts, lat, long)
    gps_entries.append(e)

    e, lat, long = nxt_ts(ts, lat, long)
    gps_entries.append(e)


with open("readingdb/test_data/img.json", "w") as f:
    json.dump(entries, f, indent="    ")

with open("readingdb/test_data/gps.json", "w") as f:
    json.dump(gps_entries, f, indent="    ")