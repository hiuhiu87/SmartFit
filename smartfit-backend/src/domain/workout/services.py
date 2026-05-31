from uuid import UUID, uuid4

from src.domain.common.enums import Goal, MuscleGroup, TrainingLevel, WorkoutDecision, WorkoutSource, WorkoutStatus
from src.domain.common.enums import WorkoutDecision
from src.domain.common.exceptions import ValidationError
from src.domain.exercise.entities import Exercise
from src.domain.workout.entities import WorkoutPlan, WorkoutPlanExercise, WorkoutSetLog


class RuleBasedWorkoutGenerator:
    SAFETY_NOTE = "Stop if you feel sharp pain, dizziness, or unusual discomfort."

    def generate(
        self,
        user_id: UUID,
        goal: str,
        training_level: str,
        readiness_score: int,
        readiness_recommendation: str,
        focus_muscle: str | None,
        available_time_minutes: int,
        exercises: list[Exercise],
        avoid_exercises: list[str],
    ) -> WorkoutPlan:
        del readiness_recommendation  # TODO: use richer recommendation shaping once AI planner is introduced.
        normalized_avoid = {item.strip().lower() for item in avoid_exercises if item.strip()}
        filtered = [
            exercise
            for exercise in exercises
            if exercise.is_active
            and exercise.slug.lower() not in normalized_avoid
            and exercise.name.lower() not in normalized_avoid
        ]

        focus = self._resolve_focus(focus_muscle)
        decision, exercise_target, target_sets, target_rpe, rest_seconds = self._prescription(
            readiness_score, available_time_minutes
        )
        selected = self._select_exercises(
            filtered, focus, training_level, decision, exercise_target
        )

        if readiness_score < 20 and not selected:
            decision = WorkoutDecision.REST_DAY.value

        reps = self._target_reps(goal, decision)
        plan_id = uuid4()
        plan_exercises = [
            WorkoutPlanExercise(
                id=uuid4(),
                workout_plan_id=plan_id,
                exercise_id=exercise.id,
                order_index=index + 1,
                target_sets=target_sets,
                target_reps=reps,
                target_rpe=target_rpe,
                target_weight=None,
                rest_seconds=rest_seconds,
                notes=exercise.safety_notes or exercise.instruction,
            )
            for index, exercise in enumerate(selected)
        ]

        goal_enum = Goal(goal)
        resolved_focus = focus if selected or focus != MuscleGroup.FULL_BODY else MuscleGroup.FULL_BODY
        return WorkoutPlan(
            id=plan_id,
            user_id=user_id,
            target_date=self._today_placeholder(),
            title=self._title(resolved_focus, goal_enum, decision, selected),
            goal=goal_enum,
            focus=resolved_focus,
            status=WorkoutStatus.GENERATED,
            source=WorkoutSource.FALLBACK,
            estimated_duration_minutes=available_time_minutes,
            readiness_score=readiness_score,
            decision=decision,
            ai_reasoning_summary="Generated using rule-based fallback based on your readiness and available equipment.",
            safety_note=self.SAFETY_NOTE,
            exercises=plan_exercises,
        )

    def _today_placeholder(self):
        from datetime import date

        return date.today()

    def _resolve_focus(self, focus_muscle: str | None) -> MuscleGroup:
        if focus_muscle is None:
            return MuscleGroup.FULL_BODY
        try:
            return MuscleGroup(focus_muscle)
        except ValueError:
            return MuscleGroup.FULL_BODY

    def _prescription(
        self, readiness_score: int, available_time_minutes: int
    ) -> tuple[str, int, int, int, int]:
        if readiness_score >= 80:
            return WorkoutDecision.NORMAL_VOLUME.value, min(6, max(4, available_time_minutes // 15)), 4, 8, 90
        if readiness_score >= 60:
            return WorkoutDecision.NORMAL_VOLUME.value, min(5, max(4, available_time_minutes // 15)), 3, 7, 75
        if readiness_score >= 40:
            return WorkoutDecision.REDUCED_VOLUME.value, min(4, max(3, available_time_minutes // 18)), 3, 6, 75
        if readiness_score >= 20:
            return WorkoutDecision.RECOVERY.value, min(4, max(3, available_time_minutes // 20)), 2, 4, 45
        return WorkoutDecision.RECOVERY.value, min(3, max(1, available_time_minutes // 20)), 1, 3, 30

    def _select_exercises(
        self,
        exercises: list[Exercise],
        focus: MuscleGroup,
        training_level: str,
        decision: str,
        exercise_target: int,
    ) -> list[Exercise]:
        filtered = exercises
        if training_level == TrainingLevel.BEGINNER.value:
            filtered = [
                exercise
                for exercise in filtered
                if exercise.training_level.value != TrainingLevel.ADVANCED.value
            ]

        if decision in {WorkoutDecision.RECOVERY.value, WorkoutDecision.REST_DAY.value}:
            priority = [
                exercise
                for exercise in filtered
                if exercise.muscle_group in {MuscleGroup.MOBILITY, MuscleGroup.CARDIO, MuscleGroup.FULL_BODY, MuscleGroup.CORE}
                or exercise.movement_type in {"cardio", "mobility"}
            ]
        else:
            priority = [exercise for exercise in filtered if exercise.muscle_group == focus]

        fallback = [
            exercise
            for exercise in filtered
            if exercise not in priority
            and exercise.muscle_group
            in {MuscleGroup.FULL_BODY, MuscleGroup.CORE, MuscleGroup.CARDIO, MuscleGroup.MOBILITY}
        ]
        remaining = [exercise for exercise in filtered if exercise not in priority and exercise not in fallback]

        ordered = self._sort_exercises(priority) + self._sort_exercises(fallback) + self._sort_exercises(remaining)

        selected: list[Exercise] = []
        seen: set[UUID] = set()
        for exercise in ordered:
            if exercise.id in seen:
                continue
            selected.append(exercise)
            seen.add(exercise.id)
            if len(selected) >= exercise_target:
                break
        return selected

    def _sort_exercises(self, exercises: list[Exercise]) -> list[Exercise]:
        movement_rank = {
            "push": 1,
            "pull": 2,
            "squat": 3,
            "hinge": 4,
            "full_body": 5,
            "cardio": 8,
            "mobility": 9,
        }
        return sorted(
            exercises,
            key=lambda exercise: (
                movement_rank.get(exercise.movement_type or "", 6),
                exercise.name.lower(),
            ),
        )

    def _target_reps(self, goal: str, decision: str) -> str:
        if decision == WorkoutDecision.RECOVERY.value:
            return "30-60 seconds" if goal == Goal.RECOVERY.value else "8-12"
        if goal == Goal.STRENGTH.value:
            return "5-8"
        if goal == Goal.ENDURANCE.value:
            return "12-20"
        if goal in {Goal.FAT_LOSS.value, Goal.GENERAL_HEALTH.value}:
            return "10-15"
        return "8-10"

    def _title(
        self,
        focus: MuscleGroup,
        goal: Goal,
        decision: str,
        exercises: list[Exercise],
    ) -> str:
        if decision == WorkoutDecision.RECOVERY.value:
            return "Full Body Recovery Session"
        equipment = next(
            (
                exercise.equipment_type.value.replace("_", " ").title()
                for exercise in exercises
                if exercise.equipment_type.value != "bodyweight"
            ),
            "",
        )
        focus_label = focus.value.replace("_", " ").title()
        if goal == Goal.STRENGTH:
            return f"{focus_label} Strength Day"
        if decision == WorkoutDecision.REDUCED_VOLUME.value:
            return f"{focus_label} Reduced Volume Day"
        if equipment:
            return f"{focus_label} {equipment} Day"
        return f"{focus_label} Session"


class WorkoutSafetyPolicy:
    def validate(self, plan: WorkoutPlan, readiness_score: float) -> None:
        decision = plan.decision or ""

        if readiness_score < 20 and decision not in {
            WorkoutDecision.RECOVERY.value,
            WorkoutDecision.REST_DAY.value,
        }:
            raise ValidationError(
                "Very low readiness only allows recovery or rest_day plans"
            )

        for exercise in plan.exercises:
            if exercise.target_sets > 5:
                raise ValidationError("Workout plan exceeds maximum target sets")
            if readiness_score < 40 and exercise.target_rpe > 7:
                raise ValidationError("Low readiness does not allow target_rpe above 7")
            if readiness_score < 40 and exercise.target_sets >= 5:
                raise ValidationError("Low readiness does not allow heavy volume")
        if not plan.exercises and decision != WorkoutDecision.REST_DAY.value:
            raise ValidationError("Unsafe workout generation blocked: no exercises for non-rest day")


class WorkoutVolumeCalculator:
    def calculate_total_volume(self, set_logs: list[WorkoutSetLog]) -> float:
        total = 0.0
        for set_log in set_logs:
            if not set_log.completed:
                continue
            if set_log.weight_kg is None or set_log.reps_completed is None:
                continue
            total += set_log.weight_kg * set_log.reps_completed
        return total
