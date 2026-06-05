from collections import Counter

from src.domain.exercise.entities import Exercise
from src.domain.exercise.equipment_policy import get_equipment_category


class EquipmentDiversityPolicy:
    def category_distribution(
        self, selected_exercises: list[Exercise]
    ) -> dict[str, int]:
        return dict(
            Counter(
                get_equipment_category(exercise.equipment_type.value)
                for exercise in selected_exercises
            )
        )

    def would_overuse_equipment(
        self,
        candidate: Exercise,
        selected: list[Exercise],
        max_ratio: float,
    ) -> bool:
        if not selected:
            return False
        category = get_equipment_category(candidate.equipment_type.value)
        distribution = self.category_distribution(selected)
        return (distribution.get(category, 0) + 1) / (len(selected) + 1) > max_ratio

    def diversity_bonus(
        self,
        candidate: Exercise,
        selected: list[Exercise],
        target_categories: dict[str, int],
    ) -> int:
        category = get_equipment_category(candidate.equipment_type.value)
        distribution = self.category_distribution(selected)
        target = target_categories.get(category, 0)
        if target <= 0:
            return 0
        return 15 if distribution.get(category, 0) < target else 0

    def validate_final_mix(
        self,
        selected: list[Exercise],
        available_equipment: list[str],
        workout_type: str,
    ) -> list[str]:
        warnings: list[str] = []
        available_categories = {
            get_equipment_category(item) for item in available_equipment
        }
        distribution = self.category_distribution(selected)
        if len(available_categories) >= 3 and selected:
            category, count = max(distribution.items(), key=lambda item: item[1])
            if count / len(selected) > 0.6:
                warnings.append(f"{category} equipment is overrepresented.")
        if len(selected) >= 5 and available_categories & {"machine", "cable"}:
            if not distribution.get("machine") and not distribution.get("cable"):
                warnings.append("No machine or cable exercise was selected.")
        if len(selected) >= 5 and "free_weight" in available_categories:
            if not distribution.get("free_weight"):
                warnings.append("No free-weight exercise was selected.")
        if len(selected) >= 5 and "bodyweight" in available_categories:
            has_core = any(
                exercise.muscle_group.value == "core" for exercise in selected
            )
            if not distribution.get("bodyweight") and not has_core:
                warnings.append("No bodyweight or core exercise was selected.")
        if (
            workout_type in {"conditioning", "full_body_conditioning"}
            and "cardio" in available_categories
            and not distribution.get("cardio")
        ):
            warnings.append(
                "Cardio equipment was available but no finisher was selected."
            )
        return warnings
