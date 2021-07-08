from readingdb.constants import Constants
from typing import Any, Dict


class S3Uri():
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]):
        return cls(
            json_data[Constants.BUCKET],
            json_data[Constants.KEY]
        )

    def __init__(self, bucket: str, object_name: str) -> None:
        self.bucket = bucket
        self.object_name = object_name