from datetime import date, timedelta
from uuid import UUID, uuid4

from src.domain.common.exceptions import ValidationError
from src.domain.program.entities import (
    PreferredSplit,
    ProgramTemplateSlot,
    ProgramWorkoutInstance,
    ProgramWorkoutStatus,
    ProgramWorkoutTemplate,
    TrainingProgram,
)


class ProgramTemplateFactory:
    STRUCTURES = {
        2: [
            ("Full Body A", "full_body", "full_body"),
            ("Full Body B", "full_body", "full_body"),
        ],
        3: [
            ("Full Body Strength", "full_body", "full_body"),
            ("Upper Body", "upper_body", "upper_body"),
            ("Lower Body + Conditioning", "lower_body", "lower_body"),
        ],
        4: [
            ("Upper Push Balanced", "upper_push_balanced", "push"),
            ("Lower Body + Core", "lower_core", "lower_body"),
            ("Upper Pull Posture", "upper_pull_posture", "pull"),
            ("Full Body Conditioning", "full_body_conditioning", "conditioning"),
        ],
        5: [
            ("Push", "upper_body_push", "push"),
            ("Pull", "upper_body_pull", "pull"),
            ("Legs", "lower_body", "lower_body"),
            ("Upper Accessories", "upper_body", "upper_body"),
            ("Lower + Conditioning", "lower_body", "lower_body"),
        ],
    }

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
    ) -> list[ProgramWorkoutTemplate]:
        del preferred_split
        if days_per_week not in self.STRUCTURES:
            raise ValidationError("days_per_week must be between 2 and 5.")

        templates = []
        for day_index, (title, focus, workout_type) in enumerate(
            self.STRUCTURES[days_per_week]
        ):
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


class ProgramScheduler:
    DAY_OFFSETS = {
        2: [0, 3],
        3: [0, 2, 4],
        4: [0, 1, 3, 4],
        5: [0, 1, 2, 4, 5],
    }

    def calculate_position(
        self, program: TrainingProgram, target_date: date
    ) -> tuple[int, int | None]:
        elapsed = (target_date - program.start_date).days
        if elapsed < 0 or target_date > program.end_date:
            return 0, None
        week_number = (elapsed // 7) + 1
        offset = elapsed % 7
        offsets = self.DAY_OFFSETS[program.days_per_week]
        day_index = offsets.index(offset) if offset in offsets else None
        return week_number, day_index

    def scheduled_date(
        self, program: TrainingProgram, week_number: int, day_index: int
    ) -> date:
        return (
            program.start_date
            + timedelta(weeks=week_number - 1)
            + timedelta(days=self.DAY_OFFSETS[program.days_per_week][day_index])
        )

    def build_instance(
        self,
        program: TrainingProgram,
        template: ProgramWorkoutTemplate,
        target_date: date,
    ) -> ProgramWorkoutInstance:
        week_number, day_index = self.calculate_position(program, target_date)
        if day_index is None or day_index != template.day_index:
            raise ValidationError("No program workout is scheduled for this date.")
        return ProgramWorkoutInstance(
            id=uuid4(),
            program_id=program.id,
            program_workout_template_id=template.id,
            user_id=program.user_id,
            scheduled_date=target_date,
            week_number=week_number,
            day_index=day_index,
            actual_workout_plan_id=None,
            status=ProgramWorkoutStatus.SCHEDULED,
        )
