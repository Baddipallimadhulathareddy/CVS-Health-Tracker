import subprocess
import time
from flask import Flask, render_template, request, redirect, Response, jsonify
from database import db, cursor

app = Flask(__name__)

scan_start_time = None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        query = """
        INSERT INTO users(name,email,password)
        VALUES(%s,%s,%s)
        """

        cursor.execute(
            query,
            (
                name,
                email,
                password
            )
        )

        db.commit()
        return redirect("/")

    with open("current_name.txt","r") as f:
        current_name = f.read()
    with open("current_email.txt","r") as f:
        current_email = f.read()
    return render_template("signup.html")


@app.route("/logout")
def logout():
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        query = """
        SELECT id,name,email
        FROM users
        WHERE email=%s AND password=%s
        """
        db.reconnect(attempts=3, delay=1)
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

            with open("current_user.txt", "w") as f:
                f.write(str(user_id))
            with open("current_name.txt", "w") as f:
                f.write(name)
            with open("current_email.txt", "w") as f:
                f.write(email)

            return redirect("/dashboard")
        else:
            return render_template(
                "login.html",
                error="Invalid Email or Password"
            )

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    with open("current_user.txt", "r") as f:
        user_id = int(f.read())
    db.reconnect(attempts=3, delay=1)

    query = """
SELECT
    blink_rate,
    redness,
    squeezing,
    itching,
    risk_score,
    risk_level,
    recommendations,
    report_date
FROM reports
WHERE user_id=%s
ORDER BY report_date DESC
"""

    cursor.execute(query, (user_id,))
    reports = cursor.fetchall()

    if reports:
        latest = reports[0]
        data = {
            "blink_rate": latest[0],
            "redness": latest[1],
            "squeezing": latest[2],
            "itching": latest[3],
            "risk_score": latest[4],
            "risk_level": latest[5],
            "recommendations": latest[6],
            "report_date": latest[7]
        }
    else:
        data = {
            "blink_rate": 0,
            "redness": "0%",
            "squeezing": 0,
            "itching": 0,
            "risk_score": 0,
            "risk_level": "NO",
            "recommendations": ""
        }

    with open("current_name.txt","r") as f:
        current_name = f.read()
    with open("current_email.txt","r") as f:
        current_email = f.read()

    return render_template(
        "first.html",
        page="dashboard",
        data=data,
        reports=reports,
        current_name=current_name,
        current_email=current_email
    )


@app.route("/history")
def history():
    with open("current_user.txt","r") as f:
        user_id = int(f.read())
    db.reconnect(attempts=3, delay=1)

    query = """
    SELECT
        report_date,
        blink_rate,
        redness,
        squeezing,
        itching,
        risk_score,
        risk_level
    FROM reports
    WHERE user_id=%s
    ORDER BY report_date DESC
    """

    cursor.execute(query,(user_id,))
    reports = cursor.fetchall()

    with open("current_name.txt","r") as f:
        current_name = f.read()
    with open("current_email.txt","r") as f:
        current_email = f.read()

    return render_template(
        "first.html",
        page="history",
        reports=reports,
        current_name=current_name,
        current_email=current_email
    )


@app.route("/eye_scan")
def eye_scan():
    with open("current_name.txt","r") as f:
        current_name = f.read()
    with open("current_email.txt","r") as f:
        current_email = f.read()

    return render_template(
        "first.html",
        page="eye_scan",
        camera_active=True,
        current_name=current_name,
        current_email=current_email
    )


@app.route("/progress")
def progress():
    with open("current_user.txt","r") as f:
        user_id = int(f.read())

    db.reconnect(attempts=3, delay=1)

    cursor.execute("""
    SELECT
        risk_score,
        report_date
    FROM reports
    WHERE user_id=%s
    ORDER BY report_date DESC
    LIMIT 7
    """,(user_id,))

    reports = cursor.fetchall()

    if len(reports) == 0:
        with open("current_name.txt","r") as f:
            current_name = f.read()
        with open("current_email.txt","r") as f:
            current_email = f.read()
        return render_template(
            "first.html",
            page="progress",
            progress=None,
            current_name=current_name,
            current_email=current_email
        )

    scores = [r[0] for r in reversed(reports)]
    latest = scores[-1]
    previous = scores[-2] if len(scores) > 1 else latest
    improvement = max(previous - latest, 0)

    if latest <= 30:
        tier = "GRADE I - INTERMEDIATE"
    elif latest <= 60:
        tier = "GRADE II - MODERATE"
    else:
        tier = "GRADE III - HIGH"

    with open("current_name.txt","r") as f:
        current_name = f.read()
    with open("current_email.txt","r") as f:
        current_email = f.read()

    return render_template(
        "first.html",
        page="progress",
        progress={
            "latest": latest,
            "previous": previous,
            "improvement": improvement,
            "tier": tier,
            "scores": scores
        },
        current_name=current_name,
        current_email=current_email
    )


# New route for browser-sent frames (Phase 1 preparation)
@app.route("/process_frame", methods=["POST"])

def process_frame_route():
    import cv2

    print("OpenCV Loaded Successfully")
    import base64
    import numpy as np
    from eye import process_frame

    data = request.json["image"]

    encoded = data.split(",")[1]

    image = base64.b64decode(encoded)

    npimg = np.frombuffer(image, np.uint8)

    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    try:

        frame, result = process_frame(frame)

        return jsonify(result)

    except Exception as e:

        print(e)

        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)