from collections import defaultdict
from datetime import date as date_type
from datetime import datetime, timedelta, timezone
from statistics import mean
from uuid import UUID

from src.domain.training.entities import (
    ExercisePerformanceTrend,
    MuscleFatigueItem,
    SetLogWithExercise,
    TrainingLoadSummary,
    TrainingRecommendationContext,
)
from src.domain.training.repositories import TrainingRepository

LARGE_MUSCLES = {"legs", "back"}
MUSCLE_FOCUS = {
    "chest": "upper_body_push",
    "shoulders": "upper_body_push",
    "back": "upper_body_pull",
    "legs": "lower_body",
    "arms": "upper_body",
    "core": "full_body",
    "cardio": "full_body",
}
FOCUS_MUSCLES = {
    "upper_body_push": {"chest", "shoulders", "arms"},
    "upper_body_pull": {"back", "arms"},
    "upper_body": {"chest", "back", "shoulders", "arms"},
    "lower_body": {"legs", "core"},
    "full_body": {"chest", "back", "shoulders", "arms", "legs", "core"},
}


class TrainingLoadCalculator:
    def __init__(self, repository: TrainingRepository) -> None:
        self.repository = repository

    async def calculate_recent_load(
        self, user_id: UUID, days: int = 7, to_date: date_type | None = None
    ) -> TrainingLoadSummary:
        end_date = to_date or date_type.today()
        start_date = end_date - timedelta(days=days - 1)
        workouts = await self.repository.get_completed_workouts(
            user_id, start_date, end_date
        )
        set_logs = await self.repository.get_set_logs_with_exercise(
            user_id, start_date, end_date
        )
        metrics = await self.repository.get_workout_health_metrics(
            user_id, start_date, end_date
        )

        completed_sets = [item for item in set_logs if item.completed]
        total_sets = len(completed_sets)
        total_volume = sum(
            (item.weight_kg or 0) * (item.reps_completed or 0)
            for item in completed_sets
        )
        total_duration = sum(item.duration_minutes or 0 for item in metrics)
        rpes = [item.rpe for item in completed_sets if item.rpe is not None]
        energies = [
            item.active_energy_burned
            for item in metrics
            if item.active_energy_burned is not None
        ]
        heart_rates = [
            item.avg_heart_rate for item in metrics if item.avg_heart_rate is not None
        ]
        score = self.calculate_load_score(
            total_volume=total_volume,
            total_sets=total_sets,
            workout_count=len(workouts),
            total_duration_minutes=total_duration,
            avg_rpe=mean(rpes) if rpes else None,
            active_energy_burned=sum(energies) if energies else None,
        )
        return TrainingLoadSummary(
            user_id=user_id,
            from_date=start_date,
            to_date=end_date,
            total_volume=round(total_volume, 2),
            total_sets=total_sets,
            workout_count=len(workouts),
            total_duration_minutes=total_duration,
            avg_rpe=round(mean(rpes), 2) if rpes else None,
            active_energy_burned=round(sum(energies), 2) if energies else None,
            avg_heart_rate=round(mean(heart_rates), 2) if heart_rates else None,
            load_score=score,
            load_level=self.calculate_load_level(score),
        )

    def calculate_load_score(
        self,
        *,
        total_volume: float,
        total_sets: int,
        workout_count: int,
        total_duration_minutes: int,
        avg_rpe: float | None,
        active_energy_burned: float | None,
    ) -> float:
        set_component = min(total_sets / 45, 1.0) * 35
        volume_component = min(total_volume / 15000, 1.0) * 25
        frequency_component = min(workout_count / 5, 1.0) * 15
        duration_component = min(total_duration_minutes / 360, 1.0) * 15
        rpe_component = max((avg_rpe or 6) - 6, 0) / 4 * 10
        energy_component = min((active_energy_burned or 0) / 2500, 1.0) * 10
        return round(
            min(
                100.0,
                set_component
                + volume_component
                + frequency_component
                + duration_component
                + rpe_component
                + energy_component,
            ),
            2,
        )

    def calculate_load_level(self, load_score: float) -> str:
        if load_score >= 80:
            return "very_high"
        if load_score >= 60:
            return "high"
        if load_score >= 35:
            return "moderate"
        return "low"


