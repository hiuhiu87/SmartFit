from enum import StrEnum


class AuthProvider(StrEnum):
    EMAIL = "email"
    APPLE = "apple"
    GOOGLE = "google"


class Goal(StrEnum):
    MUSCLE_GAIN = "muscle_gain"
    FAT_LOSS = "fat_loss"
    STRENGTH = "strength"
    ENDURANCE = "endurance"
    GENERAL_HEALTH = "general_health"
    RECOVERY = "recovery"


class TrainingLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EquipmentType(StrEnum):
    DUMBBELL = "dumbbell"
    BARBELL = "barbell"
    BENCH = "bench"
    CABLE_MACHINE = "cable_machine"
    SMITH_MACHINE = "smith_machine"
    MACHINE = "machine"
    PULL_UP_BAR = "pull_up_bar"
    RESISTANCE_BAND = "resistance_band"
    TREADMILL = "treadmill"
    BODYWEIGHT = "bodyweight"
    NONE = "none"


class MuscleGroup(StrEnum):
    CHEST = "chest"
    BACK = "back"
    LEGS = "legs"
    SHOULDERS = "shoulders"
    ARMS = "arms"
    CORE = "core"
    FULL_BODY = "full_body"
    CARDIO = "cardio"
    MOBILITY = "mobility"


class ReadinessCategory(StrEnum):
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


class ReadinessRecommendation(StrEnum):
    TRAIN_HARD = "train_hard"
    TRAIN_NORMAL = "train_normal"
    REDUCE_VOLUME = "reduce_volume"
    RECOVERY = "recovery"
    REST = "rest"


class WorkoutDecision(StrEnum):
    NORMAL_VOLUME = "normal_volume"
    REDUCED_VOLUME = "reduced_volume"
    RECOVERY = "recovery"
    REST_DAY = "rest_day"


class WorkoutStatus(StrEnum):
    GENERATED = "generated"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkoutSource(StrEnum):
    AI = "ai"
    FALLBACK = "fallback"
    MANUAL = "manual"


class DifficultyFeedback(StrEnum):
    TOO_EASY = "too_easy"
    JUST_RIGHT = "just_right"
    TOO_HARD = "too_hard"


class AIRequestType(StrEnum):
    GENERATE_WORKOUT = "generate_workout"
    REPLACE_EXERCISE = "replace_exercise"
    CHAT = "chat"


class AIRequestStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    BLOCKED = "blocked"
    FALLBACK_USED = "fallback_used"


class SubscriptionPlan(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    TRIAL = "trial"
    EXPIRED = "expired"


class WorkoutStyle(StrEnum):
    BALANCED = "balanced"
    STRENGTH_FOCUSED = "strength_focused"
    HYPERTROPHY_FOCUSED = "hypertrophy_focused"
    RECOVERY_FOCUSED = "recovery_focused"
