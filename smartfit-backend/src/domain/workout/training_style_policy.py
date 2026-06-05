from dataclasses import replace

from src.domain.common.enums import TrainingStyle
from src.domain.exercise.entities import Exercise
from src.domain.workout.templates import WorkoutSlot, WorkoutTemplate


class TrainingStylePolicy:
    def adjust_slot_priority(
        self, template: WorkoutTemplate, training_style: str
    ) -> WorkoutTemplate:
        style = TrainingStyle(training_style)
        slots = [self._adjust_slot(slot, style) for slot in template.slots]

        if style == TrainingStyle.HYPERTROPHY:
            slots.sort(
                key=lambda item: (
                    0 if {"accessory", "isolation"} & set(item.exercise_roles) else 1
                )
            )
        elif style == TrainingStyle.STRENGTH:
            slots.sort(
                key=lambda item: (
                    0
                    if {"main_compound", "secondary_compound"}
                    & set(item.exercise_roles)
                    else 1
                )
            )
        elif style == TrainingStyle.CONDITIONING:
            slots.sort(
                key=lambda item: (
                    0 if {"cardio", "core"} & set(item.movement_patterns) else 1
                )
            )
        elif style == TrainingStyle.POSTURE:
            slots.sort(
                key=lambda item: (
                    0
                    if {"horizontal_pull", "vertical_pull", "rear_delt", "core"}
                    & set(item.movement_patterns)
                    else 1
                )
            )
        elif style == TrainingStyle.GLUTE_CORE:
            slots.sort(
                key=lambda item: (
                    0 if {"hinge", "lunge", "core"} & set(item.movement_patterns) else 1
                )
            )
        return replace(template, slots=slots)

    def score_exercise(self, exercise: Exercise, training_style: str) -> int:
        style = TrainingStyle(training_style)
        pattern = exercise.movement_pattern or exercise.movement_type or ""
        role = exercise.exercise_role or ""
        if style == TrainingStyle.HYPERTROPHY and role in {"accessory", "isolation"}:
            return 15
        if style == TrainingStyle.STRENGTH and role in {
            "main_compound",
            "secondary_compound",
        }:
            return 15
        if style == TrainingStyle.CONDITIONING and pattern in {
            "cardio",
            "core",
            "lunge",
        }:
            return 15
        if style == TrainingStyle.POSTURE and pattern in {
            "horizontal_pull",
            "vertical_pull",
            "rear_delt",
            "core",
        }:
            return 15
        if style == TrainingStyle.GLUTE_CORE and pattern in {"hinge", "lunge", "core"}:
            return 15
        if style == TrainingStyle.RETURNING:
            if (
                exercise.joint_stress == "low"
                and exercise.training_level.value == "beginner"
            ):
                return 15
        return 0

    def _adjust_slot(self, slot: WorkoutSlot, style: TrainingStyle) -> WorkoutSlot:
        if style == TrainingStyle.HYPERTROPHY:
            return replace(
                slot,
                reps="8-15" if "cardio" not in slot.movement_patterns else slot.reps,
                rest_seconds=min(slot.rest_seconds, 75),
            )
        if style == TrainingStyle.STRENGTH:
            is_compound = bool(
                {"main_compound", "secondary_compound"} & set(slot.exercise_roles)
            )
            return replace(
                slot,
                reps="5-8" if is_compound else slot.reps,
                rest_seconds=(
                    max(slot.rest_seconds, 120) if is_compound else slot.rest_seconds
                ),
            )
        if style == TrainingStyle.CONDITIONING:
            return replace(slot, rest_seconds=min(slot.rest_seconds, 60))
        if style == TrainingStyle.RETURNING:
            return replace(
                slot,
                min_sets=min(slot.min_sets, 3),
                max_sets=min(slot.max_sets, 3),
                target_rpe=min(slot.target_rpe, 6),
            )
        return slot
