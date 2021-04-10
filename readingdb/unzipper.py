class Unzipper():
    def __init__(self) -> None:
        pass

    def process(uri: str) -> None:
        # gets access to the uri stream from zipped file on s3
        # creates a new s3 object heirachy based on the metadata
        # extracts and uploads all the files to that s3 heirachy
        # creates a RouteSpec based on the readings it found during extraction
        # sends a request to the RaedingDB lambda to upload that routespec
        pass