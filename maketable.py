from readingdb.db import DB

if __name__ == '__main__':
    db = DB("http://localhost:8000")
    movie_table = db.create_reading_db()
    print("Table status:", movie_table.table_status)