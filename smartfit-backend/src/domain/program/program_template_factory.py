from uuid import UUID, uuid4
from src.domain.common.exceptions import ValidationError
from src.domain.program.entities import (
    PreferredSplit,
    ProgramTemplateSlot,
    ProgramWorkoutTemplate,
)
from src.domain.program.split_selection_policy import SplitSelectionPolicy


class ProgramTemplateFactory:
    def __init__(self, split_policy: SplitSelectionPolicy | None = None) -> None:
        self.split_policy = split_policy or SplitSelectionPolicy()

    def create_weekly_structure(
        self,
        *,
        program_id: UUID,
        goal: str,
        days_per_week: int,
        level: str,
        preferred_split: PreferredSplit,
        focus_areas: list[str],
        session_duration_minutes: int,
        training_style: str = "balanced",
        equipment: list[str] | None = None,
    ) -> list[ProgramWorkoutTemplate]:
        del preferred_split
        if not 2 <= days_per_week <= 6:
            raise ValidationError("days_per_week must be between 2 and 6.")

        templates = []
        structure = self.split_policy.get_split_structure(days_per_week, training_style)
        for day_index, (title, focus, workout_type) in enumerate(structure):
            template_id = uuid4()
            templates.append(
                ProgramWorkoutTemplate(
                    id=template_id,
                    program_id=program_id,
                    day_index=day_index,
                    title=title,
                    focus_type=focus,
                    workout_type=workout_type,
                    estimated_duration_minutes=session_duration_minutes,
                    sequence_order=day_index + 1,
                    slots=self._slots(
                        template_id,
                        focus,
                        goal,
                        level,
                        focus_areas,
                        training_style,
                    ),
                )
            )
        return templates

    def _slots(
        self,
        template_id: UUID,
        focus: str,
        goal: str,
        level: str,
        focus_areas: list[str],
        training_style: str,
    ) -> list[ProgramTemplateSlot]:
        volume = 4 if level == "advanced" else 3
        reps = "4-6" if goal == "strength" else "8-12"
        premium_specs = self._premium_split_specs().get(focus)
        if premium_specs is not None:
            return [
                ProgramTemplateSlot(
                    id=uuid4(),
                    program_workout_template_id=template_id,
                    slot_order=index + 1,
                    slot_type=slot_type,
                    movement_patterns=movement_patterns,
                    primary_muscles=primary_muscles,
                    exercise_roles=roles,
                    required=required,
                    base_sets=sets,
                    base_reps=reps,
                    base_rest_seconds=rest_seconds,
                    base_rpe=6 if training_style == "returning" else target_rpe,
                    progression_rule="double_progression",
                )
                for index, (
                    slot_type,
                    movement_patterns,
                    primary_muscles,
                    roles,
                    required,
                    sets,
                    reps,
                    rest_seconds,
                    target_rpe,
                ) in enumerate(premium_specs)
            ]
        patterns = {
            "upper_push_balanced": [
                "horizontal_push",
                "vertical_push",
                "vertical_pull",
                "rear_delt",
                "elbow_extension",
                "cardio",
            ],
            "lower_core": ["squat", "hinge", "squat", "calf_raise", "core", "core"],
            "upper_pull_posture": [
                "horizontal_pull",
                "horizontal_pull",
                "horizontal_push",
                "rear_delt",
                "elbow_flexion",
                "cardio",
            ],
            "full_body_conditioning": [
                "lunge",
                "vertical_pull",
                "vertical_push",
                "hinge",
                "core",
                "cardio",
            ],
            "upper_body_pull": ["vertical_pull", "horizontal_pull", "hinge"],
            "upper_body_push": ["horizontal_push", "vertical_push"],
            "upper_push_focus": [
                "horizontal_push",
                "horizontal_push",
                "vertical_push",
                "rear_delt",
                "elbow_extension",
                "cardio",
            ],
            "lower_posterior_core": ["hinge", "squat", "lunge", "core", "core"],
            "upper_pull_focus": [
                "vertical_pull",
                "horizontal_pull",
                "horizontal_pull",
                "rear_delt",
                "elbow_flexion",
                "cardio",
            ],
            "lower_quad_core": ["squat", "hinge", "calf_raise", "core", "cardio"],
            "upper_arms_shoulders": [
                "vertical_pull",
                "vertical_push",
                "rear_delt",
                "elbow_flexion",
                "elbow_extension",
            ],
            "upper_body": ["horizontal_push", "horizontal_pull", "vertical_push"],
            "lower_body": ["squat", "hinge", "lunge"],
            "full_body": ["squat", "hinge", "push", "pull"],
        }.get(focus, ["compound"])
        if focus in {
            "upper_push_balanced",
            "lower_core",
            "upper_pull_posture",
            "full_body_conditioning",
        }:
            roles = [
                ["main_compound"],
                ["secondary_compound"],
                ["secondary_compound"],
                ["accessory", "isolation", "corrective"],
                ["accessory", "isolation", "corrective"],
                ["finisher"],
            ]
            return [
                ProgramTemplateSlot(
                    id=uuid4(),
                    program_workout_template_id=template_id,
                    slot_order=index + 1,
                    slot_type=f"{focus}_{index + 1}",
                    movement_patterns=[pattern],
                    primary_muscles=[],
                    exercise_roles=roles[index],
                    required=(
                        pattern != "cardio"
                        or (
                            focus == "full_body_conditioning"
                            and training_style != "strength"
                        )
                    ),
                    base_sets=3 if pattern != "cardio" else 1,
                    base_reps=(
                        "5-8" if training_style == "strength" and index < 2 else "8-15"
                    ),
                    base_rest_seconds=120 if training_style == "strength" else 60,
                    base_rpe=6 if training_style == "returning" else 7,
                    progression_rule="double_progression",
                )
                for index, pattern in enumerate(patterns)
            ]
        muscles = {
            "upper_body_pull": ["back", "arms"],
            "upper_body_push": ["chest", "shoulders", "arms"],
            "upper_body": ["chest", "back", "shoulders", "arms"],
            "lower_body": ["legs", "core"],
            "full_body": ["chest", "back", "legs", "core"],
        }.get(focus, ["full_body"])

        slot_specs = [
            ("primary_compound", patterns[:1], muscles, ["primary"], True),
            (
                "secondary_compound",
                patterns[1:2] or patterns[:1],
                muscles,
                ["secondary"],
                True,
            ),
            ("accessory", patterns[2:3] or patterns[:1], muscles, ["accessory"], True),
            ("accessory", [], focus_areas or muscles, ["accessory"], True),
            ("core_or_conditioning", ["carry", "core"], ["core"], ["finisher"], True),
            ("optional_accessory", [], muscles, ["accessory"], False),
        ]
        return [
            ProgramTemplateSlot(
                id=uuid4(),
                program_workout_template_id=template_id,
                slot_order=index + 1,
                slot_type=slot_type,
                movement_patterns=movement_patterns,
                primary_muscles=primary_muscles,
                exercise_roles=roles,
                required=required,
                base_sets=volume if index < 2 else max(2, volume - 1),
                base_reps=reps if index < 2 else "10-15",
                base_rest_seconds=120 if index < 2 else 60,
                base_rpe=8 if level == "advanced" else 7,
                progression_rule="double_progression",
            )
            for index, (
                slot_type,
                movement_patterns,
                primary_muscles,
                roles,
                required,
            ) in enumerate(slot_specs)
        ]

    def _premium_split_specs(
        self,
    ) -> dict[
        str,
        list[
            tuple[
                str,
                list[str],
                list[str],
                list[str],
                bool,
                int,
                str,
                int,
                int,
            ]
        ],
    ]:
        return {
            "upper_push_focus": [
                (
                    "incline_dumbbell_press",
                    ["horizontal_push"],
                    ["chest"],
                    ["main_compound", "secondary_compound"],
                    True,
                    3,
                    "12",
                    90,
                    7,
                ),
                (
                    "machine_chest_press",
                    ["horizontal_push"],
                    ["chest"],
                    ["secondary_compound"],
                    True,
                    3,
                    "12",
                    75,
                    7,
                ),
                (
                    "seated_dumbbell_shoulder_press",
                    ["vertical_push"],
                    ["shoulders"],
                    ["main_compound", "secondary_compound"],
                    True,
                    3,
                    "12",
                    90,
                    7,
                ),
                (
                    "dumbbell_lateral_raise",
                    ["rear_delt", "vertical_push"],
                    ["shoulders"],
                    ["isolation", "accessory", "corrective"],
                    True,
                    4,
                    "15",
                    45,
                    7,
                ),
                (
                    "cable_triceps_pushdown",
                    ["elbow_extension"],
                    ["arms"],
                    ["isolation", "accessory"],
                    True,
                    3,
                    "15",
                    45,
                    7,
                ),
                (
                    "zone2_cardio",
                    ["cardio"],
                    ["cardio"],
                    ["finisher"],
                    False,
                    1,
                    "15-20 minutes zone 2",
                    30,
                    6,
                ),
            ],
            "lower_posterior_core": [
                (
                    "romanian_deadlift",
                    ["hinge"],
                    ["legs"],
                    ["main_compound"],
                    True,
                    4,
                    "12",
                    105,
                    7,
                ),
                (
                    "goblet_squat",
                    ["squat"],
                    ["legs"],
                    ["secondary_compound"],
                    True,
                    3,
                    "12-15",
                    90,
                    7,
                ),
                (
                    "dumbbell_lunge",
                    ["lunge"],
                    ["legs"],
                    ["secondary_compound", "accessory"],
                    True,
                    3,
                    "12 each side",
                    75,
                    7,
                ),
                (
                    "cable_crunch",
                    ["core"],
                    ["core"],
                    ["isolation", "accessory", "corrective"],
                    True,
                    3,
                    "15",
                    45,
                    7,
                ),
                (
                    "captains_chair_leg_raise",
                    ["core"],
                    ["core"],
                    ["isolation", "accessory", "corrective"],
                    True,
                    3,
                    "12",
                    45,
                    7,
                ),
            ],
            "upper_pull_focus": [
                (
                    "wide_lat_pulldown",
                    ["vertical_pull"],
                    ["back"],
                    ["main_compound", "secondary_compound"],
                    True,
                    3,
                    "12",
                    90,
                    7,
                ),
                (
                    "row_variation",
                    ["horizontal_pull"],
                    ["back"],
                    ["main_compound"],
                    True,
                    3,
                    "12",
                    90,
                    7,
                ),
                (
                    "chest_supported_row",
                    ["horizontal_pull"],
                    ["back"],
                    ["secondary_compound"],
                    True,
                    3,
                    "12",
                    75,
                    7,
                ),
                (
                    "rear_delt_fly",
                    ["rear_delt"],
                    ["shoulders"],
                    ["isolation", "corrective"],
                    True,
                    3,
                    "15",
                    45,
                    7,
                ),
                (
                    "dumbbell_biceps_curl",
                    ["elbow_flexion"],
                    ["arms"],
                    ["isolation", "accessory"],
                    True,
                    3,
                    "12",
                    45,
                    7,
                ),
                (
                    "bike_hiit",
                    ["cardio"],
                    ["cardio"],
                    ["finisher"],
                    False,
                    10,
                    "30s fast / 60s easy",
                    60,
                    7,
                ),
            ],
            "lower_quad_core": [
                (
                    "leg_press",
                    ["squat"],
                    ["legs"],
                    ["main_compound"],
                    True,
                    4,
                    "12",
                    105,
                    7,
                ),
                (
                    "kettlebell_or_dumbbell_swing",
                    ["hinge"],
                    ["legs"],
                    ["secondary_compound", "main_compound"],
                    True,
                    3,
                    "20",
                    60,
                    7,
                ),
                (
                    "seated_calf_raise",
                    ["calf_raise"],
                    ["legs"],
                    ["isolation", "accessory"],
                    True,
                    4,
                    "15",
                    45,
                    7,
                ),
                (
                    "weighted_russian_twist",
                    ["core"],
                    ["core"],
                    ["isolation", "accessory", "corrective"],
                    True,
                    3,
                    "20",
                    45,
                    7,
                ),
                (
                    "zone2_cardio",
                    ["cardio"],
                    ["cardio"],
                    ["finisher"],
                    False,
                    1,
                    "15 minutes zone 2",
                    30,
                    6,
                ),
            ],
            "upper_arms_shoulders": [
                (
                    "close_grip_lat_pulldown",
                    ["vertical_pull"],
                    ["back"],
                    ["secondary_compound"],
                    True,
                    3,
                    "12",
                    75,
                    7,
                ),
                (
                    "dumbbell_arnold_press",
                    ["vertical_push"],
                    ["shoulders"],
                    ["secondary_compound"],
                    True,
                    3,
                    "12",
                    75,
                    7,
                ),
                (
                    "dumbbell_lateral_raise",
                    ["rear_delt", "vertical_push"],
                    ["shoulders"],
                    ["isolation", "accessory", "corrective"],
                    True,
                    3,
                    "15",
                    45,
                    7,
                ),
                (
                    "dumbbell_hammer_curl",
                    ["elbow_flexion"],
                    ["arms"],
                    ["isolation", "accessory"],
                    True,
                    3,
                    "12",
                    45,
                    7,
                ),
                (
                    "overhead_cable_triceps_extension",
                    ["elbow_extension"],
                    ["arms"],
                    ["isolation", "accessory"],
                    True,
                    3,
                    "12",
                    45,
                    7,
                ),
            ],
        }
