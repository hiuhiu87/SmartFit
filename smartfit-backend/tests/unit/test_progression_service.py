from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.domain.common.enums import (
    EquipmentType,
    Goal,
    MuscleGroup,
    TrainingLevel,
)
from src.domain.exercise.entities import Exercise
from src.domain.progression.entities import (
    ExercisePerformanceHistory,
    ExerciseSessionPerformance,
    ProgressionAction,
    SetPerformance,
)
from src.domain.progression.services import ProgressionService
from src.domain.workout.services import RuleBasedWorkoutGenerator


def session(
    *,
    days_ago: int = 0,
    reps: list[int],
    weight: float | None = 20,
    rpes: list[int] | None = None,
) -> ExerciseSessionPerformance:
    rpe_values = rpes or [7] * len(reps)
    return ExerciseSessionPerformance(
        workout_log_id=uuid4(),
        completed_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        sets=[
            SetPerformance(
                weight=weight,
                reps=rep,
                rpe=rpe_values[index],
                completed=True,
            )
            for index, rep in enumerate(reps)
        ],
    )


def history(
    *,
    sessions: list[ExerciseSessionPerformance],
    equipment: str = "dumbbell",
    movement_type: str = "horizontal_push",
    exercise_id=None,
) -> ExercisePerformanceHistory:
    return ExercisePerformanceHistory(
        exercise_id=exercise_id or uuid4(),
        exercise_name="Dumbbell Bench Press",
        recent_sessions=sessions,
        equipment_type=equipment,
        movement_type=movement_type,
    )


def suggest(
    performance_history: ExercisePerformanceHistory,
    *,
    default_sets: int = 3,
    default_reps: str = "8-12",
    default_rpe: int = 7,
):
    return ProgressionService().suggest_next_prescription(
        history=performance_history,
        default_sets=default_sets,
        default_reps=default_reps,
        default_rpe=default_rpe,
        training_level="intermediate",
    )


def test_no_history_returns_no_data() -> None:
    suggestion = suggest(history(sessions=[]))

    assert suggestion.action == ProgressionAction.NO_DATA
    assert suggestion.suggested_weight is None
    assert suggestion.suggested_sets == 3
    assert suggestion.suggested_reps == "8-12"
    assert suggestion.suggested_rpe == 7
    assert suggestion.reason == "No previous data for this exercise."


def test_completed_upper_reps_suggests_increase_weight() -> None:
    suggestion = suggest(history(sessions=[session(reps=[12, 12, 12], weight=20)]))

    assert suggestion.action == ProgressionAction.INCREASE_WEIGHT
    assert suggestion.suggested_weight == 22
    assert suggestion.suggested_reps == "8"
    assert suggestion.reason == "You completed the top of the rep range last time."


def test_high_rpe_suggests_maintain() -> None:
    suggestion = suggest(
        history(sessions=[session(reps=[10, 10, 10], weight=20, rpes=[9, 9, 9])])
    )

    assert suggestion.action == ProgressionAction.MAINTAIN
    assert suggestion.suggested_weight == 20
    assert suggestion.reason == "You completed the work, but effort was high."


def test_missed_reps_suggests_reduce_weight() -> None:
    suggestion = suggest(history(sessions=[session(reps=[6, 7, 8], weight=20)]))

    assert suggestion.action == ProgressionAction.REDUCE_WEIGHT
    assert suggestion.suggested_weight == 18
    assert suggestion.reason == "You missed the minimum rep target last time."


def test_declining_recent_sessions_suggests_reduce_volume() -> None:
    performance_history = history(
        sessions=[
            session(days_ago=0, reps=[8, 8, 8], weight=20),
            session(days_ago=1, reps=[10, 10, 10], weight=20),
            session(days_ago=2, reps=[12, 12, 12], weight=20),
        ]
    )

    suggestion = suggest(performance_history)

    assert suggestion.action == ProgressionAction.REDUCE_VOLUME
    assert suggestion.suggested_sets == 2
    assert suggestion.suggested_rpe == 6
    assert suggestion.reason == "Recent performance suggests accumulated fatigue."


def test_low_readiness_blocks_increase_weight() -> None:
    exercise_id = uuid4()
    exercise = Exercise(
        id=exercise_id,
        slug="dumbbell-bench-press",
        name="Dumbbell Bench Press",
        muscle_group=MuscleGroup.CHEST,
        equipment_type=EquipmentType.DUMBBELL,
        training_level=TrainingLevel.BEGINNER,
        movement_type="horizontal_push",
        movement_pattern="horizontal_push",
        exercise_role="main_compound",
        is_active=True,
    )
    performance_history = history(
        exercise_id=exercise_id,
        sessions=[session(reps=[12, 12, 12], weight=20)],
    )

    plan = RuleBasedWorkoutGenerator().generate(
        user_id=uuid4(),
        goal=Goal.MUSCLE_GAIN.value,
        training_level=TrainingLevel.BEGINNER.value,
        readiness_score=55,
        readiness_recommendation="reduce_volume",
        workout_split="push",
        focus_muscle="upper_body_push",
        available_time_minutes=45,
        exercises=[exercise],
        avoid_exercises=[],
        available_equipment=["dumbbell", "bodyweight"],
        progression_histories={exercise_id: performance_history},
    )

    prescription = next(
        item for item in plan.exercises if item.exercise_id == exercise_id
    )
    assert prescription.target_weight == 20
    assert "Readiness is low" in (prescription.notes or "")


def test_bodyweight_progression_increases_reps() -> None:
    suggestion = suggest(
        history(
            sessions=[session(reps=[12, 12, 12], weight=None)],
            equipment="bodyweight",
        )
    )

    assert suggestion.action == ProgressionAction.INCREASE_REPS
    assert suggestion.suggested_weight is None
    assert suggestion.suggested_reps == "11-15"
