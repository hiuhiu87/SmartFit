EQUIPMENT_CATEGORIES = {
    "free_weight": {"dumbbell", "barbell", "kettlebell"},
    "machine": {"machine", "smith_machine", "leg_press"},
    "cable": {"cable_machine"},
    "bodyweight": {"bodyweight", "pull_up_bar"},
    "cardio": {"treadmill", "bike", "rowing_machine", "elliptical"},
    "other": {"resistance_band", "none"},
}


def get_equipment_category(equipment: str) -> str:
    normalized = (equipment or "").strip().lower()
    for category, values in EQUIPMENT_CATEGORIES.items():
        if normalized in values:
            return category
    return "other"
