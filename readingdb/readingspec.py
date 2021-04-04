class ReadingSpec():
    def __init__(self, reading_type, format, path, name=None) -> None:
        self.reading_type = reading_type
        self.format = format
        self.path = path
        self.name = name