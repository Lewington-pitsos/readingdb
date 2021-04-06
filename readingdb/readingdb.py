import abc
from typing import List, Tuple

from readingdb.route import Route
from readingdb.reading import Reading
from readingdb.readingspec import ReadingSpec

class ReadingDB(abc.ABC):
    # ML API related
    @abc.abstractmethod
    def route_info(route_id: str, user_id: str) -> Route:
        """Returns null if no route exists for that route_id.
        """
        raise NotImplementedError("route_info is not implemented") 

    @abc.abstractmethod
    def set_as_predicting(route_id: str, user_id: str):
        """Updates the status of the specified route to predicting (indicating
        that a prediction process is under way).
        """
        raise NotImplementedError("set_as_predicting is not implemented") 

    @abc.abstractmethod
    def save_predictions(readings: List[Reading], route_id: int, user_id: str):
        """Saves the prediction readings to the given route and sets the status
        of that route to 'complete'.
        """
        raise NotImplementedError("save_predictions is not implemented")

    @abc.abstractmethod
    def all_route_readings(route_id: int, user_id: str) -> List[Reading]:
        """Returns all readings (e.g. gps readings, accelerometer readings, 
        camera image readings, prior predictions) associated with that route.
        """
        raise NotImplementedError("all_route_readings is not implemented")

    # Other

    @abc.abstractmethod
    def upload(reading_spec: ReadingSpec, user_id: str) -> str:
        """Uploads all readings listed within reading_spec as a single route.
        Returns the ID of the newly created route.
        """
        raise NotImplementedError("upload is not implemented")

    @abc.abstractclassmethod
    def update_route_name(route_id: str, user_id: str, name: str):
        """Sets the name of the given route to the given name.
        """
        raise NotImplementedError("not implemented")

    @abc.abstractclassmethod
    def process_upload(s3_uri: str, user_id: str) -> str:
        """Uploads all readings that exist within the se_uri (which 
        will be a zipped file) as a new route.

        Returns the id of the newly created route.
        """
        raise NotImplementedError("not implemented")

