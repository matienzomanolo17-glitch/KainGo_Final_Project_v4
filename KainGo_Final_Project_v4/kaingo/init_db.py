"""Creates the database, tables, and sample data:  python init_db.py   (XAMPP MySQL must be running)."""
import sys
import mysql.connector
from config import Config

conn = mysql.connector.connect(host=Config.DB_HOST, user=Config.DB_USER, password=Config.DB_PASSWORD, charset="utf8mb4")
cur = conn.cursor()
if "--reset" in sys.argv:            # python init_db.py --reset  (erases the old database and starts fresh)
    cur.execute(f"DROP DATABASE IF EXISTS {Config.DB_NAME}")
with open("database/kaingo_db.sql", encoding="utf-8") as f:
    sql = "\n".join(line for line in f if not line.strip().startswith("--"))   # skip comment lines
for statement in sql.split(";\n"):
    if statement.strip():
        cur.execute(statement)
conn.commit()
cur.close()
conn.close()
print("Database ready. Admin login -> admin@kaingo.org / Admin@123")
