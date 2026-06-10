class SplitSelectionPolicy:
    def get_split_structure(
        self, days_per_week: int, training_style: str = "balanced"
    ) -> list[tuple[str, str, str]]:
        style = (training_style or "").strip().lower()
        if days_per_week == 2:
            return [
                ("Full Body A", "full_body", "full_body"),
                ("Full Body B", "full_body", "full_body"),
            ]
        elif days_per_week == 3:
            return [
                ("Full Body Strength", "full_body", "full_body"),
                ("Upper Body", "upper_body", "upper_body"),
                ("Lower Body + Core", "lower_body", "lower_body"),
            ]
        elif days_per_week == 4:
            return [
                ("Upper Push Balanced", "upper_push_balanced", "push"),
                ("Lower Body + Core", "lower_core", "lower_body"),
                ("Upper Pull Posture", "upper_pull_posture", "pull"),
                ("Full Body Conditioning", "full_body_conditioning", "conditioning"),
            ]
        elif days_per_week == 5:
            return [
                ("Push", "upper_body_push", "push"),
                ("Pull", "upper_body_pull", "pull"),
                ("Legs", "lower_body", "lower_body"),
                ("Upper Accessories", "upper_body", "upper_body"),
                ("Lower + Conditioning", "lower_body", "lower_body"),
            ]
        elif days_per_week == 6:
            if style == "returning":
                # Option B, balanced/returning
                return [
                    ("Upper Push", "upper_body_push", "push"),
                    ("Lower Body", "lower_body", "lower_body"),
                    ("Upper Pull", "upper_body_pull", "pull"),
                    ("Conditioning & Core", "full_body_conditioning", "conditioning"),
                    ("Full Body Light", "full_body", "full_body"),
                    ("Recovery & Mobility", "recovery_session", "recovery"),
                ]
            else:
                # Option A, standard
                return [
                    ("Push", "upper_body_push", "push"),
                    ("Pull", "upper_body_pull", "pull"),
                    ("Legs", "lower_body", "lower_body"),
                    ("Push Variation", "upper_push_balanced", "push"),
                    ("Pull Variation", "upper_pull_posture", "pull"),
                    ("Legs & Conditioning", "full_body_conditioning", "conditioning"),
                ]
        else:
            raise ValueError("days_per_week must be between 2 and 6.")
