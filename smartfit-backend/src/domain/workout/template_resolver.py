from src.domain.common.enums import TrainingLevel
from src.domain.workout.entities import WorkoutPlan
from src.domain.workout.templates import BUILT_IN_TEMPLATES, WorkoutTemplate


class WorkoutTemplateResolver:
    def resolve(
        self,
        focus_muscle: str | None,
        goal: str,
        training_level: str,
        readiness_score: int,
        recent_workouts: list[WorkoutPlan] | None = None,
    ) -> WorkoutTemplate:
        del goal
        # TODO: use recent_workouts to avoid repeating the same muscle groups too often.
        del recent_workouts

        if readiness_score < 40:
            return BUILT_IN_TEMPLATES["recovery_session"]

        focus = (focus_muscle or "full_body").strip().lower()
        if focus in {"upper_body_pull", "back"}:
            return BUILT_IN_TEMPLATES["upper_pull_emphasis"]
        if focus in {"upper_body_push", "chest", "shoulders"}:
            return BUILT_IN_TEMPLATES["upper_push_emphasis"]
        if focus == "upper_body":
            return BUILT_IN_TEMPLATES["balanced_upper"]
        if focus in {"legs", "lower_body"}:
            return BUILT_IN_TEMPLATES["lower_body_strength"]
        if focus == "full_body" or focus_muscle is None:
            if training_level == TrainingLevel.BEGINNER.value:
                return BUILT_IN_TEMPLATES["full_body_beginner"]
            return BUILT_IN_TEMPLATES["balanced_upper"]
        return BUILT_IN_TEMPLATES["full_body_beginner"]
