from readingdb.db import DB
from readingdb.constants import *

if __name__ == '__main__':
    db = DB("http://localhost:8000")

    db.delete_table(Database.READING_TABLE_NAME)
    print("Movies table deleted.")
