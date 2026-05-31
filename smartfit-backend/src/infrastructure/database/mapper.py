from src.domain.common.enums import (
    AuthProvider,
    EquipmentType,
    Goal,
    MuscleGroup,
    ReadinessCategory,
    ReadinessRecommendation,
    TrainingLevel,
    WorkoutSource,
    WorkoutStatus,
)
from src.domain.exercise.entities import Exercise
from src.domain.health.entities import HealthSummary, ManualCheckin
from src.domain.readiness.entities import ReadinessScore
from src.domain.user.entities import User, UserProfile
from src.domain.workout.entities import WorkoutPlan
from src.infrastructure.database.models.exercise_model import ExerciseModel
from src.infrastructure.database.models.health_model import (
    HealthSummaryModel,
    ManualCheckinModel,
)
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.user_model import UserModel, UserProfileModel
from src.infrastructure.database.models.workout_model import WorkoutPlanModel


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
    return Exercise(
        id=model.id,
        slug=model.slug,
        name=model.name,
        description=model.description,
        muscle_group=MuscleGroup(model.muscle_group),
        equipment_type=EquipmentType(model.equipment_type),
        training_level=TrainingLevel(model.training_level),
        instructions=list(model.instructions),
        metadata=dict(model.exercise_metadata),
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
        instructions=entity.instructions,
        exercise_metadata=entity.metadata,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def workout_plan_model_to_domain(model: WorkoutPlanModel) -> WorkoutPlan:
    return WorkoutPlan(
        id=model.id,
        user_id=model.user_id,
        title=model.title,
        focus=MuscleGroup(model.focus),
        status=WorkoutStatus(model.status),
        source=WorkoutSource(model.source),
        readiness_score=model.readiness_score,
        decision=model.decision,
        exercises=[],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def workout_plan_domain_to_model(entity: WorkoutPlan) -> WorkoutPlanModel:
    return WorkoutPlanModel(
        id=entity.id,
        user_id=entity.user_id,
        title=entity.title,
        focus=entity.focus.value,
        status=entity.status.value,
        source=entity.source.value,
        readiness_score=entity.readiness_score,
        decision=entity.decision,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
