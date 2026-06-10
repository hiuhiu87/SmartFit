from uuid import UUID, uuid4
from datetime import date
from src.domain.program.entities import ProgramWorkoutTemplate, ProgramPhase
from src.domain.workout.entities import WorkoutPlan, WorkoutPlanExercise
from src.domain.workout.templates import WorkoutTemplate, WorkoutSlot
from src.domain.common.enums import Goal, MuscleGroup, WorkoutStatus, WorkoutSource
from src.domain.user.entities import UserProfile
from src.domain.exercise.entities import Exercise
from src.domain.workout.services import (
    RuleBasedWorkoutGenerator,
    WorkoutSafetyPolicy,
)
from src.domain.workout.exercise_selection_policy import ExerciseSelectionPolicy
from src.domain.workout.workout_volume_policy import WorkoutVolumePolicy
from src.domain.workout.equipment_diversity_policy import EquipmentDiversityPolicy
from src.domain.workout.workout_ordering_policy import WorkoutOrderingPolicy
from src.domain.progression.services import ProgressionService


class ProgramWorkoutPlanner:
    def __init__(
        self,
        selection_policy: ExerciseSelectionPolicy | None = None,
        volume_policy: WorkoutVolumePolicy | None = None,
        diversity_policy: EquipmentDiversityPolicy | None = None,
        ordering_policy: WorkoutOrderingPolicy | None = None,
        safety_policy: WorkoutSafetyPolicy | None = None,
        progression_service: ProgressionService | None = None,
    ) -> None:
        self.selection_policy = selection_policy or ExerciseSelectionPolicy()
        self.volume_policy = volume_policy or WorkoutVolumePolicy()
        self.diversity_policy = diversity_policy or EquipmentDiversityPolicy()
        self.ordering_policy = ordering_policy or WorkoutOrderingPolicy()
        self.safety_policy = safety_policy or WorkoutSafetyPolicy()
        self.progression_service = progression_service or ProgressionService()
        self.workout_generator = RuleBasedWorkoutGenerator(
            selection_policy=self.selection_policy,
            progression_service=self.progression_service,
            diversity_policy=self.diversity_policy,
            volume_policy=self.volume_policy,
            ordering_policy=self.ordering_policy,
        )

    def generate_planned_workout(
        self,
        template: ProgramWorkoutTemplate,
        phase: ProgramPhase,
        user_profile: UserProfile,
        available_equipment: list[str],
        exercises: list[Exercise],
        avoid_exercises: list[str] | None = None,
        recent_workouts: list[WorkoutPlan] | None = None,
        progression_histories: dict[UUID, any] | None = None,
        training_style: str = "balanced",
        target_date: date | None = None,
    ) -> WorkoutPlan:
        avoid_exercises = avoid_exercises or []
        target_date = target_date or date.today()

        # 1. Map ProgramTemplateSlot to WorkoutSlot
        workout_slots = []
        for slot in template.slots:
            workout_slots.append(
                WorkoutSlot(
                    slot_type=slot.slot_type,
                    movement_patterns=slot.movement_patterns,
                    primary_muscles=slot.primary_muscles,
                    exercise_roles=slot.exercise_roles,
                    required=slot.required,
                    min_sets=slot.base_sets,
                    max_sets=slot.base_sets,
                    reps=slot.base_reps,
                    rest_seconds=slot.base_rest_seconds,
                    target_rpe=slot.base_rpe,
                    max_candidates=1,
                    preferred_equipment_categories=self._preferred_equipment_categories(
                        slot.slot_type
                    ),
                )
            )

        workout_template = WorkoutTemplate(
            id=template.focus_type,
            title=template.title,
            focus_type=template.focus_type,
            goal_tags=[user_profile.primary_goal.value],
            slots=workout_slots,
        )

        # 2. Filter candidate exercises using RuleBasedWorkoutGenerator._excluded_by_profile
        filtered = [
            exercise
            for exercise in exercises
            if exercise.is_active
            and not self.workout_generator._excluded_by_profile(
                exercise=exercise,
                goal=user_profile.primary_goal.value,
                training_level=user_profile.training_level.value,
                injuries=user_profile.injuries,
                training_style=training_style,
                movement_limitations=user_profile.movement_limitations,
                pain_areas=user_profile.pain_areas,
                pain_movements=user_profile.pain_movements,
            )
        ]

        # 3. Select exercises for slots
        normalized_equipment = self.workout_generator._normalize_equipment(
            available_equipment
        )
        selected_pairs = self.workout_generator._select_template_exercises(
            template=workout_template,
            exercises=filtered,
            available_equipment=normalized_equipment,
            training_level=user_profile.training_level.value,
            avoid_exercises=avoid_exercises,
            readiness_score=100,
            available_time_minutes=template.estimated_duration_minutes,
            training_style=training_style,
        )

        # 4. Equipment diversity
        selected_pairs = self.workout_generator._resolve_equipment_diversity(
            selected_pairs=selected_pairs,
            exercises=filtered,
            available_equipment=normalized_equipment,
            workout_type=workout_template.id,
            training_level=user_profile.training_level.value,
        )

        # 5. Fill to target
        selected_pairs = self.workout_generator._fill_to_target_count(
            template=workout_template,
            selected_pairs=selected_pairs,
            exercises=filtered,
            available_equipment=normalized_equipment,
            training_level=user_profile.training_level.value,
            avoid_exercises=avoid_exercises,
            readiness_score=100,
            available_time_minutes=template.estimated_duration_minutes,
            training_style=training_style,
        )

        # 6. Order
        if template.focus_type not in self._slot_ordered_focus_types():
            selected_pairs = self.workout_generator._order_selected_pairs(
                selected_pairs
            )

        # 7. Build plan exercises with phase volume, intensity, rpe modifications
        plan_id = uuid4()
        plan_exercises = []
        for index, (slot, exercise) in enumerate(selected_pairs):
            # Apply phase volume multiplier
            target_sets = max(1, round(slot.min_sets * phase.volume_multiplier))
            target_reps = slot.reps

            # Apply RPE modifier
            if phase.phase_type == "intensification":
                target_rpe = min(8, slot.target_rpe + phase.rpe_modifier)
            else:
                target_rpe = max(1, min(10, slot.target_rpe + phase.rpe_modifier))

            target_weight = None
            notes = self._programming_note(slot.slot_type, exercise.name)
            if exercise.safety_notes:
                notes = (
                    f"{notes} {exercise.safety_notes}"
                    if notes
                    else exercise.safety_notes
                )
            elif exercise.instruction and not notes:
                notes = exercise.instruction

            # Check progression history
            if progression_histories and exercise.id in progression_histories:
                history = progression_histories[exercise.id]
                suggestion = self.progression_service.suggest_next_prescription(
                    history=history,
                    default_sets=target_sets,
                    default_reps=target_reps,
                    default_rpe=target_rpe,
                    training_level=user_profile.training_level.value,
                )
                target_sets = suggestion.suggested_sets
                target_reps = suggestion.suggested_reps
                target_rpe = min(target_rpe, suggestion.suggested_rpe)
                if suggestion.suggested_weight is not None:
                    target_weight = (
                        suggestion.suggested_weight * phase.intensity_multiplier
                    )
                notes = self.workout_generator._progression_notes(notes, suggestion)

            plan_exercises.append(
                WorkoutPlanExercise(
                    id=uuid4(),
                    workout_plan_id=plan_id,
                    exercise_id=exercise.id,
                    order_index=index + 1,
                    target_sets=target_sets,
                    target_reps=target_reps,
                    target_rpe=target_rpe,
                    target_weight=target_weight,
                    rest_seconds=slot.rest_seconds,
                    notes=notes,
                    name=exercise.name,
                    primary_muscle=exercise.muscle_group.value,
                    equipment=exercise.equipment_type.value,
                )
            )

        # Apply muscle set caps
        self.workout_generator._apply_muscle_set_caps(
            plan_exercises,
            selected_pairs,
            user_profile.training_level.value,
            100,
        )

        resolved_focus = self.workout_generator._plan_focus(
            workout_template, template.focus_type
        )
        goal_enum = Goal(user_profile.primary_goal.value)
        title = f"{phase.name} - {template.title}"

        return WorkoutPlan(
            id=plan_id,
            user_id=user_profile.user_id,
            target_date=target_date,
            title=title,
            goal=goal_enum,
            focus=resolved_focus,
            status=WorkoutStatus.GENERATED,
            source=WorkoutSource.FALLBACK,
            estimated_duration_minutes=template.estimated_duration_minutes,
            readiness_score=100.0,
            decision="normal_volume",
            ai_reasoning_summary=f"Pre-generated for {phase.name}.",
            safety_note=self.workout_generator.SAFETY_NOTE,
            exercises=plan_exercises,
        )

    def _slot_ordered_focus_types(self) -> set[str]:
        return {
            "upper_push_focus",
            "lower_posterior_core",
            "upper_pull_focus",
            "lower_quad_core",
            "upper_arms_shoulders",
        }

    def _preferred_equipment_categories(self, slot_type: str) -> list[str]:
        machine_slots = {
            "machine_chest_press",
            "wide_lat_pulldown",
            "close_grip_lat_pulldown",
            "leg_press",
            "seated_calf_raise",
        }
        cable_slots = {
            "cable_triceps_pushdown",
            "overhead_cable_triceps_extension",
            "cable_crunch",
        }
        cardio_slots = {"zone2_cardio", "bike_hiit"}
        if slot_type in machine_slots:
            return ["machine"]
        if slot_type in cable_slots:
            return ["cable"]
        if slot_type in cardio_slots:
            return ["cardio"]
        return ["free_weight"]

    def _programming_note(self, slot_type: str, exercise_name: str) -> str:
        notes = {
            "incline_dumbbell_press": "Upper-chest priority: use a controlled incline press and stop 1-2 reps before form breaks.",
            "machine_chest_press": "Stable chest volume: use the machine path to press hard without irritating the shoulders.",
            "dumbbell_lateral_raise": "Keep the load light enough to lead with the elbows and avoid swinging.",
            "cable_triceps_pushdown": "Lock the upper arms in place and fully extend the elbows on each rep.",
            "romanian_deadlift": "Posterior-chain priority: hinge at the hips and keep the lats tight.",
            "cable_crunch": "Think ribs toward pelvis; progress by adding cable load, not by rushing reps.",
            "wide_lat_pulldown": "Pull elbows down toward the ribs and avoid leaning far back.",
            "chest_supported_row": "Keep the chest glued to the bench to bias upper-back work and reduce low-back fatigue.",
            "leg_press": "Quad focus: use a controlled range and avoid locking the knees hard at the top.",
            "kettlebell_or_dumbbell_swing": "Explosive hinge finisher: drive with hips, not a front raise.",
            "weighted_russian_twist": "Rotate through the torso under control; keep the ribs down.",
            "dumbbell_arnold_press": "Smooth shoulder hypertrophy press; keep the motion controlled through the rotation.",
            "overhead_cable_triceps_extension": "Bias the long head of the triceps with a smooth cable line.",
            "zone2_cardio": "Zone 2 finish: breathe steadily and keep the pace conversational.",
            "bike_hiit": "HIIT finish: repeat 30 seconds hard then 60 seconds easy for the prescribed rounds.",
        }
        return notes.get(slot_type, f"Planned slot: {exercise_name}.")
