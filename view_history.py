from database import cursor

with open("current_user.txt","r") as f:
    user_id = int(f.read())
with open("scan_status.txt","r") as f:
    status = f.read()

query = """
SELECT
report_date,
blink_rate,
redness,
squeezing,
itching,
risk_score,
risk_level,
recommendations
FROM reports
WHERE user_id=%s
ORDER BY report_date DESC
"""

cursor.execute(query,(user_id,))

rows = cursor.fetchall()

for row in rows:

    print("\n==========================")
    print("Date:", row[0])
    print("Blink Rate:", row[1])
    print("Redness:", row[2])
    print("Squeezing:", row[3])
    print("Itching:", row[4])
    print("Risk Score:", row[5])
    print("Risk Level:", row[6])

    print("\nRecommendations:")
    print(row[7])