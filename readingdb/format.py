from typing import Any, Dict
from readingdb.constants import *
from datetime import datetime

epoch = datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return int((dt - epoch).total_seconds() * 1e3)

def unix_from_key(key: str) -> int:
    ts_str = key.split('/')[-1].split('-')[0]
    if 'img_' in key:
        return int(ts_str.split('_')[-1])

    dt = datetime.strptime(ts_str, '%Y_%m_%d_%H_%M_%S_%f')

    return unix_time_millis(dt)

def entry_from_file(bucket: str, key: str) -> Dict[str, Any]:
    return {
        Constants.TIMESTAMP: unix_from_key(key),
        Constants.READING: {
            Constants.URI: {
                Constants.BUCKET: bucket,
                Constants.KEY: key
            }
        },
}

def txt_to_points(lines):
    points = []

    for line in lines:
        if len(line) > 10:
            segments = [s.strip('\n').strip('\r') for s in line.split(' ') if s != '']    
            point = {
                Constants.TIMESTAMP: int(segments[0].split(':')[-1]),
                Constants.READING: {
                    Constants.LATITUDE: float(segments[1].split(':')[-1]),
                    Constants.LONGITUDE: float(segments[2].split(':')[-1])
                },
            }

            points.append(point)

    return points

# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# ------------------------ DDB KEYS -------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------
# -----------------------------------------------------------------

def route_sort_key(rid:str) -> str:
    return f'Route#{rid}'