from pprint import pprint

from readingdb.db import DB

if __name__ == '__main__':
    db = DB("http://localhost:8000")
    movie = db.all_route_readings(3)
    if movie:
        print("Get movie succeeded:")
        pprint(movie, sort_dicts=False)