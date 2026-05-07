import psycopg
from psycopg.rows import dict_row
import os

conn_string = "postgresql://" + os.getenv("DB_USER") + ":" + os.getenv("DB_PASSWORD") + "@localhost:" + os.getenv("DB_PORT") + "/" + os.getenv("DB_NAME")
# conn_string = "dbname=" + os.getenv("DB_NAME") +" user=" + os.getenv("DB_USER")
print(conn_string)
conn = psycopg.connect(conn_string)

def get_users():
    with conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM tester2")
            print(cur.fetchone())
            return
    
get_users()