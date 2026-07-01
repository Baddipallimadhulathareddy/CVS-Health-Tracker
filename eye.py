import cv2
import mediapipe as mp
import numpy as np
import time
# ------------------------------ Setup ------------------------------
mp_face_mesh = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
EAR_THRESHOLD = 0.21
CONSEC_FRAMES = 1
REDNESS_NORMAL_LIMIT = 0.10
REDNESS_CRITICAL_LIMIT = 0.22
BASELINE_FRAMES = 10
ITCH_DISTANCE = 220
# ------------------------------ Variables ------------------------------
blink_counter = 0
closed_frames = 0
blink_start_time = None
blink_durations = []
blink_timestamps = []
baseline_ear_values = []
baseline_ear = None
saved = False

session_redness = []
session_squeezing = 0
session_itching = 0
# Initialize MediaPipe
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=0,
    min_detection_confidence=0.35,
    min_tracking_confidence=0.35
)
# ------------------------------ Helper Functions ------------------------------
def eye_aspect_ratio(landmarks, eye_points):
    p1, p2, p3, p4, p5, p6 = [np.array([landmarks[i].x, landmarks[i].y]) for i in eye_points]
    A = np.linalg.norm(p2 - p6)
    B = np.linalg.norm(p3 - p5)
    C = np.linalg.norm(p1 - p4)
    ear = (A + B) / (2.0 * C)
    return ear

def redness_detection(eye_region):
    hsv = cv2.cvtColor(eye_region, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 40, 40])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 40, 40])
    upper_red2 = np.array([180, 255, 255])
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)
    red_ratio = cv2.countNonZero(mask) / (mask.shape[0] * mask.shape[1]) if mask.shape[0] * mask.shape[1] > 0 else 0
    if red_ratio < REDNESS_NORMAL_LIMIT:
        return "Normal"
    elif red_ratio < REDNESS_CRITICAL_LIMIT:
        return "Mild"
    else:
        return "Critical"

# ------------------------------ Main Processing Function ------------------------------
def process_frame(frame):
    global saved
    global blink_counter, closed_frames, blink_start_time, blink_durations, blink_timestamps, baseline_ear_values, baseline_ear

    global start_time

    if "start_time" not in globals():
        start_time = time.time()
    TEST_DURATION = 10

    global session_redness
    global session_squeezing
    global session_itching

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results_face = face_mesh.process(rgb)
    results_hands = hands.process(rgb)

    h, w, _ = frame.shape
    current_time = time.time()

    # Default Values
    squeezing_alert = False
    itching_alert = False
    redness_level = "Normal"
    color_red = (0, 255, 0)
    blink_rate = 0
    avg_blink_time = 0
    avg_gap = 0
    blink_status = "Unknown"
    color_blink = (255, 255, 255)

    if results_face.multi_face_landmarks:
        for face_landmarks in results_face.multi_face_landmarks:
            # EAR Calculation
            left_ear = eye_aspect_ratio(face_landmarks.landmark, LEFT_EYE)
            right_ear = eye_aspect_ratio(face_landmarks.landmark, RIGHT_EYE)
            avg_ear = (left_ear + right_ear) / 2.0
