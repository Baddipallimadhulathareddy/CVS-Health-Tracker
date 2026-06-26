import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="madhu@12345",
    database="cvs_tracker",
    use_pure=True,
    connection_timeout=5,
    autocommit=True
)

cursor = db.cursor()

print("Database Connected")