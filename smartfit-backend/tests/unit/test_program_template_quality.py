from uuid import uuid4

from src.domain.program.entities import PreferredSplit
from src.domain.program.program_template_factory import ProgramTemplateFactory
from src.domain.program.split_selection_policy import SplitSelectionPolicy


def test_five_day_split_uses_premium_upper_lower_structure() -> None:
    structure = SplitSelectionPolicy().get_split_structure(
        days_per_week=5,
        training_style="hypertrophy",
    )

    assert [focus for _, focus, _ in structure] == [
        "upper_push_focus",
        "lower_posterior_core",
        "upper_pull_focus",
        "lower_quad_core",
        "upper_arms_shoulders",
    ]


def test_five_day_program_templates_have_intentional_slots() -> None:
    templates = ProgramTemplateFactory().create_weekly_structure(
        program_id=uuid4(),
        goal="muscle_gain",
        days_per_week=5,
        level="intermediate",
        preferred_split=PreferredSplit.UPPER_LOWER,
        focus_areas=["shoulders", "core"],
        session_duration_minutes=60,
        training_style="hypertrophy",
    )

    slots_by_focus = {
        template.focus_type: [slot.slot_type for slot in template.slots]
        for template in templates
    }

    assert slots_by_focus["upper_push_focus"] == [
        "incline_dumbbell_press",
        "machine_chest_press",
        "seated_dumbbell_shoulder_press",
        "dumbbell_lateral_raise",
        "cable_triceps_pushdown",
        "zone2_cardio",
    ]
    assert slots_by_focus["lower_posterior_core"] == [
        "romanian_deadlift",
        "goblet_squat",
        "dumbbell_lunge",
        "cable_crunch",
        "captains_chair_leg_raise",
    ]
    assert slots_by_focus["upper_pull_focus"] == [
        "wide_lat_pulldown",
        "row_variation",
        "chest_supported_row",
        "rear_delt_fly",
        "dumbbell_biceps_curl",
        "bike_hiit",
    ]
    assert slots_by_focus["lower_quad_core"] == [
        "leg_press",
        "kettlebell_or_dumbbell_swing",
        "seated_calf_raise",
        "weighted_russian_twist",
        "zone2_cardio",
    ]
    assert slots_by_focus["upper_arms_shoulders"] == [
        "close_grip_lat_pulldown",
        "dumbbell_arnold_press",
        "dumbbell_lateral_raise",
        "dumbbell_hammer_curl",
        "overhead_cable_triceps_extension",
    ]

    upper_push = next(t for t in templates if t.focus_type == "upper_push_focus")
    lateral_raise = next(
        slot for slot in upper_push.slots if slot.slot_type == "dumbbell_lateral_raise"
    )
    assert lateral_raise.base_sets == 4
    assert lateral_raise.base_reps == "15"
