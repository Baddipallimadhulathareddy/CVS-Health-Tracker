from database import cursor

email = input("Enter Email: ")
password = input("Enter Password: ")

query = """
SELECT id,name,email
FROM users
WHERE email=%s AND password=%s
"""

cursor.execute(
    query,
    (
        email,
        password
    )
)

user = cursor.fetchone()

if user:

    user_id = user[0]
    name = user[1]
    email = user[2]
    with open("current_name.txt","w") as f:
        f.write(name)

    with open("current_email.txt","w") as f:
        f.write(email)
    
    

    with open("login_status.txt", "w") as f:
        f.write("success")

    print(f"Welcome {name}")
    from database import cursor

    query = """
    SELECT recommendations
    FROM reports
    WHERE user_id=%s
    ORDER BY report_id DESC
    LIMIT 1
    """

    cursor.execute(query, (user_id,))
    last_report = cursor.fetchone()

    if last_report:

        print("\n===== LAST RECOMMENDATIONS =====")
        print(last_report[0])

else:

    with open("login_status.txt", "w") as f:
        f.write("failed")

    print("Invalid Email or Password")