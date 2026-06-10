from src.domain.common.enums import MuscleGroup, TrainingLevel
from src.domain.workout.entities import WorkoutPlan


class WorkoutVolumePolicy:
    def target_exercise_count(
        self,
        training_level: str,
        duration_minutes: int,
        workout_type: str,
        readiness_score: float,
    ) -> tuple[int, int]:
        level = (training_level or "").strip().lower()
        if level == TrainingLevel.BEGINNER.value:
            if duration_minutes <= 30:
                min_count, max_count = 3, 4
            elif duration_minutes <= 45:
                min_count, max_count = 4, 5
            else:
                min_count, max_count = 5, 5
        elif level == TrainingLevel.ADVANCED.value:
            if duration_minutes <= 30:
                min_count, max_count = 4, 5
            elif duration_minutes <= 45:
                min_count, max_count = 5, 6
            else:
                min_count, max_count = 6, 8
        else:  # Intermediate or default
            if duration_minutes <= 30:
                min_count, max_count = 4, 4
            elif duration_minutes <= 45:
                min_count, max_count = 5, 5
            else:
                min_count, max_count = 5, 7

        w_type = (workout_type or "").strip().lower()
        if w_type in {"strength", "power", "compound_heavy"}:
            min_count = max(3, min_count - 1)
            max_count = max(3, max_count - 1)
        elif w_type in {"conditioning", "hypertrophy", "isolation"}:
            max_count += 1

        if readiness_score < 20:
            return 2, 3
        if readiness_score < 40:
            min_count = max(2, min_count - 1)
            max_count = max(3, max_count - 1)

        return min_count, max_count

    def target_role_distribution(
        self,
        training_level: str,
        duration_minutes: int,
        workout_type: str,
        readiness_score: float,
    ) -> dict[str, tuple[int, int]]:
        dist = {
            "compound": (1, 2),
            "accessory": (2, 3),
            "isolation_core": (1, 2),
            "cardio": (0, 1),
        }
        if duration_minutes <= 30:
            dist["accessory"] = (1, 2)
            dist["isolation_core"] = (0, 1)

        w_type = (workout_type or "").strip().lower()
        if w_type == "strength":
            dist["compound"] = (2, 3)
            dist["accessory"] = (1, 2)
            dist["cardio"] = (0, 0)
        elif w_type == "conditioning":
            dist["compound"] = (0, 1)
            dist["accessory"] = (1, 2)
            dist["cardio"] = (1, 2)
        if training_level == TrainingLevel.BEGINNER.value:
            dist["compound"] = (1, min(2, dist["compound"][1]))
        if readiness_score < 40:
            dist["accessory"] = (max(0, dist["accessory"][0] - 1), 2)
            dist["isolation_core"] = (0, 1)

        return dist

    def max_quality_sets_per_muscle(
        self,
        training_level: str,
        muscle_size: str,
        readiness_score: float,
    ) -> int:
        muscle = (muscle_size or "").strip().lower()
        is_large = muscle in {
            "large",
            MuscleGroup.LEGS.value,
            MuscleGroup.BACK.value,
            MuscleGroup.CHEST.value,
            MuscleGroup.FULL_BODY.value,
        }

        level = (training_level or "").strip().lower()
        if level == TrainingLevel.BEGINNER.value:
            base_cap = 5 if is_large else 3
        elif level == TrainingLevel.ADVANCED.value:
            base_cap = 8 if is_large else 6
        else:  # Intermediate or default
            base_cap = 7 if is_large else 5

        if readiness_score >= 60:
            factor = 1.0
        elif readiness_score >= 40:
            factor = 0.7
        else:  # < 40
            factor = 0.5

        return max(1, int(round(base_cap * factor)))

    def adjust_sets_for_readiness(self, sets: int, readiness_score: float) -> int:
        if readiness_score >= 60:
            return sets
        if readiness_score >= 40:
            return max(1, sets - 1)
        if readiness_score >= 20:
            return min(2, sets)
        return 1

    def validate_volume(
        self,
        plan: WorkoutPlan,
        training_level: str = "intermediate",
        workout_type: str = "balanced",
    ) -> list[str]:
        warnings: list[str] = []
        readiness = plan.readiness_score or 80.0
        duration = plan.estimated_duration_minutes or 45

        min_count, max_count = self.target_exercise_count(
            training_level, duration, workout_type, readiness
        )
        actual_count = len(plan.exercises)
        if actual_count < min_count and readiness >= 20:
            warnings.append(
                f"Workout has too few exercises ({actual_count}). Target is {min_count}-{max_count}."
            )
        elif actual_count > max_count:
            warnings.append(
                f"Workout has too many exercises ({actual_count}). Target is {min_count}-{max_count}."
            )

        muscle_sets: dict[str, int] = {}
        for exercise in plan.exercises:
            muscle = (exercise.primary_muscle or "").strip().lower()
            if not muscle:
                continue
            muscle_sets[muscle] = muscle_sets.get(muscle, 0) + exercise.target_sets

        for muscle, sets in muscle_sets.items():
            cap = self.max_quality_sets_per_muscle(training_level, muscle, readiness)
            if sets > cap:
                warnings.append(
                    f"Muscle group '{muscle}' exceeds session quality set cap: {sets}/{cap} sets."
                )

        for exercise in plan.exercises:
            is_cardio_interval = bool(
                exercise.target_reps
                and any(
                    term in exercise.target_reps.lower()
                    for term in ["fast", "easy", "minutes"]
                )
            )
            is_mobility = "mobility" in (exercise.primary_muscle or "").lower()
            if not is_cardio_interval and not is_mobility:
                if exercise.target_sets > 5:
                    warnings.append(
                        f"Exercise '{exercise.name}' has excessive sets ({exercise.target_sets} > 5)."
                    )

        return warnings
