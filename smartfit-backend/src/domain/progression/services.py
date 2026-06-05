import math
import re
from statistics import mean, median

from src.domain.progression.entities import (
    ExercisePerformanceHistory,
    ExerciseSessionPerformance,
    ProgressionAction,
    ProgressionSuggestion,
)


class ProgressionService:
    def suggest_next_prescription(
        self,
        history: ExercisePerformanceHistory,
        default_sets: int,
        default_reps: str,
        default_rpe: int,
        training_level: str,
    ) -> ProgressionSuggestion:
        rep_range = self._rep_range(default_reps)
        base = {
            "exercise_id": history.exercise_id,
            "suggested_sets": default_sets,
            "suggested_reps": default_reps,
            "suggested_rpe": default_rpe,
        }
        sessions = [
            session
            for session in history.recent_sessions
            if any(item.completed for item in session.sets)
        ]
        if not sessions:
            return ProgressionSuggestion(
                **base,
                suggested_weight=None,
                action=ProgressionAction.NO_DATA,
                reason="No previous data for this exercise.",
                confidence=0.0,
            )

        sessions = sorted(sessions, key=lambda item: item.completed_at, reverse=True)
        last = sessions[0]
        last_weight = self._session_weight(last)
        avg_rpe = self._average_rpe(last)

        fatigue_action = self._fatigue_action(sessions[:3])
        if fatigue_action is not None:
            action = fatigue_action
            return ProgressionSuggestion(
                **{
                    **base,
                    "suggested_sets": max(1, default_sets - 1),
                    "suggested_rpe": min(default_rpe, 6),
                },
                suggested_weight=last_weight,
                action=action,
                reason="Recent performance suggests accumulated fatigue.",
                confidence=self._confidence(len(sessions), training_level),
            )

        if rep_range is None:
            return self._non_standard_progression(
                history=history,
                last=last,
                last_weight=last_weight,
                default_sets=default_sets,
                default_reps=default_reps,
                default_rpe=default_rpe,
                training_level=training_level,
            )

        minimum_reps, upper_reps = rep_range
        missed_sets = [
            item
            for item in last.sets
            if not item.completed or item.reps is None or item.reps < minimum_reps
        ]
        if last.sets and len(missed_sets) / len(last.sets) > 0.5:
            return ProgressionSuggestion(
                **base,
                suggested_weight=self._reduced_weight(
                    last_weight, history.equipment_type
                ),
                action=ProgressionAction.REDUCE_WEIGHT,
                reason="You missed the minimum rep target last time.",
                confidence=self._confidence(len(sessions), training_level),
            )

        hit_target = len(last.sets) >= default_sets and all(
            item.completed and item.reps is not None and item.reps >= minimum_reps
            for item in last.sets
        )
        hit_upper = len(last.sets) >= default_sets and all(
            item.completed and item.reps is not None and item.reps >= upper_reps
            for item in last.sets
        )

        if hit_target and avg_rpe is not None and avg_rpe >= 9:
            return ProgressionSuggestion(
                **base,
                suggested_weight=last_weight,
                action=ProgressionAction.MAINTAIN,
                reason="You completed the work, but effort was high.",
                confidence=self._confidence(len(sessions), training_level),
            )

        if hit_upper and (avg_rpe is None or avg_rpe <= 8):
            if self._is_bodyweight(history):
                increase = 2 if training_level == "beginner" else 3
                return ProgressionSuggestion(
                    **{
                        **base,
                        "suggested_reps": self._format_rep_range(
                            minimum_reps + increase, upper_reps + increase
                        ),
                    },
                    suggested_weight=None,
                    action=ProgressionAction.INCREASE_REPS,
                    reason="You reached the top of the rep range last time.",
                    confidence=self._confidence(len(sessions), training_level),
                )
            if self._is_cardio(history):
                return ProgressionSuggestion(
                    **{
                        **base,
                        "suggested_reps": self._format_rep_range(
                            minimum_reps + 2, upper_reps + 2
                        ),
                    },
                    suggested_weight=None,
                    action=ProgressionAction.INCREASE_REPS,
                    reason="Your previous cardio effort was moderate.",
                    confidence=self._confidence(len(sessions), training_level),
                )
            return ProgressionSuggestion(
                **{**base, "suggested_reps": str(minimum_reps)},
                suggested_weight=self._increased_weight(
                    last_weight, history.equipment_type
                ),
                action=ProgressionAction.INCREASE_WEIGHT,
                reason="You completed the top of the rep range last time.",
                confidence=self._confidence(len(sessions), training_level),
            )

        return ProgressionSuggestion(
            **base,
            suggested_weight=None if self._is_bodyweight(history) else last_weight,
            action=ProgressionAction.MAINTAIN,
            reason="Maintain the current prescription and build consistency.",
            confidence=self._confidence(len(sessions), training_level),
        )

    def apply_readiness_guard(
        self,
        suggestion: ProgressionSuggestion,
        history: ExercisePerformanceHistory,
        readiness_score: int,
    ) -> ProgressionSuggestion:
        if (
            readiness_score >= 60
            or suggestion.action != ProgressionAction.INCREASE_WEIGHT
        ):
            return suggestion
        latest = max(
            history.recent_sessions,
            key=lambda item: item.completed_at,
            default=None,
        )
        return ProgressionSuggestion(
            exercise_id=suggestion.exercise_id,
            suggested_weight=self._session_weight(latest) if latest else None,
            suggested_sets=suggestion.suggested_sets,
            suggested_reps=suggestion.suggested_reps,
            suggested_rpe=suggestion.suggested_rpe,
            action=ProgressionAction.MAINTAIN,
            reason="Readiness is low, so maintain the previous weight today.",
            confidence=suggestion.confidence,
        )

    def _non_standard_progression(
        self,
        *,
        history: ExercisePerformanceHistory,
        last: ExerciseSessionPerformance,
        last_weight: float | None,
        default_sets: int,
        default_reps: str,
        default_rpe: int,
        training_level: str,
    ) -> ProgressionSuggestion:
        if self._is_cardio(history):
            duration = self._duration_progression(default_reps)
            avg_rpe = self._average_rpe(last)
            if duration is not None and (avg_rpe is None or avg_rpe <= 8):
                return ProgressionSuggestion(
                    exercise_id=history.exercise_id,
                    suggested_weight=None,
                    suggested_sets=default_sets,
                    suggested_reps=duration,
                    suggested_rpe=default_rpe,
                    action=ProgressionAction.INCREASE_REPS,
                    reason="Your previous cardio effort was moderate.",
                    confidence=self._confidence(
                        len(history.recent_sessions), training_level
                    ),
                )
        return ProgressionSuggestion(
            exercise_id=history.exercise_id,
            suggested_weight=None if self._is_cardio(history) else last_weight,
            suggested_sets=default_sets,
            suggested_reps=default_reps,
            suggested_rpe=default_rpe,
            action=ProgressionAction.MAINTAIN,
            reason="Maintain the current prescription and build consistency.",
            confidence=self._confidence(len(history.recent_sessions), training_level),
        )

    def _duration_progression(self, value: str) -> str | None:
        if not any(token in value.lower() for token in ("minute", "round")):
            return None
        numbers = [int(item) for item in re.findall(r"\d+", value)]
        if not numbers:
            return None
        replacements = iter(str(item + 2) for item in numbers[:2])
        return re.sub(
            r"\d+",
            lambda _: next(replacements),
            value,
            count=len(numbers[:2]),
        )

    def _fatigue_action(
        self, sessions: list[ExerciseSessionPerformance]
    ) -> ProgressionAction | None:
        if len(sessions) < 3:
            return None
        chronological = list(reversed(sessions))
        reps = [self._average_reps(item) for item in chronological]
        rpes = [self._average_rpe(item) for item in chronological]
        declining_reps = (
            all(value is not None for value in reps) and reps[0] > reps[1] >= reps[2]
        )
        high_rpe_count = sum(value is not None and value >= 9 for value in rpes)
        if high_rpe_count == 3:
            return ProgressionAction.DELOAD
        if declining_reps or high_rpe_count >= 2:
            return ProgressionAction.REDUCE_VOLUME
        return None

    def _rep_range(self, value: str) -> tuple[int, int] | None:
        if any(
            token in value.lower()
            for token in ("second", "minute", "round", "fast", "easy")
        ):
            return None
        numbers = [int(item) for item in re.findall(r"\d+", value)]
        if not numbers:
            return None
        if len(numbers) == 1:
            return numbers[0], numbers[0]
        return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])

    def _session_weight(self, session: ExerciseSessionPerformance) -> float | None:
        weights = [
            item.weight
            for item in session.sets
            if item.completed and item.weight is not None and item.weight > 0
        ]
        return round(float(median(weights)), 2) if weights else None

    def _average_reps(self, session: ExerciseSessionPerformance) -> float | None:
        values = [
            item.reps
            for item in session.sets
            if item.completed and item.reps is not None
        ]
        return mean(values) if values else None

    def _average_rpe(self, session: ExerciseSessionPerformance) -> float | None:
        values = [
            item.rpe for item in session.sets if item.completed and item.rpe is not None
        ]
        return mean(values) if values else None

    def _increased_weight(
        self, weight: float | None, equipment_type: str | None
    ) -> float | None:
        if weight is None or weight <= 0:
            return None
        increment = self._weight_increment(weight, equipment_type)
        target = weight * (1.025 if weight >= 60 else 1.05)
        return round(
            max(weight + increment, math.ceil(target / increment) * increment), 2
        )

    def _reduced_weight(
        self, weight: float | None, equipment_type: str | None
    ) -> float | None:
        if weight is None or weight <= 0:
            return None
        increment = self._weight_increment(weight, equipment_type)
        target = weight * 0.925
        rounded = math.floor(target / increment) * increment
        return round(max(increment, min(weight - increment, rounded)), 2)

    def _weight_increment(self, weight: float, equipment_type: str | None) -> float:
        if equipment_type == "dumbbell":
            return 1.0 if weight < 20 else 2.0
        if equipment_type == "barbell":
            return 2.5
        if equipment_type in {"machine", "cable_machine", "smith_machine"}:
            return 2.5 if weight < 50 else 5.0
        return 2.5

    def _is_bodyweight(self, history: ExercisePerformanceHistory) -> bool:
        return history.equipment_type in {"bodyweight", "none"}

    def _is_cardio(self, history: ExercisePerformanceHistory) -> bool:
        return history.movement_type == "cardio" or history.equipment_type in {
            "treadmill",
            "bike",
        }

    def _format_rep_range(self, minimum: int, maximum: int) -> str:
        return str(minimum) if minimum == maximum else f"{minimum}-{maximum}"

    def _confidence(self, session_count: int, training_level: str) -> float:
        base = min(0.95, 0.55 + min(session_count, 4) * 0.1)
        if training_level == "beginner":
            base -= 0.05
        return round(max(0.0, base), 2)
