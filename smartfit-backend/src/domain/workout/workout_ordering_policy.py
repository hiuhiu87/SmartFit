from typing import Any


class WorkoutOrderingPolicy:
    def get_order_bucket(self, item: Any) -> int:
        roles = []
        patterns = []
        name = ""
        rest_seconds = None

        if isinstance(item, tuple):
            slot, exercise = item
            roles = list(slot.exercise_roles) + (
                [exercise.exercise_role] if exercise.exercise_role else []
            )
            patterns = list(slot.movement_patterns) + (
                [exercise.movement_pattern] if exercise.movement_pattern else []
            )
            name = exercise.name.lower()
            rest_seconds = slot.rest_seconds
        else:
            roles = [
                getattr(item, "exercise_role", ""),
                getattr(item, "role", ""),
            ]
            if hasattr(item, "exercise_roles"):
                roles.extend(getattr(item, "exercise_roles") or [])

            patterns = [
                getattr(item, "movement_pattern", ""),
                getattr(item, "movement_type", ""),
            ]
            if hasattr(item, "movement_patterns"):
                patterns.extend(getattr(item, "movement_patterns") or [])

            name = getattr(item, "name", "").lower()
            rest_seconds = getattr(item, "rest_seconds", None)

        roles_set = {str(r).strip().lower() for r in roles if r}
        patterns_set = {str(p).strip().lower() for p in patterns if p}

        is_activation = bool(
            {"warmup", "activation", "warmup_activation"} & roles_set
            or "activation" in name
            or "warm-up" in name
            or "warmup" in name
        )
        is_cooldown_mobility = (
            "mobility" in patterns_set
            and not is_activation
            and (
                "stretch" in name
                or "cooldown" in name
                or "cool-down" in name
                or "cooldown_mobility" in roles_set
                or rest_seconds == 0
            )
        )
        if is_cooldown_mobility:
            return 9

        if "cardio_finisher" in roles_set or (
            "cardio" in patterns_set and not is_activation
        ):
            return 8

        if "core" in patterns_set or "core" in roles_set:
            return 7

        if "corrective" in roles_set:
            return 6

        if "isolation" in roles_set:
            return 5

        if "accessory" in roles_set:
            return 4

        if "secondary_compound" in roles_set or "secondary" in roles_set:
            return 3

        if {
            "main_compound",
            "primary_compound",
            "primary",
        } & roles_set:
            return 2

        if is_activation or "mobility" in patterns_set:
            return 1

        return 4

    def sort_exercises(self, exercises: list[Any]) -> list[Any]:
        return sorted(exercises, key=self.get_order_bucket)

    def validate_order(self, exercises: list[Any]) -> list[str]:
        buckets = [self.get_order_bucket(item) for item in exercises]
        if buckets != sorted(buckets):
            return ["Exercises do not follow the required PT ordering."]
        return []
