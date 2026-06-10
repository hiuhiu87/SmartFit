from collections import Counter

from src.domain.common.enums import EquipmentType, TrainingLevel
from src.domain.exercise.entities import Exercise
from src.domain.exercise.equipment_policy import get_equipment_category
from src.domain.workout.equipment_diversity_policy import EquipmentDiversityPolicy
from src.domain.workout.training_style_policy import TrainingStylePolicy
from src.domain.workout.templates import WorkoutSlot


class ExerciseSelectionPolicy:
    def __init__(
        self,
        diversity_policy: EquipmentDiversityPolicy | None = None,
        training_style_policy: TrainingStylePolicy | None = None,
    ) -> None:
        self.diversity_policy = diversity_policy or EquipmentDiversityPolicy()
        self.training_style_policy = training_style_policy or TrainingStylePolicy()

    def select_exercise_for_slot(
        self,
        slot: WorkoutSlot,
        candidates: list[Exercise],
        available_equipment: list[str],
        training_level: str,
        avoid_exercises: list[str],
        already_selected: list[Exercise],
        template_id: str | None = None,
        training_style: str = "balanced",
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
                already_selected=already_selected,
                training_style=training_style,
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
        already_selected: list[Exercise],
        training_style: str,
    ) -> int:
        score = 0
        movement_pattern = self._movement_pattern(exercise)
        primary_muscle = exercise.muscle_group.value
        role = self._exercise_role(exercise)
        equipment = exercise.equipment_type.value
        substitution_group = self._substitution_group(exercise)
        category = get_equipment_category(equipment)

        if movement_pattern in slot.movement_patterns:
            score += 40
        if primary_muscle in slot.primary_muscles:
            score += 25
        if equipment in available_equipment:
            score += 20
        if role in slot.exercise_roles:
            score += 20
        if self._difficulty_allowed(exercise.training_level.value, training_level):
            score += 10
        if category in slot.preferred_equipment_categories:
            score += 20
        score += self._slot_intent_score(slot.slot_type, exercise, category)
        score += self.training_style_policy.score_exercise(exercise, training_style)
        score += self.diversity_policy.diversity_bonus(
            exercise,
            already_selected,
            list(available_equipment),
            self._target_categories(slot),
        )
        score += self.diversity_policy.overuse_penalty(
            exercise,
            already_selected,
            list(available_equipment),
        )
        if (
            training_level == TrainingLevel.BEGINNER.value
            and self._joint_stress(exercise) == "low"
        ):
            score += 5

        allowed_group_count = 1
        if (
            template_id in {"upper_pull_emphasis", "upper_pull_focus"}
            and substitution_group == "row"
        ):
            allowed_group_count = 2
        if slot.slot_type in {
            "row_variation",
            "chest_supported_row",
            "cable_crunch",
            "captains_chair_leg_raise",
            "dumbbell_lateral_raise",
        }:
            allowed_group_count = 2
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

    def _target_categories(self, slot: WorkoutSlot) -> dict[str, int]:
        targets = {
            "free_weight": 2,
            "machine": 1,
            "cable": 1,
            "bodyweight": 1,
            "cardio": 0,
        }
        if "cardio" in slot.movement_patterns:
            targets["cardio"] = 1
        for category in slot.preferred_equipment_categories:
            targets[category] = max(1, targets.get(category, 0))
        return targets

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
        if any(
            term in name
            for term in ["crunch", "leg raise", "knee raise", "russian twist", "twist"]
        ):
            return "core"
        if any(
            term in name
            for term in ["treadmill", "bike", "cycle", "cycling", "elliptical", "rower"]
        ):
            return "cardio"
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
        if "calf" in name:
            return "calf_raise"
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
        if movement_pattern == "calf_raise":
            return "calf_raise"
        if (
            movement_pattern == "cardio"
            and exercise.equipment_type.value == "treadmill"
        ):
            return "treadmill_cardio"
        return movement_pattern

    def _slot_intent_score(
        self, slot_type: str, exercise: Exercise, equipment_category: str
    ) -> int:
        name = exercise.name.lower()
        slug = exercise.slug.lower()
        text = f"{slug} {name}"

        intent_terms: dict[str, list[tuple[str, int]]] = {
            "incline_dumbbell_press": [
                ("incline", 35),
                ("dumbbell", 25),
                ("press", 15),
                ("push-up", -25),
                ("fly", -15),
            ],
            "machine_chest_press": [
                ("chest press", 35),
                ("machine", 25),
                ("lever", 20),
                ("push-up", -30),
                ("incline", -10),
            ],
            "seated_dumbbell_shoulder_press": [
                ("seated", 20),
                ("dumbbell", 20),
                ("shoulder press", 35),
                ("arnold", -10),
            ],
            "dumbbell_lateral_raise": [
                ("lateral raise", 45),
                ("side raise", 25),
                ("dumbbell", 20),
                ("rear", -20),
                ("press", -25),
            ],
            "cable_triceps_pushdown": [
                ("pushdown", 45),
                ("rope", 25),
                ("triceps", 25),
                ("cable", 25),
                ("dip", -20),
            ],
            "romanian_deadlift": [
                ("romanian", 45),
                ("rdl", 35),
                ("deadlift", 25),
                ("stiff", 15),
                ("swing", -25),
            ],
            "goblet_squat": [
                ("goblet", 45),
                ("squat", 25),
                ("dumbbell", 15),
                ("kettlebell", 15),
            ],
            "dumbbell_lunge": [
                ("dumbbell", 25),
                ("lunge", 35),
                ("jump", -25),
                ("twist", -15),
            ],
            "cable_crunch": [
                ("cable", 35),
                ("crunch", 40),
                ("plank", -30),
                ("twist", -10),
            ],
            "captains_chair_leg_raise": [
                ("captain", 45),
                ("leg raise", 35),
                ("knee raise", 25),
                ("hanging", -10),
                ("crunch", -20),
            ],
            "wide_lat_pulldown": [
                ("lat pulldown", 45),
                ("wide", 20),
                ("pulldown", 35),
                ("pull-up", -10),
            ],
            "close_grip_lat_pulldown": [
                ("lat pulldown", 40),
                ("close", 25),
                ("reverse", 15),
                ("pulldown", 30),
            ],
            "row_variation": [
                ("row", 35),
                ("barbell", 20),
                ("dumbbell", 20),
                ("upright", -30),
            ],
            "chest_supported_row": [
                ("chest supported", 50),
                ("incline row", 30),
                ("row", 25),
                ("barbell", -5),
            ],
            "rear_delt_fly": [
                ("rear delt", 45),
                ("fly", 30),
                ("face pull", 25),
                ("lateral raise", -20),
            ],
            "dumbbell_biceps_curl": [
                ("dumbbell", 25),
                ("bicep", 25),
                ("biceps", 25),
                ("curl", 30),
                ("hammer", -20),
                ("lunge", -30),
            ],
            "leg_press": [
                ("leg press", 55),
                ("sled", 25),
                ("smith", 10),
                ("squat", -10),
            ],
            "kettlebell_or_dumbbell_swing": [
                ("swing", 50),
                ("kettlebell", 25),
                ("dumbbell", 15),
                ("deadlift", -15),
            ],
            "seated_calf_raise": [
                ("seated calf", 50),
                ("calf raise", 35),
                ("calf press", 20),
                ("stretch", -40),
            ],
            "weighted_russian_twist": [
                ("weighted", 25),
                ("russian twist", 45),
                ("twist", 25),
                ("cable", 10),
                ("stretch", -30),
            ],
            "dumbbell_arnold_press": [
                ("arnold", 50),
                ("dumbbell", 25),
                ("press", 20),
            ],
            "dumbbell_hammer_curl": [
                ("hammer", 50),
                ("dumbbell", 25),
                ("curl", 25),
                ("lunge", -30),
            ],
            "overhead_cable_triceps_extension": [
                ("overhead", 35),
                ("cable", 35),
                ("triceps", 25),
                ("extension", 25),
                ("pushdown", -20),
                ("dip", -30),
            ],
            "zone2_cardio": [
                ("incline", 25),
                ("walk", 25),
                ("treadmill", 30),
                ("bike", 20),
                ("elliptical", 15),
            ],
            "bike_hiit": [
                ("bike", 45),
                ("cycle", 35),
                ("cycling", 35),
                ("treadmill", -10),
            ],
        }

        score = 0
        for term, value in intent_terms.get(slot_type, []):
            if term in text:
                score += value

        if (
            slot_type
            in {
                "machine_chest_press",
                "wide_lat_pulldown",
                "close_grip_lat_pulldown",
                "leg_press",
            }
            and equipment_category == "machine"
        ):
            score += 20
        if (
            slot_type
            in {
                "cable_triceps_pushdown",
                "overhead_cable_triceps_extension",
                "cable_crunch",
            }
            and equipment_category == "cable"
        ):
            score += 20
        if (
            slot_type
            in {
                "incline_dumbbell_press",
                "seated_dumbbell_shoulder_press",
                "dumbbell_lateral_raise",
                "romanian_deadlift",
                "goblet_squat",
                "dumbbell_lunge",
                "dumbbell_biceps_curl",
                "dumbbell_arnold_press",
                "dumbbell_hammer_curl",
            }
            and equipment_category == "free_weight"
        ):
            score += 15

        return score