class MuscleFatigueCalculator:
    def __init__(self, repository: TrainingRepository) -> None:
        self.repository = repository

    async def calculate_muscle_fatigue(
        self, user_id: UUID, days: int = 7, to_date: date_type | None = None
    ) -> list[MuscleFatigueItem]:
        end_date = to_date or date_type.today()
        start_date = end_date - timedelta(days=days - 1)
        set_logs = await self.repository.get_set_logs_with_exercise(
            user_id, start_date, end_date
        )
        by_muscle: dict[str, list[SetLogWithExercise]] = defaultdict(list)
        for item in set_logs:
            if not item.completed:
                continue
            muscles = [item.primary_muscle, *item.secondary_muscles]
            for muscle in {muscle for muscle in muscles if muscle}:
                by_muscle[muscle].append(item)

        fatigue: list[MuscleFatigueItem] = []
        for muscle, items in by_muscle.items():
            last_trained_at = max(
                (item.completed_at for item in items if item.completed_at is not None),
                default=None,
            )
            days_since = self._days_since(last_trained_at, end_date)
            recent_sets = len(items)
            recent_volume = sum(
                (item.weight_kg or 0) * (item.reps_completed or 0) for item in items
            )
            large_multiplier = 1.18 if muscle in LARGE_MUSCLES else 1.0
            base = min(100.0, (recent_sets * 5.5) + (recent_volume / 90))
            fatigue_score = round(
                min(100.0, base * self._decay_factor(days_since) * large_multiplier),
                2,
            )
            fatigue.append(
                MuscleFatigueItem(
                    muscle=muscle,
                    fatigue_score=fatigue_score,
                    last_trained_at=last_trained_at,
                    recent_sets=recent_sets,
                    recent_volume=round(recent_volume, 2),
                    recovery_status=self._recovery_status(fatigue_score),
                )
            )
        return sorted(fatigue, key=lambda item: item.fatigue_score, reverse=True)

    def _days_since(self, trained_at: datetime | None, to_date: date_type) -> int:
        if trained_at is None:
            return 999
        return max(0, (to_date - trained_at.date()).days)

    def _decay_factor(self, days_since: int) -> float:
        if days_since <= 0:
            return 1.0
        if days_since == 1:
            return 0.75
        if days_since == 2:
            return 0.5
        if days_since == 3:
            return 0.25
        return 0.1

    def _recovery_status(self, fatigue_score: float) -> str:
        if fatigue_score >= 75:
            return "high_fatigue"
        if fatigue_score >= 50:
            return "moderate_fatigue"
        if fatigue_score >= 25:
            return "recovering"
        return "ready"


class ExercisePerformanceAnalyzer:
    def analyze(
        self, history: list[SetLogWithExercise]
    ) -> ExercisePerformanceTrend | None:
        completed = [
            item
            for item in history
            if item.completed and item.reps_completed is not None
        ]
        if not completed:
            return None
        ordered = sorted(
            completed,
            key=lambda item: (
                item.completed_at or datetime.min.replace(tzinfo=timezone.utc),
                item.set_number,
            ),
        )
        last = ordered[-1]
        best = max(ordered, key=self._estimated_one_rep_max)
        recent = ordered[-3:]
        previous = ordered[-6:-3]
        trend = self._trend(recent, previous)
        suggested_weight, suggested_reps = self._suggest_next(last, recent, trend)
        return ExercisePerformanceTrend(
            exercise_id=last.exercise_id,
            exercise_name=last.exercise_name,
            trend=trend,
            last_weight=last.weight_kg,
            last_reps=last.reps_completed,
            best_weight=best.weight_kg,
            best_reps=best.reps_completed,
            suggested_next_weight=suggested_weight,
            suggested_next_reps=suggested_reps,
        )

    def _trend(
        self, recent: list[SetLogWithExercise], previous: list[SetLogWithExercise]
    ) -> str:
        if not previous:
            return "stable"
        recent_score = mean(self._estimated_one_rep_max(item) for item in recent)
        previous_score = mean(self._estimated_one_rep_max(item) for item in previous)
        if recent_score >= previous_score * 1.03:
            return "improving"
        if recent_score <= previous_score * 0.97:
            return "declining"
        return "stable"

    def _suggest_next(
        self,
        last: SetLogWithExercise,
        recent: list[SetLogWithExercise],
        trend: str,
    ) -> tuple[float | None, int | None]:
        high_rpe = [
            item.rpe for item in recent if item.rpe is not None and item.rpe >= 9
        ]
        avg_reps = mean(item.reps_completed or 0 for item in recent)
        weight = last.weight_kg
        reps = last.reps_completed
        if len(high_rpe) >= 2:
            return (round(weight * 0.95, 2) if weight else weight), reps
        if trend == "improving" and avg_reps >= 10:
            if weight and weight > 0:
                return round(weight + self._weight_increment(weight), 2), max(
                    6, reps or 8
                )
            return weight, (reps or 10) + 1
        return weight, reps

    def _estimated_one_rep_max(self, item: SetLogWithExercise) -> float:
        return (item.weight_kg or 0) * (1 + (item.reps_completed or 0) / 30)

    def _weight_increment(self, weight: float) -> float:
        return 2.5 if weight < 60 else 5.0


