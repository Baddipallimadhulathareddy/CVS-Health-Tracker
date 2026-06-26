def get_recommendations(redness_level,
                        squeezing_alert,
                        itching_alert,
                        blink_status):

    recommendations = []

    # Eye Redness
    if redness_level == "Mild":
        recommendations.extend([
            "Wash your eyes with clean cold water 2-3 times daily.",
            "Reduce screen brightness and avoid prolonged screen usage.",
            "Follow the 20-20-20 rule every 20 minutes.",
            "Drink at least 2 liters of water daily."
        ])

    elif redness_level == "Critical":
        recommendations.extend([
            "Wash your eyes immediately with clean cold water.",
            "Rest your eyes for 15 minutes every hour.",
            "Avoid using mobile devices in dark environments.",
            "Consider consulting an eye specialist if redness persists."
        ])

    # Eye Squeezing
    if squeezing_alert:
        recommendations.extend([
            "Increase font size on your screen.",
            "Maintain a viewing distance of 50-70 cm from the monitor.",
            "Reduce screen glare using night mode or anti-glare filters.",
            "Adjust room lighting to avoid eye strain."
        ])

    # Eye Itching
    if itching_alert:
        recommendations.extend([
            "Avoid rubbing your eyes.",
            "Wash your hands before touching your face.",
            "Clean your eyes gently with clean water.",
            "Avoid dusty environments and allergens."
        ])

    # Blink Rate
    if blink_status == "Critical (Low)":
        recommendations.extend([
            "Blink consciously while working.",
            "Take a 5-minute eye break every hour.",
            "Look away from the screen frequently."
        ])

    elif blink_status == "Critical (High)":
        recommendations.extend([
            "Relax your eye muscles.",
            "Take a short break from screen activities."
        ])

    # Food Recommendations
    recommendations.extend([
        "",
        "Food Recommendations:",
        "Eat carrots for Vitamin A.",
        "Eat spinach and green leafy vegetables.",
        "Consume almonds and walnuts.",
        "Include eggs in your diet.",
        "Eat oranges and citrus fruits.",
        "Drink plenty of water daily."
    ])

    if not recommendations:
        recommendations.append(
            "No significant CVS symptoms detected. Continue healthy eye habits."
        )
    recommendation_text = "\n".join(recommendations)
    return recommendation_text