from collections import Counter
from typing import Any

from src.domain.exercise.entities import Exercise
from src.domain.exercise.equipment_policy import get_equipment_category


class EquipmentDiversityPolicy:
    def get_equipment_category(self, equipment: str) -> str:
        return get_equipment_category(equipment)

    def category_distribution(
        self, selected_exercises: list[Exercise]
    ) -> dict[str, int]:
        return dict(
            Counter(
                get_equipment_category(exercise.equipment_type.value)
                for exercise in selected_exercises
            )
        )

    def diversity_bonus(
        self,
        candidate: Exercise,
        selected: list[Exercise],
        available_equipment: list[str],
        target_mix: dict[str, int],
    ) -> int:
        del available_equipment
        category = get_equipment_category(candidate.equipment_type.value)
        distribution = self.category_distribution(selected)
        target = target_mix.get(category, 0)
        if target <= 0:
            return 0
        if distribution.get(category, 0) < target:
            return 15
        return 0

    def overuse_penalty(
        self,
        candidate: Exercise,
        selected: list[Exercise],
        available_equipment: list[str],
        max_ratio: float = 0.6,
    ) -> int:
        category = get_equipment_category(candidate.equipment_type.value)
        distribution = self.category_distribution(selected)
        available_categories = {
            get_equipment_category(item) for item in available_equipment
        } - {"other"}
        if len(available_categories) < 3:
            return 0

        new_ratio = (distribution.get(category, 0) + 1) / (len(selected) + 1)

        if new_ratio > max_ratio:
            represented = set(distribution)
            alternatives_exist = (
                len(available_categories - represented - {category}) > 0
            )
            if alternatives_exist and new_ratio >= 0.75:
                return -40
            return -25
        return 0

    def validate_final_mix(
        self,
        selected: list[Exercise],
        available_equipment: list[str],
        workout_type: str,
    ) -> list[str]:
        warnings: list[str] = []
        available_categories = {
            get_equipment_category(item) for item in available_equipment
        } - {"other"}
        distribution = self.category_distribution(selected)

        if len(available_categories) >= 3 and selected:
            category, count = max(distribution.items(), key=lambda item: item[1])
            if count / len(selected) > 0.6:
                warnings.append(f"{category} equipment is overrepresented.")

        if len(selected) >= 5:
            if (
                "free_weight" in available_categories
                and distribution.get("free_weight", 0) < 2
            ):
                warnings.append("Less than 2 free-weight exercises selected.")

            has_machine_cable = (
                distribution.get("machine", 0) + distribution.get("cable", 0)
            ) >= 1
            if (available_categories & {"machine", "cable"}) and not has_machine_cable:
                warnings.append("No machine or cable exercise selected.")

            has_bodyweight = distribution.get("bodyweight", 0) >= 1
            has_core = any(ex.muscle_group.value == "core" for ex in selected)
            if "bodyweight" in available_categories and not (
                has_bodyweight or has_core
            ):
                warnings.append("No bodyweight or core exercise selected.")

        if (
            workout_type in {"conditioning", "full_body_conditioning"}
            and "cardio" in available_categories
            and not distribution.get("cardio")
        ):
            warnings.append(
                "Cardio equipment was available but no finisher was selected."
            )
        return warnings

    def resolve_diversity_if_needed(
        self,
        selected: list[Exercise],
        candidates_by_slot: list[list[Exercise]],
        constraints: dict[str, Any],
    ) -> list[Exercise]:
        available_equipment = constraints.get("available_equipment", [])
        workout_type = constraints.get("workout_type", "balanced")

        warnings = self.validate_final_mix(selected, available_equipment, workout_type)
        if (
            not warnings
            or not candidates_by_slot
            or len(selected) != len(candidates_by_slot)
        ):
            return selected

        result = list(selected)
        for i, _ in enumerate(result):
            current_warnings = self.validate_final_mix(
                result, available_equipment, workout_type
            )
            if not current_warnings:
                break

            best = result
            best_penalty = self._mix_penalty(result, available_equipment, workout_type)
            for alt in candidates_by_slot[i]:
                if alt.id in {e.id for e in result}:
                    continue
                test_selection = list(result)
                test_selection[i] = alt
                alt_warnings = self.validate_final_mix(
                    test_selection, available_equipment, workout_type
                )
                alt_penalty = self._mix_penalty(
                    test_selection, available_equipment, workout_type
                )
                if len(alt_warnings) <= len(current_warnings) and (
                    alt_penalty < best_penalty
                ):
                    best = test_selection
                    best_penalty = alt_penalty
            result = best
        return result

    def _mix_penalty(
        self,
        selected: list[Exercise],
        available_equipment: list[str],
        workout_type: str,
    ) -> float:
        if not selected:
            return 0
        distribution = self.category_distribution(selected)
        available_categories = {
            get_equipment_category(item) for item in available_equipment
        } - {"other"}
        largest_ratio = max(distribution.values()) / len(selected)
        penalty = max(0, largest_ratio - 0.6) * 100
        if len(selected) >= 5:
            if "free_weight" in available_categories:
                penalty += max(0, 2 - distribution.get("free_weight", 0)) * 10
            if available_categories & {"machine", "cable"}:
                if not distribution.get("machine") and not distribution.get("cable"):
                    penalty += 10
        if (
            workout_type in {"conditioning", "full_body_conditioning"}
            and "cardio" in available_categories
            and not distribution.get("cardio")
        ):
            penalty += 10
        return penalty
