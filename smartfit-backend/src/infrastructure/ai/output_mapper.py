from uuid import uuid4

from src.domain.ai.entities import AIWorkoutGenerationContext, AIWorkoutGenerationResult
from src.domain.common.enums import Goal, MuscleGroup, WorkoutSource, WorkoutStatus
from src.domain.common.exceptions import AIExerciseMappingError
from src.domain.workout.entities import WorkoutPlan, WorkoutPlanExercise


class AIWorkoutOutputMapper:
    DEFAULT_SAFETY_NOTE = (
        "Stop if you feel sharp pain, dizziness, or unusual discomfort."
    )

    def to_workout_plan(
        self,
        result: AIWorkoutGenerationResult,
        context: AIWorkoutGenerationContext,
    ) -> WorkoutPlan:
        allowed_by_slug = {item.slug: item for item in context.allowed_exercises}
        plan_id = uuid4()
        exercises: list[WorkoutPlanExercise] = []
        for index, item in enumerate(result.exercises, start=1):
            allowed = allowed_by_slug.get(item.exercise_slug)
            if allowed is None:
                raise AIExerciseMappingError(
                    f"Cannot map AI exercise slug: {item.exercise_slug}"
                )
            exercises.append(
                WorkoutPlanExercise(
                    id=uuid4(),
                    workout_plan_id=plan_id,
                    exercise_id=allowed.exercise_id,
                    order_index=index,
                    target_sets=item.sets,
                    target_reps=item.reps,
                    target_rpe=item.rpe,
                    target_weight=item.target_weight,
                    rest_seconds=item.rest_seconds,
                    notes=item.notes,
                    name=allowed.name,
                    primary_muscle=allowed.primary_muscle,
                    equipment=allowed.equipment,
                )
            )

        focus = context.focus_muscle or "full_body"
        try:
            focus_enum = MuscleGroup(focus)
        except ValueError:
            focus_enum = MuscleGroup.FULL_BODY

        return WorkoutPlan(
            id=plan_id,
            user_id=context.user_id,
            target_date=context.target_date,
            title=result.workout_title,
            goal=Goal(context.goal),
            focus=focus_enum,
            status=WorkoutStatus.GENERATED,
            source=WorkoutSource.AI,
            estimated_duration_minutes=result.estimated_duration_minutes,
            readiness_score=context.readiness_score,
            decision=result.training_decision,
            ai_reasoning_summary=result.reasoning_summary,
            safety_note=result.safety_note or self.DEFAULT_SAFETY_NOTE,
            exercises=exercises,
        )
