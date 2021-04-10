import time
from typing import Any, Dict
from readingdb.constants import *
from datetime import datetime, timezone

epoch = datetime.utcfromtimestamp(0)

def unix_time_millis(dt):
    return int((dt - epoch).total_seconds() * 1e3)

def unix_from_key(key: str) -> int:
    ts_str = key.split("/")[-1].split("-")[0]
    dt = datetime.strptime(ts_str, '%Y_%m_%d_%H_%M_%S_%f')

    return unix_time_millis(dt)

def entry_from_file(bucket: str, key: str) -> Dict[str, Any]:
    return {
        ReadingKeys.TIMESTAMP: unix_from_key(key),
        ReadingKeys.READING: {
            ImageReadingKeys.URI: {
                S3Path.BUCKET: bucket,
                S3Path.KEY: key
            }
        },
}
