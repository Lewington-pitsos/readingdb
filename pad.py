
from readingdb.db import DB

db = DB("http://localhost:8000")
# db.teardown_reading_db()
print(db.all_tables())