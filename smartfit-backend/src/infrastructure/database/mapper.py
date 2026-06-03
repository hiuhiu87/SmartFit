from src.domain.common.enums import (
    AuthProvider,
    DifficultyFeedback,
    EquipmentType,
    Goal,
    MuscleGroup,
    ReadinessCategory,
    ReadinessRecommendation,
    TrainingLevel,
    WorkoutSource,
    WorkoutStatus,
)
from src.domain.ai.entities import AIRequestLog, AIUsageDaily
from src.domain.exercise.entities import Exercise
from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.readiness.entities import ReadinessScore
from src.domain.user.entities import User, UserProfile
from src.domain.workout.entities import (
    WorkoutFeedback,
    WorkoutLog,
    WorkoutPlan,
    WorkoutPlanExercise,
    WorkoutSetLog,
)
from src.infrastructure.database.base import utcnow
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.models.ai_model import (
    AIRequestModel,
    AIUsageDailyModel,
)
from src.infrastructure.database.models.health_model import (
    HealthSummaryModel,
    ManualCheckinModel,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.user_model import UserModel, UserProfileModel
from src.infrastructure.database.models.workout_model import (
    WorkoutFeedbackModel,
    WorkoutLogModel,
    WorkoutPlanExerciseModel,
    WorkoutPlanModel,
    WorkoutSetLogModel,
)


def user_model_to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        auth_provider=AuthProvider(model.auth_provider),
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_domain_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id,
        email=entity.email,
        password_hash=entity.password_hash,
        auth_provider=entity.auth_provider.value,
        is_active=entity.is_active,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def user_profile_model_to_domain(model: UserProfileModel) -> UserProfile:
    return UserProfile(
        id=model.id,
        user_id=model.user_id,
        full_name=model.full_name,
        age=model.age,
        height_cm=model.height_cm,
        weight_kg=model.weight_kg,
        training_level=TrainingLevel(model.training_level),
        primary_goal=Goal(model.primary_goal),
        injuries=list(model.injuries),
        notes=model.notes,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def user_profile_domain_to_model(entity: UserProfile) -> UserProfileModel:
    return UserProfileModel(
        id=entity.id,
        user_id=entity.user_id,
        full_name=entity.full_name,
        age=entity.age,
        height_cm=entity.height_cm,
        weight_kg=entity.weight_kg,
        training_level=entity.training_level.value,
        primary_goal=entity.primary_goal.value,
        injuries=entity.injuries,
        notes=entity.notes,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def health_summary_model_to_domain(model: HealthSummaryModel) -> HealthSummary:
    return HealthSummary(
        id=model.id,
        user_id=model.user_id,
        date=model.date,
        sleep_hours=model.sleep_hours,
        sleep_efficiency=model.sleep_efficiency,
        resting_heart_rate=model.resting_heart_rate,
        heart_rate_variability=model.heart_rate_variability,
        steps=model.steps,
        active_energy_kcal=model.active_energy_kcal,
        source=model.source,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def health_summary_domain_to_model(entity: HealthSummary) -> HealthSummaryModel:
    return HealthSummaryModel(
        id=entity.id,
        user_id=entity.user_id,
        date=entity.date,
        sleep_hours=entity.sleep_hours,
        sleep_efficiency=entity.sleep_efficiency,
        resting_heart_rate=entity.resting_heart_rate,
        heart_rate_variability=entity.heart_rate_variability,
        steps=entity.steps,
        active_energy_kcal=entity.active_energy_kcal,
        source=entity.source,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def manual_checkin_model_to_domain(model: ManualCheckinModel) -> ManualCheckin:
    return ManualCheckin(
        id=model.id,
        user_id=model.user_id,
        date=model.date,
        energy=model.energy,
        soreness=model.soreness,
        stress=model.stress,
        motivation=model.motivation,
        sleep_quality=model.sleep_quality,
        notes=model.notes,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def manual_checkin_domain_to_model(entity: ManualCheckin) -> ManualCheckinModel:
    return ManualCheckinModel(
        id=entity.id,
        user_id=entity.user_id,
        date=entity.date,
        energy=entity.energy,
        soreness=entity.soreness,
        stress=entity.stress,
        motivation=entity.motivation,
        sleep_quality=entity.sleep_quality,
        notes=entity.notes,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def readiness_score_model_to_domain(model: ReadinessScoreModel) -> ReadinessScore:
    return ReadinessScore(
        id=model.id,
        user_id=model.user_id,
        date=model.date,
        score=model.score,
        category=ReadinessCategory(model.category),
        recommendation=ReadinessRecommendation(model.recommendation),
        confidence=model.confidence,
        explanation=model.explanation,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def readiness_score_domain_to_model(entity: ReadinessScore) -> ReadinessScoreModel:
    return ReadinessScoreModel(
        id=entity.id,
        user_id=entity.user_id,
        date=entity.date,
        score=entity.score,
        category=entity.category.value,
        recommendation=entity.recommendation.value,
        confidence=entity.confidence,
        explanation=entity.explanation,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def exercise_model_to_domain(model: ExerciseModel) -> Exercise:
    metadata = dict(model.exercise_metadata)
    return Exercise(
        id=model.id,
        slug=model.slug,
        name=model.name,
        description=model.description,
        muscle_group=MuscleGroup(model.muscle_group),
        equipment_type=EquipmentType(model.equipment_type),
        training_level=TrainingLevel(model.training_level),
        secondary_muscles=list(model.secondary_muscles or []),
        movement_type=model.movement_type,
        movement_pattern=model.movement_pattern or metadata.get("movement_pattern"),
        exercise_role=model.exercise_role or metadata.get("exercise_role"),
        fatigue_level=model.fatigue_level or metadata.get("fatigue_level"),
        joint_stress=model.joint_stress or metadata.get("joint_stress"),
        substitution_group=model.substitution_group
        or metadata.get("substitution_group"),
        instruction=model.instruction,
        safety_notes=model.safety_notes,
        instructions=list(model.instructions),
        metadata=metadata,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def exercise_domain_to_model(entity: Exercise) -> ExerciseModel:
    return ExerciseModel(
        id=entity.id,
        slug=entity.slug,
        name=entity.name,
        description=entity.description,
        muscle_group=entity.muscle_group.value,
        equipment_type=entity.equipment_type.value,
        training_level=entity.training_level.value,
        secondary_muscles=entity.secondary_muscles,
        movement_type=entity.movement_type,
        movement_pattern=entity.movement_pattern,
        exercise_role=entity.exercise_role,
        fatigue_level=entity.fatigue_level,
        joint_stress=entity.joint_stress,
        substitution_group=entity.substitution_group,
        instruction=entity.instruction,
        safety_notes=entity.safety_notes,
        instructions=entity.instructions,
        exercise_metadata=entity.metadata,
        is_active=entity.is_active,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def workout_plan_model_to_domain(model: WorkoutPlanModel) -> WorkoutPlan:
    return WorkoutPlan(
        id=model.id,
        user_id=model.user_id,
        target_date=model.target_date,
        title=model.title,
        goal=Goal(model.goal),
        focus=MuscleGroup(model.focus),
        status=WorkoutStatus(model.status),
        source=WorkoutSource(model.source),
        estimated_duration_minutes=model.estimated_duration_minutes,
        readiness_score=model.readiness_score,
        decision=model.decision,
        ai_reasoning_summary=model.ai_reasoning_summary,
        safety_note=model.safety_note,
        exercises=[],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def workout_plan_domain_to_model(entity: WorkoutPlan) -> WorkoutPlanModel:
    return WorkoutPlanModel(
        id=entity.id,
        user_id=entity.user_id,
        target_date=entity.target_date,
        title=entity.title,
        goal=entity.goal.value,
        focus=entity.focus.value,
        status=entity.status.value,
        source=entity.source.value,
        estimated_duration_minutes=entity.estimated_duration_minutes,
        readiness_score=entity.readiness_score,
        decision=entity.decision,
        ai_reasoning_summary=entity.ai_reasoning_summary,
        safety_note=entity.safety_note,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def workout_plan_exercise_model_to_domain(
    model: WorkoutPlanExerciseModel,
) -> WorkoutPlanExercise:
    return WorkoutPlanExercise(
        id=model.id,
        workout_plan_id=model.workout_plan_id,
        exercise_id=model.exercise_id,
        order_index=model.order_index,
        target_sets=model.target_sets,
        target_reps=model.target_reps,
        target_rpe=model.target_rpe,
        target_weight=model.target_weight,
        rest_seconds=model.rest_seconds,
        notes=model.notes,
        name=None,
        primary_muscle=None,
        equipment=None,
        logged_sets=[],
    )


def workout_plan_exercise_domain_to_model(
    entity: WorkoutPlanExercise,
) -> WorkoutPlanExerciseModel:
    return WorkoutPlanExerciseModel(
        id=entity.id,
        workout_plan_id=entity.workout_plan_id,
        exercise_id=entity.exercise_id,
        order_index=entity.order_index,
        target_sets=entity.target_sets,
        target_reps=entity.target_reps,
        target_rpe=entity.target_rpe,
        target_weight=entity.target_weight,
        rest_seconds=entity.rest_seconds,
        notes=entity.notes,
    )


def workout_log_model_to_domain(model: WorkoutLogModel) -> WorkoutLog:
    return WorkoutLog(
        id=model.id,
        workout_plan_id=model.workout_plan_id,
        user_id=model.user_id,
        title=None,
        focus_muscle=None,
        started_at=model.started_at,
        completed_at=model.completed_at,
        duration_minutes=model.duration_minutes,
        total_volume=model.total_volume,
        calories_burned=model.calories_burned,
        avg_heart_rate=model.avg_heart_rate,
        notes=model.notes,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def workout_log_domain_to_model(entity: WorkoutLog) -> WorkoutLogModel:
    return WorkoutLogModel(
        id=entity.id,
        workout_plan_id=entity.workout_plan_id,
        user_id=entity.user_id,
        started_at=entity.started_at,
        completed_at=entity.completed_at,
        duration_minutes=entity.duration_minutes,
        total_volume=entity.total_volume,
        calories_burned=entity.calories_burned,
        avg_heart_rate=entity.avg_heart_rate,
        notes=entity.notes,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def workout_set_log_model_to_domain(model: WorkoutSetLogModel) -> WorkoutSetLog:
    return WorkoutSetLog(
        id=model.id,
        workout_log_id=model.workout_log_id,
        workout_plan_exercise_id=model.workout_plan_exercise_id,
        set_number=model.set_number,
        reps_completed=model.reps_completed,
        weight_kg=model.weight_kg,
        rpe=model.rpe,
        completed=model.completed,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def workout_set_log_domain_to_model(entity: WorkoutSetLog) -> WorkoutSetLogModel:
    return WorkoutSetLogModel(
        id=entity.id,
        workout_log_id=entity.workout_log_id,
        workout_plan_exercise_id=entity.workout_plan_exercise_id,
        set_number=entity.set_number,
        reps_completed=entity.reps_completed,
        weight_kg=entity.weight_kg,
        rpe=entity.rpe,
        completed=entity.completed,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def workout_feedback_model_to_domain(model: WorkoutFeedbackModel) -> WorkoutFeedback:
    return WorkoutFeedback(
        id=model.id,
        workout_log_id=model.workout_log_id,
        difficulty_feedback=(
            DifficultyFeedback(model.difficulty_feedback)
            if model.difficulty_feedback is not None
            else None
        ),
        energy_after=model.energy_after,
        comments=model.comments,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def workout_feedback_domain_to_model(entity: WorkoutFeedback) -> WorkoutFeedbackModel:
    return WorkoutFeedbackModel(
        id=entity.id,
        workout_log_id=entity.workout_log_id,
        difficulty_feedback=(
            entity.difficulty_feedback.value
            if entity.difficulty_feedback is not None
            else None
        ),
        energy_after=entity.energy_after,
        comments=entity.comments,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def ai_usage_daily_model_to_domain(model: AIUsageDailyModel) -> AIUsageDaily:
    return AIUsageDaily(
        user_id=model.user_id,
        date=model.date,
        ai_workout_count=model.ai_workout_count,
        ai_chat_count=model.ai_chat_count,
        ai_replacement_count=model.ai_replacement_count,
        ai_weekly_report_count=model.ai_weekly_report_count,
        total_ai_count=model.total_ai_count,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def ai_request_log_domain_to_model(entity: AIRequestLog) -> AIRequestModel:
    created_at = entity.created_at or utcnow()
    return AIRequestModel(
        id=entity.id,
        user_id=entity.user_id,
        workout_plan_id=entity.workout_plan_id,
        request_type=entity.request_type,
        provider=entity.provider,
        model_name=entity.model_name,
        generation_mode=entity.generation_mode,
        status=entity.status,
        # Older Postgres schemas still enforce NOT NULL on these legacy columns.
        prompt=entity.prompt or "",
        response=entity.response or "",
        input_payload=entity.input_payload or {},
        output_payload=entity.output_payload or {},
        error_code=entity.error_code,
        error_message=entity.error_message,
        fallback_used=entity.fallback_used,
        latency_ms=entity.latency_ms,
        request_metadata=entity.metadata or {},
        created_at=created_at,
        updated_at=created_at,
    )
