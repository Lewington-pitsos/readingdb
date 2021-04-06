import json
from readingdb.constants import S3Path
from typing import Any, Dict


class S3Uri():
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]):
        return cls(
            json_data[S3Path.BUCKET],
            json_data[S3Path.KEY]
        )

    def __init__(self, bucket: str, object_name: str) -> None:
        self.bucket = bucket
        self.object_name = object_name