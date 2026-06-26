def calculate_risk_score(redness_level,
                         squeezing_alert,
                         itching_alert,
                         blink_status):

    score = 0

    if redness_level == "Mild":
        score += 15

    elif redness_level == "Critical":
        score += 30

    if squeezing_alert:
        score += 20

    if itching_alert:
        score += 20

    if blink_status == "Critical (Low)":
        score += 30

    elif blink_status == "Critical (High)":
        score += 20

    score = min(score, 100)

    if score < 30:
        level = "LOW"
    elif score < 60:
        level = "MEDIUM"
    else:
        level = "HIGH"

    return score, level