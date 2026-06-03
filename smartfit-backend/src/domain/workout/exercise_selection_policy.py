from collections import Counter

from src.domain.common.enums import EquipmentType, TrainingLevel
from src.domain.exercise.entities import Exercise
from src.domain.workout.templates import WorkoutSlot


class ExerciseSelectionPolicy:
    def select_exercise_for_slot(
        self,
        slot: WorkoutSlot,
        candidates: list[Exercise],
        available_equipment: list[str],
        training_level: str,
        avoid_exercises: list[str],
        already_selected: list[Exercise],
        template_id: str | None = None,
    ) -> Exercise | None:
        selected_ids = {exercise.id for exercise in already_selected}
        normalized_avoid = {
            item.strip().lower() for item in avoid_exercises if item.strip()
        }
        equipment = self._normalize_equipment(available_equipment)
        group_counts = Counter(
            self._substitution_group(exercise) for exercise in already_selected
        )

        scored: list[tuple[int, str, Exercise]] = []
        for exercise in candidates:
            if exercise.id in selected_ids:
                continue
            if (
                exercise.slug.lower() in normalized_avoid
                or exercise.name.lower() in normalized_avoid
            ):
                continue
            if (
                exercise.equipment_type.value not in equipment
                and exercise.equipment_type.value != EquipmentType.BODYWEIGHT.value
            ):
                continue
            if (
                self._movement_pattern(exercise) not in slot.movement_patterns
                and exercise.muscle_group.value not in slot.primary_muscles
            ):
                continue

            score = self._score(
                slot=slot,
                exercise=exercise,
                available_equipment=equipment,
                training_level=training_level,
                avoid_exercises=normalized_avoid,
                group_counts=group_counts,
                template_id=template_id,
            )
            if score <= -50:
                continue
            scored.append((score, exercise.name.lower(), exercise))

        if not scored:
            return None
        return max(
            scored, key=lambda item: (item[0], self._difficulty_rank(item[2]), item[1])
        )[2]

    def _score(
        self,
        slot: WorkoutSlot,
        exercise: Exercise,
        available_equipment: set[str],
        training_level: str,
        avoid_exercises: set[str],
        group_counts: Counter[str],
        template_id: str | None,
    ) -> int:
        score = 0
        movement_pattern = self._movement_pattern(exercise)
        primary_muscle = exercise.muscle_group.value
        role = self._exercise_role(exercise)
        equipment = exercise.equipment_type.value
        substitution_group = self._substitution_group(exercise)

        if movement_pattern in slot.movement_patterns:
            score += 40
        if primary_muscle in slot.primary_muscles:
            score += 25
        if equipment in available_equipment:
            score += 20
        if role in slot.exercise_roles:
            score += 10
        if self._difficulty_allowed(exercise.training_level.value, training_level):
            score += 10
        if (
            training_level == TrainingLevel.BEGINNER.value
            and self._joint_stress(exercise) == "low"
        ):
            score += 5

        allowed_group_count = (
            2
            if template_id == "upper_pull_emphasis" and substitution_group == "row"
            else 1
        )
        if group_counts[substitution_group] >= allowed_group_count:
            score -= 30
        if (
            exercise.slug.lower() in avoid_exercises
            or exercise.name.lower() in avoid_exercises
        ):
            score -= 50
        if (
            equipment not in available_equipment
            and equipment != EquipmentType.BODYWEIGHT.value
        ):
            score -= 100
        if (
            training_level == TrainingLevel.BEGINNER.value
            and exercise.training_level.value == TrainingLevel.ADVANCED.value
        ):
            score -= 100
        return score

    def _normalize_equipment(self, equipment: list[str]) -> set[str]:
        normalized = {item.strip().lower() for item in equipment if item.strip()}
        normalized.add(EquipmentType.BODYWEIGHT.value)
        return normalized

    def _difficulty_allowed(self, exercise_level: str, training_level: str) -> bool:
        rank = {
            TrainingLevel.BEGINNER.value: 1,
            TrainingLevel.INTERMEDIATE.value: 2,
            TrainingLevel.ADVANCED.value: 3,
        }
        return rank.get(exercise_level, 1) <= rank.get(training_level, 1) + 1

    def _difficulty_rank(self, exercise: Exercise) -> int:
        return {
            TrainingLevel.BEGINNER.value: 3,
            TrainingLevel.INTERMEDIATE.value: 2,
            TrainingLevel.ADVANCED.value: 1,
        }.get(exercise.training_level.value, 0)

    def _movement_pattern(self, exercise: Exercise) -> str:
        if exercise.movement_pattern:
            return exercise.movement_pattern
        metadata_value = exercise.metadata.get("movement_pattern")
        if metadata_value:
            return metadata_value
        name = exercise.name.lower()
        movement = exercise.movement_type or ""
        if "curl" in name:
            return "elbow_flexion"
        if "triceps" in name or "extension" in name or "pushdown" in name:
            return "elbow_extension"
        if "rear delt" in name or "face pull" in name or "lateral raise" in name:
            return "rear_delt"
        if "pulldown" in name or "pull-up" in name or "chin" in name:
            return "vertical_pull"
        if "row" in name or movement == "pull":
            return "horizontal_pull"
        if "shoulder press" in name or "overhead press" in name:
            return "vertical_push"
        if (
            "push" in name
            or "bench press" in name
            or "chest press" in name
            or movement == "push"
        ):
            return "horizontal_push"
        if "lunge" in name:
            return "lunge"
        if "squat" in name or "leg press" in name:
            return "squat"
        if (
            "deadlift" in name
            or "hinge" in name
            or "hip thrust" in name
            or "bridge" in name
        ):
            return "hinge"
        if movement in {"core", "cardio", "mobility"}:
            return movement
        return "mobility" if exercise.muscle_group.value == "mobility" else "core"

    def _exercise_role(self, exercise: Exercise) -> str:
        if exercise.exercise_role:
            return exercise.exercise_role
        movement_pattern = self._movement_pattern(exercise)
        if movement_pattern in {"cardio"}:
            return "finisher"
        if movement_pattern in {"mobility", "core", "rear_delt"}:
            return "corrective"
        if movement_pattern in {"elbow_flexion", "elbow_extension"}:
            return "isolation"
        return (
            "secondary_compound"
            if exercise.training_level.value == TrainingLevel.BEGINNER.value
            else "main_compound"
        )

    def _joint_stress(self, exercise: Exercise) -> str:
        return (
            exercise.joint_stress or exercise.metadata.get("joint_stress") or "medium"
        )

    def _substitution_group(self, exercise: Exercise) -> str:
        if exercise.substitution_group:
            return exercise.substitution_group
        metadata_value = exercise.metadata.get("substitution_group")
        if metadata_value:
            return metadata_value
        movement_pattern = self._movement_pattern(exercise)
        if movement_pattern == "horizontal_pull":
            return "row"
        if (
            movement_pattern == "cardio"
            and exercise.equipment_type.value == "treadmill"
        ):
            return "treadmill_cardio"
        return movement_pattern
