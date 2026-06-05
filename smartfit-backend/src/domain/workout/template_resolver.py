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
        avoid_recent_repetition: bool = True,
    ) -> WorkoutTemplate:
        del goal

        if readiness_score < 40:
            return BUILT_IN_TEMPLATES["recovery_session"]

        focus = (focus_muscle or "full_body").strip().lower()
        if avoid_recent_repetition:
            focus = self._rotate_focus_if_needed(focus, recent_workouts or [])

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

    def _rotate_focus_if_needed(
        self,
        focus: str,
        recent_workouts: list[WorkoutPlan],
    ) -> str:
        if not recent_workouts:
            return focus

        recent_focuses = [self._workout_focus(item) for item in recent_workouts[:3]]
        recent_focuses = [item for item in recent_focuses if item]
        if not recent_focuses:
            return focus

        if focus == "upper_body" and recent_focuses[0] == "upper_body_push":
            return "upper_body_pull"
        if focus == "upper_body" and recent_focuses[0] == "upper_body_pull":
            return "upper_body_push"
        if (
            focus in {"full_body", "upper_body"}
            and recent_focuses.count("lower_body") == 0
        ):
            if sum(1 for item in recent_focuses if item.startswith("upper_body")) >= 2:
                return "lower_body"
        if focus == "full_body" and recent_focuses.count("lower_body") >= 2:
            return "upper_body"
        return focus

    def _workout_focus(self, workout: WorkoutPlan) -> str | None:
        raw_focus = getattr(workout, "focus_muscle", None)
        if raw_focus is None:
            focus = getattr(workout, "focus", None)
            raw_focus = getattr(focus, "value", focus)
        if raw_focus is None:
            return None

        focus = str(raw_focus).strip().lower()
        if focus in {"chest", "shoulders"}:
            return "upper_body_push"
        if focus == "back":
            return "upper_body_pull"
        if focus in {"legs", "lower_body"}:
            return "lower_body"
        if focus in {"upper_body_push", "upper_body_pull", "upper_body", "full_body"}:
            return focus
        return None
