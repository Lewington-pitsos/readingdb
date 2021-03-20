from readingdb.db import DB

if __name__ == '__main__':
    db = DB("http://localhost:8000")

    db.delete_table()
    print("Movies table deleted.")
