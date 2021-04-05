import abc
from typing import List, Tuple

from readingdb.route import Route
from readingdb.reading import Reading
from readingdb.readingspec import ReadingSpec

class ReadingDB(abc.ABC):
    # ML API related
    @abc.abstractmethod
    def route_info(route_id: int) -> Route:
        """Returns null if no route exists for that route_id.
        """
        raise NotImplementedError("route_info is not implemented") 

    @abc.abstractmethod
    def set_as_predicting(route_id: int) -> bool:
        """Updates the status of the specified route to predicting (indicating
        that a prediction process is under way). Returns false the route has any status 
        other that 'uploaded' or does not exist.
        """
        raise NotImplementedError("set_as_predicting is not implemented") 

    @abc.abstractmethod
    def save_predictions(readings: List[Reading], route_id: int) -> bool:
        """Saves the prediction readings to the given route and sets the status
        of that route to 'complete'.

        Returns whether the save operation completed sucessfully.
        """
        raise NotImplementedError("save_predictions is not implemented")

    @abc.abstractmethod
    def all_route_readings(route_id: int) -> List[Reading]:
        """Returns all readings (e.g. gps readings, accelerometer readings, 
        camera image readings, prior predictions) associated with that route.
        """
        raise NotImplementedError("all_route_readings is not implemented")

    @abc.abstractmethod
    def upload(reading_spec: ReadingSpec):
        raise NotImplementedError("upload is not implemented")
