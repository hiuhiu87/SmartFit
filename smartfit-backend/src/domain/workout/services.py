from src.domain.common.enums import WorkoutDecision
from src.domain.common.exceptions import ValidationError
from src.domain.workout.entities import WorkoutPlan


class WorkoutSafetyPolicy:
    def validate(self, plan: WorkoutPlan, readiness_score: float) -> None:
        decision = plan.decision or ""

        if readiness_score < 20 and decision not in {WorkoutDecision.RECOVERY.value, WorkoutDecision.REST_DAY.value}:
            raise ValidationError("Very low readiness only allows recovery or rest_day plans")

        for exercise in plan.exercises:
            if exercise.target_sets > 5:
                raise ValidationError("Workout plan exceeds maximum target sets")
            if readiness_score < 40 and exercise.target_rpe > 7:
                raise ValidationError("Low readiness does not allow target_rpe above 7")
            if readiness_score < 40 and exercise.target_sets >= 5:
                raise ValidationError("Low readiness does not allow heavy volume")
