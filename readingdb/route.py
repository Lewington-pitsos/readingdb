from readingdb.routestatus import RouteStatus

class Route():
    def __init__(self, user_id, id, name=None, sample_data=None) -> None:
        """sample_data contains a small collection of readings that belong to
        this route. Allows users to get an idea of what kind of data the route
        contains without loading all of it.
        """

        self.user_id = user_id
        self.id = id
        self.name = name
        self.sample_data = sample_data  
        self.status = RouteStatus.UPLOADED