#             print(
#     f"EAR={avg_ear:.3f}  Baseline={baseline_ear}  Closed={closed_frames}  Blinks={blink_counter}"
# )

            # Baseline EAR Setup
            if baseline_ear is None:
                baseline_ear_values.append(avg_ear)
                if len(baseline_ear_values) >= BASELINE_FRAMES:
                    baseline_ear = np.mean(baseline_ear_values)
                    print("Baseline Ready:", baseline_ear)
                cv2.putText(frame, "Calibrating baseline EAR...", (30, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                # Continue processing for display
            else:
                # Blink Detection
                dynamic_threshold = baseline_ear * 0.82
                # print("Threshold =", round(dynamic_threshold, 3))
                if avg_ear < dynamic_threshold:
                    # print("Eye Closed")
                    closed_frames += 1
                    if blink_start_time is None:
                        blink_start_time = current_time
                else:
                    # print("Eye Open")
                    if closed_frames >= CONSEC_FRAMES:
                        blink_counter += 1
                        print("BLINK DETECTED ->", blink_counter)

                        if blink_start_time:
                            blink_duration = current_time - blink_start_time
                            blink_durations.append(blink_duration)
                            blink_timestamps.append(current_time)
                    closed_frames = 0
                    blink_start_time = None

                # Blink Rate and Gap
                blink_timestamps = [t for t in blink_timestamps if current_time - t <= 60]
                elapsed_minutes = max((current_time - start_time) / 60, 1 / 60)
                blink_rate = int(blink_counter / elapsed_minutes)
                avg_blink_time = np.mean(blink_durations) if blink_durations else 0
                if len(blink_timestamps) > 1:
                    avg_gap = np.mean(np.diff(blink_timestamps))
                else:
                    avg_gap = 0

                # Blink status
                if blink_rate < 10:
                    blink_status = "Critical (Low)"
                elif blink_rate > 25:
                    blink_status = "Critical (High)"
                else:
                    blink_status = "Normal"

                # Squeezing Detection
                if avg_ear < baseline_ear * 0.65:
                    squeezing_alert = True
                    session_squeezing += 1

                # Redness Detection
                left = face_landmarks.landmark[33]
                right = face_landmarks.landmark[263]
                top = face_landmarks.landmark[159]
                bottom = face_landmarks.landmark[145]
                x1 = int(min(left.x, right.x) * w)
                x2 = int(max(left.x, right.x) * w)
                y1 = int(top.y * h)
                y2 = int(bottom.y * h)
                padding = 35
                eye_region = frame[
                    max(0, y1 - padding):min(h, y2 + padding),
                    max(0, x1 - padding):min(w, x2 + padding)
                ]
                if eye_region.size > 0:
                    redness_level = redness_detection(eye_region)
                    session_redness.append(redness_level)
                    color_red = (
                        (0, 255, 0) if redness_level == "Normal" else
                        (0, 255, 255) if redness_level == "Mild" else
                        (0, 0, 255)
                    )

                # Eye Itching Detection
                if results_hands.multi_hand_landmarks:
                    for hand_landmarks in results_hands.multi_hand_landmarks:
                        tip = hand_landmarks.landmark[8]
                        mcp = hand_landmarks.landmark[5]
                        x = int(((tip.x + mcp.x) / 2) * w)
                        y = int(((tip.y + mcp.y) / 2) * h)
                        left_eye_pos = (
                            int((face_landmarks.landmark[33].x + face_landmarks.landmark[133].x) / 2 * w),
                            int((face_landmarks.landmark[159].y + face_landmarks.landmark[145].y) / 2 * h)
                        )
                        right_eye_pos = (
                            int((face_landmarks.landmark[362].x + face_landmarks.landmark[263].x) / 2 * w),
                            int((face_landmarks.landmark[386].y + face_landmarks.landmark[374].y) / 2 * h)
                        )
                        left_dist = np.linalg.norm(np.array([x, y]) - np.array(left_eye_pos))
                        right_dist = np.linalg.norm(np.array([x, y]) - np.array(right_eye_pos))
                        if (left_dist < ITCH_DISTANCE or right_dist < ITCH_DISTANCE or
                            (left_dist < 260 and avg_ear < baseline_ear * 0.85) or
                            (right_dist < 260 and avg_ear < baseline_ear * 0.85)):
                            itching_alert = True
                            session_itching += 1
                            cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
                            cv2.line(frame, (x, y), left_eye_pos, (255, 0, 0), 2)
                            cv2.line(frame, (x, y), right_eye_pos, (255, 0, 0), 2)
                            break

    # ---------------- Risk Score Calculation ----------------
    risk_score = 0
    # Blink Rate
    if blink_rate < 10:
        risk_score += 40
    elif blink_rate < 15:
        risk_score += 30
    elif blink_rate < 20:
        risk_score += 20
    elif blink_rate < 30:
        risk_score += 10
    # Eye Redness
    if redness_level == "Critical":
        risk_score += 35
    elif redness_level == "Mild":
        risk_score += 10
    # Eye Squeezing
    if squeezing_alert:
        risk_score += 15
    # Eye Itching
    if itching_alert:
        risk_score += 10
    risk_score = min(risk_score, 100)

    # Risk Level
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # ---------------- Display Clean Info on Screen ----------------
    info_y = 50
    line_gap = 30
    cv2.putText(frame, f"Blinks: {blink_counter}", (30, info_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Blink Rate: {blink_rate}/min ({blink_status})", (30, info_y + line_gap),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_blink, 2)
    cv2.putText(frame, f"Avg Blink Time: {avg_blink_time:.2f}s", (30, info_y + 2 * line_gap),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Avg Gap Between Blinks: {avg_gap:.1f}s", (30, info_y + 3 * line_gap),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(frame, f"Redness: {redness_level}", (30, info_y + 4 * line_gap),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_red, 2)
    cv2.putText(
        frame,
        f"CVS Risk Score: {risk_score}/100 ({risk_level})",
        (30, info_y + 5 * line_gap),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )
    if squeezing_alert:
        cv2.putText(frame, "Eye Squeezing Detected", (30, info_y + 6 * line_gap),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    if itching_alert:
        cv2.putText(frame, "Possible Eye Itching", (30, info_y + 7 * line_gap),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Time Left
    elapsed_time = time.time() - start_time
    # print("Elapsed:", elapsed_time)
    remaining = max(0, int(TEST_DURATION - elapsed_time))
    cv2.putText(
        frame,
        f"Time Left: {remaining}s",
        (450, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    # ---------------- Final Analysis ----------------
    final_redness = "Normal"
    if session_redness:
        if session_redness.count("Critical") > session_redness.count("Mild"):
            final_redness = "Critical"
        elif session_redness.count("Mild") > 0:
            final_redness = "Mild"

    final_squeezing = session_squeezing >= 2
    final_itching = session_itching >= 1

    if blink_rate < 10:
        blink_status = "Critical (Low)"
    elif blink_rate > 25:
        blink_status = "Critical (High)"
    else:
        blink_status = "Normal"

    # Final Risk Score Calculation (using final values)
    risk_score = 0
    if blink_rate < 10:
        risk_score += 40
    elif blink_rate < 15:
        risk_score += 30
    elif blink_rate < 20:
        risk_score += 20
    elif blink_rate < 30:
        risk_score += 10

    if final_redness == "Critical":
        risk_score += 35
    elif final_redness == "Mild":
        risk_score += 10

    if final_squeezing:
        risk_score += 15
    if final_itching:
        risk_score += 10

    risk_score = min(risk_score, 100)

    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # ---------------- Recommendations ----------------
    recommendations = []
    if blink_rate < 15:
        recommendations.append(
            "Increase your blink frequency by taking regular breaks and consciously blinking more often."
        )
    if final_redness == "Critical":
        recommendations.append(
            "Your eye redness is severe. Reduce screen exposure immediately and consult an eye specialist if it continues."
        )
    elif final_redness == "Mild":
        recommendations.append(
            "Take short visual breaks to reduce eye strain."
        )
    if final_squeezing:
        recommendations.append(
            "Frequent eye squeezing indicates eye fatigue. Relax your eye muscles and avoid prolonged focus."
        )
    if final_itching:
        recommendations.append(
            "Avoid rubbing your eyes. Wash your hands frequently and consider artificial tears if irritation continues."
        )
    if len(recommendations) == 0:
        recommendations.append(
            "Excellent eye health detected. Continue following the 20-20-20 rule and maintain proper hydration."
        )

    recommendations_text = "\n".join(recommendations)

        # ---------------- Database Save ----------------

    elapsed_time = time.time() - start_time
    # print("Elapsed:", elapsed_time)
    # print("Elapsed Check:", elapsed_time)
    if elapsed_time >= TEST_DURATION and not saved:

        try:
            print("Reached Database Save")
            from database import db, cursor

            with open("current_user.txt", "r") as f:
                user_id = int(f.read())
            print("Current User ID =", user_id)

            query = """
            INSERT INTO reports(
                user_id,
                blink_rate,
                redness,
                squeezing,
                itching,
                risk_score,
                risk_level,
                recommendations
            )
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            """
            print("========== FINAL REPORT ==========")
            print("Blink Counter :", blink_counter)
            print("Blink Rate    :", blink_rate)
            print("Risk Score    :", risk_score)
            print("==================================")

            cursor.execute(
                query,
                (
                    user_id,
                    blink_rate,
                    final_redness,
                    final_squeezing,
                    final_itching,
                    risk_score,
                    risk_level,
                    recommendations_text
                )
            )
            print("Rows inserted:", cursor.rowcount)
            db.commit()
            cursor.execute("SELECT COUNT(*) FROM reports")
            print("TOTAL REPORTS:", cursor.fetchone()[0])
            print("Database Saved Successfully")

            saved = True
            del start_time
            
            blink_counter = 0
            closed_frames = 0
            blink_start_time = None
            blink_durations.clear()
            blink_timestamps.clear()
            baseline_ear_values.clear()
            baseline_ear = None
            session_redness.clear()
            session_squeezing = 0
            session_itching = 0
        except Exception as e:
            print("Database Error:", e)
       
        
        

    return frame, {
        "blink_rate": blink_rate,
        "redness": final_redness,
        "squeezing": final_squeezing,
        "itching": final_itching,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommendations": recommendations_text
    }