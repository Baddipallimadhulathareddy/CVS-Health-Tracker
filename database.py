import os
import mysql.connector

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    port=int(os.getenv("DB_PORT") or 3306),
    use_pure=True,
    connection_timeout=5,
    autocommit=True
)

cursor = db.cursor()

print("Database Connected")