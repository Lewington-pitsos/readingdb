class S3Uri():
    def __init__(self, bucket: str, object_name: str) -> None:
        self.bucket = bucket
        self.object_name = object_name