class TrainingRecommendationService:
    def __init__(
        self,
        load_calculator: TrainingLoadCalculator,
        fatigue_calculator: MuscleFatigueCalculator,
        performance_analyzer: ExercisePerformanceAnalyzer | None = None,
    ) -> None:
        self.load_calculator = load_calculator
        self.fatigue_calculator = fatigue_calculator
        self.repository = load_calculator.repository
        self.performance_analyzer = (
            performance_analyzer or ExercisePerformanceAnalyzer()
        )

    async def build_context(
        self, user_id: UUID, target_date: date_type
    ) -> TrainingRecommendationContext:
        recent_load = await self.load_calculator.calculate_recent_load(
            user_id, to_date=target_date
        )
        muscle_fatigue = await self.fatigue_calculator.calculate_muscle_fatigue(
            user_id, to_date=target_date
        )
        exercise_trends = await self._exercise_trends(user_id, target_date)
        avoid_focus = self._avoid_focus(muscle_fatigue)
        suggested_focus = self._suggest_focus(recent_load, muscle_fatigue, avoid_focus)
        return TrainingRecommendationContext(
            recent_load=recent_load,
            muscle_fatigue=muscle_fatigue,
            exercise_trends=exercise_trends,
            suggested_focus=suggested_focus,
            avoid_focus=avoid_focus,
            reason=self._reason(
                recent_load, muscle_fatigue, suggested_focus, avoid_focus
            ),
        )

    async def _exercise_trends(
        self, user_id: UUID, target_date: date_type
    ) -> list[ExercisePerformanceTrend]:
        start_date = target_date - timedelta(days=13)
        recent_sets = await self.repository.get_set_logs_with_exercise(
            user_id, start_date, target_date
        )
        latest_by_exercise: dict[UUID, datetime] = {}
        for item in recent_sets:
            if item.completed_at is None:
                continue
            current = latest_by_exercise.get(item.exercise_id)
            if current is None or item.completed_at > current:
                latest_by_exercise[item.exercise_id] = item.completed_at

        trends: list[ExercisePerformanceTrend] = []
        for exercise_id, _ in sorted(
            latest_by_exercise.items(), key=lambda pair: pair[1], reverse=True
        )[:5]:
            history = await self.repository.get_exercise_history(
                user_id, exercise_id, limit=12
            )
            trend = self.performance_analyzer.analyze(history)
            if trend is not None:
                trends.append(trend)
        return trends

    def _avoid_focus(self, fatigue: list[MuscleFatigueItem]) -> list[str]:
        focuses = {
            MUSCLE_FOCUS[item.muscle]
            for item in fatigue
            if item.fatigue_score >= 70 and item.muscle in MUSCLE_FOCUS
        }
        return sorted(focuses)

    def _suggest_focus(
        self,
        recent_load: TrainingLoadSummary,
        fatigue: list[MuscleFatigueItem],
        avoid_focus: list[str],
    ) -> str:
        if recent_load.load_score >= 80:
            return "recovery"
        fatigue_by_muscle = {item.muscle: item.fatigue_score for item in fatigue}
        candidates = ["upper_body_push", "upper_body_pull", "lower_body", "full_body"]
        available = [focus for focus in candidates if focus not in avoid_focus]
        if not available:
            return "recovery"
        return min(
            available,
            key=lambda focus: max(
                [fatigue_by_muscle.get(muscle, 0) for muscle in FOCUS_MUSCLES[focus]]
                or [0]
            ),
        )

    def _reason(
        self,
        recent_load: TrainingLoadSummary,
        fatigue: list[MuscleFatigueItem],
        suggested_focus: str,
        avoid_focus: list[str],
    ) -> str:
        if recent_load.load_score >= 80:
            return "Recent training load is very high, so recovery or reduced volume is preferred."
        if avoid_focus and fatigue:
            highest = fatigue[0]
            return (
                f"{highest.muscle.title()} fatigue is {highest.recovery_status} "
                "from recent training."
            )
        return f"{suggested_focus} has the best recovery profile from recent workouts."
