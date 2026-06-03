from uuid import UUID, uuid4

from src.domain.common.enums import (
    EquipmentType,
    Goal,
    MuscleGroup,
    TrainingLevel,
    WorkoutDecision,
    WorkoutSource,
    WorkoutStatus,
)
from src.domain.common.exceptions import ValidationError
from src.domain.exercise.entities import Exercise
from src.domain.workout.exercise_selection_policy import ExerciseSelectionPolicy
from src.domain.workout.entities import WorkoutPlan, WorkoutPlanExercise, WorkoutSetLog
from src.domain.workout.template_resolver import WorkoutTemplateResolver
from src.domain.workout.templates import WorkoutSlot, WorkoutTemplate


class RuleBasedWorkoutGenerator:
    SAFETY_NOTE = "Stop if you feel sharp pain, dizziness, or unusual discomfort."

    def __init__(
        self,
        template_resolver: WorkoutTemplateResolver | None = None,
        selection_policy: ExerciseSelectionPolicy | None = None,
    ) -> None:
        self.template_resolver = template_resolver or WorkoutTemplateResolver()
        self.selection_policy = selection_policy or ExerciseSelectionPolicy()

    def generate(
        self,
        user_id: UUID,
        goal: str,
        training_level: str,
        readiness_score: int,
        readiness_recommendation: str,
        workout_split: str,
        focus_muscle: str | None,
        available_time_minutes: int,
        exercises: list[Exercise],
        avoid_exercises: list[str],
        available_equipment: list[str] | None = None,
        injuries: list[str] | None = None,
    ) -> WorkoutPlan:
        available_equipment = self._normalize_equipment(available_equipment)
        template_focus = focus_muscle or self._focus_from_split(workout_split)
        template = self.template_resolver.resolve(
            focus_muscle=template_focus,
            goal=goal,
            training_level=training_level,
            readiness_score=readiness_score,
            recent_workouts=None,
        )
        decision = self._decision(readiness_score)
        if readiness_score < 20:
            template = self.template_resolver.resolve(
                focus_muscle="recovery",
                goal=Goal.RECOVERY.value,
                training_level=training_level,
                readiness_score=readiness_score,
                recent_workouts=None,
            )

        filtered = [
            exercise
            for exercise in exercises
            if exercise.is_active
            and not self._excluded_by_profile(
                exercise=exercise,
                goal=goal,
                training_level=training_level,
                injuries=injuries or [],
            )
        ]
        selected_pairs = self._select_template_exercises(
            template=template,
            exercises=filtered,
            available_equipment=available_equipment,
            training_level=training_level,
            avoid_exercises=avoid_exercises,
            readiness_score=readiness_score,
            available_time_minutes=available_time_minutes,
        )
        selected_pairs = self._fill_to_target_count(
            template=template,
            selected_pairs=selected_pairs,
            exercises=filtered,
            available_equipment=available_equipment,
            training_level=training_level,
            avoid_exercises=avoid_exercises,
            readiness_score=readiness_score,
            available_time_minutes=available_time_minutes,
        )
        selected_pairs = self._order_selected_pairs(selected_pairs)

        if readiness_score < 20 and not selected_pairs:
            decision = WorkoutDecision.REST_DAY.value

        plan_id = uuid4()
        plan_exercises = [
            WorkoutPlanExercise(
                id=uuid4(),
                workout_plan_id=plan_id,
                exercise_id=exercise.id,
                order_index=index + 1,
                target_sets=self._sets_for_slot(slot, readiness_score),
                target_reps=self._reps_for_slot(slot, goal, readiness_score),
                target_rpe=self._rpe_for_slot(slot, readiness_score),
                target_weight=None,
                rest_seconds=self._rest_for_slot(slot, goal, readiness_score),
                notes=exercise.safety_notes or exercise.instruction,
            )
            for index, (slot, exercise) in enumerate(selected_pairs)
        ]

        goal_enum = Goal(goal)
        resolved_focus = self._plan_focus(template, focus_muscle)
        return WorkoutPlan(
            id=plan_id,
            user_id=user_id,
            target_date=self._today_placeholder(),
            title=self._title(template, goal_enum, decision),
            goal=goal_enum,
            focus=resolved_focus,
            status=WorkoutStatus.GENERATED,
            source=WorkoutSource.FALLBACK,
            estimated_duration_minutes=self._planned_duration(
                available_time_minutes, readiness_score, decision
            ),
            readiness_score=readiness_score,
            decision=decision,
            ai_reasoning_summary=self._reasoning(
                template, readiness_score, readiness_recommendation
            ),
            safety_note=self.SAFETY_NOTE,
            exercises=plan_exercises,
        )

    def _today_placeholder(self):
        from datetime import date

        return date.today()

    def _resolve_focus(self, focus_muscle: str | None) -> MuscleGroup:
        if focus_muscle is None:
            return MuscleGroup.FULL_BODY
        try:
            return MuscleGroup(focus_muscle)
        except ValueError:
            return MuscleGroup.FULL_BODY

    def _decision(self, readiness_score: int) -> str:
        if readiness_score >= 80:
            return WorkoutDecision.NORMAL_VOLUME.value
        if readiness_score >= 60:
            return WorkoutDecision.NORMAL_VOLUME.value
        if readiness_score >= 40:
            return WorkoutDecision.REDUCED_VOLUME.value
        if readiness_score >= 20:
            return WorkoutDecision.RECOVERY.value
        return WorkoutDecision.RECOVERY.value

    def _select_template_exercises(
        self,
        template: WorkoutTemplate,
        exercises: list[Exercise],
        available_equipment: list[str],
        training_level: str,
        avoid_exercises: list[str],
        readiness_score: int,
        available_time_minutes: int,
    ) -> list[tuple[WorkoutSlot, Exercise]]:
        selected: list[Exercise] = []
        selected_pairs: list[tuple[WorkoutSlot, Exercise]] = []
        for slot in template.slots:
            if not self._should_include_slot(
                slot, readiness_score, available_time_minutes, available_equipment
            ):
                continue
            exercise = self.selection_policy.select_exercise_for_slot(
                slot=slot,
                candidates=exercises,
                available_equipment=available_equipment,
                training_level=training_level,
                avoid_exercises=avoid_exercises,
                already_selected=selected,
                template_id=template.id,
            )
            if exercise is None:
                if slot.required:
                    continue
                continue
            selected.append(exercise)
            selected_pairs.append((slot, exercise))
        return selected_pairs

    def _order_selected_pairs(
        self, selected_pairs: list[tuple[WorkoutSlot, Exercise]]
    ) -> list[tuple[WorkoutSlot, Exercise]]:
        compounds = [
            pair
            for pair in selected_pairs
            if self._slot_order_bucket(pair[0]) == 1
        ]
        accessories = [
            pair
            for pair in selected_pairs
            if self._slot_order_bucket(pair[0]) == 2
        ]
        finishers = [
            pair
            for pair in selected_pairs
            if self._slot_order_bucket(pair[0]) == 3
        ]
        return self._alternate_patterns(compounds) + accessories + finishers

    def _slot_order_bucket(self, slot: WorkoutSlot) -> int:
        if "cardio" in slot.movement_patterns:
            return 3
        if any(
            role in slot.exercise_roles
            for role in {"accessory", "isolation", "corrective", "finisher"}
        ):
            return 2
        return 1

    def _alternate_patterns(
        self, pairs: list[tuple[WorkoutSlot, Exercise]]
    ) -> list[tuple[WorkoutSlot, Exercise]]:
        remaining = list(pairs)
        ordered: list[tuple[WorkoutSlot, Exercise]] = []
        last_family: str | None = None
        while remaining:
            next_index = 0
            for index, (slot, _) in enumerate(remaining):
                family = self._movement_family(slot)
                if family != last_family:
                    next_index = index
                    break
            pair = remaining.pop(next_index)
            ordered.append(pair)
            last_family = self._movement_family(pair[0])
        return ordered

    def _movement_family(self, slot: WorkoutSlot) -> str:
        patterns = set(slot.movement_patterns)
        if patterns & {"horizontal_push", "vertical_push", "elbow_extension"}:
            return "push"
        if patterns & {"horizontal_pull", "vertical_pull", "elbow_flexion", "rear_delt"}:
            return "pull"
        if patterns & {"squat", "hinge", "lunge"}:
            return "lower"
        if patterns & {"core", "mobility"}:
            return "core"
        if "cardio" in patterns:
            return "cardio"
        return "other"

    def _fill_to_target_count(
        self,
        template: WorkoutTemplate,
        selected_pairs: list[tuple[WorkoutSlot, Exercise]],
        exercises: list[Exercise],
        available_equipment: list[str],
        training_level: str,
        avoid_exercises: list[str],
        readiness_score: int,
        available_time_minutes: int,
    ) -> list[tuple[WorkoutSlot, Exercise]]:
        target_count = self._target_exercise_count(
            template=template,
            readiness_score=readiness_score,
            available_time_minutes=available_time_minutes,
        )
        if len(selected_pairs) >= target_count:
            return selected_pairs

        selected = [exercise for _, exercise in selected_pairs]
        selected_slot_types = {slot.slot_type for slot, _ in selected_pairs}
        fill_slots = [
            slot
            for slot in self._fill_slots_for_template(template)
            if slot.slot_type not in selected_slot_types
            and self._should_include_slot(
                slot, readiness_score, available_time_minutes, available_equipment
            )
        ]

        for slot in fill_slots:
            if len(selected_pairs) >= target_count:
                break
            exercise = self.selection_policy.select_exercise_for_slot(
                slot=slot,
                candidates=exercises,
                available_equipment=available_equipment,
                training_level=training_level,
                avoid_exercises=avoid_exercises,
                already_selected=selected,
                template_id=template.id,
            )
            if exercise is None:
                continue
            selected.append(exercise)
            selected_pairs.append((slot, exercise))

        return selected_pairs

    def _target_exercise_count(
        self,
        template: WorkoutTemplate,
        readiness_score: int,
        available_time_minutes: int,
    ) -> int:
        if template.id == "recovery_session":
            if readiness_score < 20:
                return 2
            return 3
        if readiness_score >= 60:
            if available_time_minutes >= 60:
                return 6
            if available_time_minutes >= 45:
                return 5
            if available_time_minutes >= 30:
                return 4
            return 3
        if readiness_score >= 40:
            if available_time_minutes >= 60:
                return 5
            if available_time_minutes >= 45:
                return 4
            return 3
        if readiness_score >= 20:
            return 3
        return 2

    def _fill_slots_for_template(self, template: WorkoutTemplate) -> list[WorkoutSlot]:
        base_slots = list(template.slots)
        if template.id == "upper_pull_emphasis":
            base_slots.extend(
                [
                    self._programming_slot(
                        "extra_vertical_pull",
                        ["vertical_pull"],
                        ["back"],
                        ["secondary_compound", "main_compound"],
                        3,
                        "8-12",
                        75,
                        7,
                    ),
                    self._programming_slot(
                        "extra_core",
                        ["core"],
                        ["core"],
                        ["accessory", "corrective"],
                        2,
                        "30-45 seconds",
                        60,
                        7,
                    ),
                ]
            )
        elif template.id == "upper_push_emphasis":
            base_slots.extend(
                [
                    self._programming_slot(
                        "extra_chest_accessory",
                        ["horizontal_push"],
                        ["chest"],
                        ["secondary_compound", "accessory"],
                        3,
                        "10-12",
                        75,
                        7,
                    ),
                    self._programming_slot(
                        "extra_core",
                        ["core"],
                        ["core"],
                        ["accessory", "corrective"],
                        2,
                        "30-45 seconds",
                        60,
                        7,
                    ),
                ]
            )
        elif template.id == "balanced_upper":
            base_slots.extend(
                [
                    self._programming_slot(
                        "extra_rear_delt",
                        ["rear_delt"],
                        ["shoulders"],
                        ["corrective", "isolation"],
                        3,
                        "12-15",
                        60,
                        7,
                    ),
                    self._programming_slot(
                        "extra_arms",
                        ["elbow_flexion", "elbow_extension"],
                        ["arms"],
                        ["accessory", "isolation"],
                        3,
                        "10-12",
                        60,
                        7,
                    ),
                ]
            )
        elif template.id == "lower_body_strength":
            base_slots.extend(
                [
                    self._programming_slot(
                        "extra_core",
                        ["core"],
                        ["core"],
                        ["accessory", "corrective"],
                        2,
                        "30-45 seconds",
                        60,
                        7,
                    ),
                    self._programming_slot(
                        "extra_light_cardio",
                        ["cardio"],
                        ["cardio"],
                        ["finisher"],
                        6,
                        "Easy 5-10 minutes",
                        45,
                        6,
                        required=False,
                    ),
                ]
            )
        elif template.id == "full_body_beginner":
            base_slots.extend(
                [
                    self._programming_slot(
                        "extra_lunge",
                        ["lunge"],
                        ["legs"],
                        ["secondary_compound", "accessory"],
                        2,
                        "8-10 each side",
                        75,
                        7,
                    ),
                    self._programming_slot(
                        "extra_shoulders_or_arms",
                        ["rear_delt", "elbow_flexion", "elbow_extension"],
                        ["shoulders", "arms"],
                        ["accessory", "isolation", "corrective"],
                        2,
                        "10-15",
                        60,
                        7,
                    ),
                ]
            )
        return base_slots

    def _programming_slot(
        self,
        slot_type: str,
        movement_patterns: list[str],
        primary_muscles: list[str],
        exercise_roles: list[str],
        sets: int,
        reps: str,
        rest_seconds: int,
        target_rpe: int,
        required: bool = True,
    ) -> WorkoutSlot:
        return WorkoutSlot(
            slot_type=slot_type,
            movement_patterns=movement_patterns,
            primary_muscles=primary_muscles,
            exercise_roles=exercise_roles,
            required=required,
            min_sets=sets,
            max_sets=sets,
            reps=reps,
            rest_seconds=rest_seconds,
            target_rpe=target_rpe,
        )

    def _should_include_slot(
        self,
        slot: WorkoutSlot,
        readiness_score: int,
        available_time_minutes: int,
        available_equipment: list[str],
    ) -> bool:
        if slot.required:
            return True
        if readiness_score < 60:
            return False
        if available_time_minutes < 45:
            return False
        if "cardio" not in slot.movement_patterns:
            return True
        return any(
            item in available_equipment
            for item in {
                EquipmentType.TREADMILL.value,
                EquipmentType.BODYWEIGHT.value,
                "bike",
                "stationary_bike",
            }
        )

    def _sets_for_slot(self, slot: WorkoutSlot, readiness_score: int) -> int:
        if readiness_score >= 80:
            return min(slot.max_sets, 5)
        if readiness_score >= 60:
            return slot.min_sets
        if readiness_score >= 40:
            return max(1, slot.min_sets - 1)
        if readiness_score >= 20:
            return min(2, slot.min_sets)
        return 1

    def _rpe_for_slot(self, slot: WorkoutSlot, readiness_score: int) -> int:
        if readiness_score >= 80:
            return min(8, slot.target_rpe + 1)
        if readiness_score >= 60:
            return slot.target_rpe
        if readiness_score >= 40:
            return min(6, slot.target_rpe)
        if readiness_score >= 20:
            return min(4, slot.target_rpe)
        return min(3, slot.target_rpe)

    def _reps_for_slot(self, slot: WorkoutSlot, goal: str, readiness_score: int) -> str:
        if "cardio" in slot.movement_patterns:
            if self._is_lean_goal(goal) and readiness_score >= 40:
                return "10-15 minutes"
            return slot.reps
        if "mobility" in slot.movement_patterns or "core" in slot.movement_patterns:
            return slot.reps
        if self._is_lean_goal(goal):
            return "12-15"
        if goal == Goal.STRENGTH.value:
            return "5-8"
        if goal == Goal.ENDURANCE.value:
            return "12-20"
        return slot.reps

    def _rest_for_slot(self, slot: WorkoutSlot, goal: str, readiness_score: int) -> int:
        if readiness_score < 40:
            return min(slot.rest_seconds, 45)
        if self._is_lean_goal(goal):
            if any(role in slot.exercise_roles for role in {"accessory", "isolation", "corrective"}):
                return min(slot.rest_seconds, 45)
            return min(slot.rest_seconds, 60)
        return slot.rest_seconds

    def _planned_duration(
        self,
        available_time_minutes: int,
        readiness_score: int,
        decision: str,
    ) -> int:
        if decision == WorkoutDecision.REST_DAY.value:
            return 0
        if readiness_score < 20:
            return min(available_time_minutes, 20)
        if readiness_score < 40:
            return min(available_time_minutes, 30)
        return available_time_minutes

    def _normalize_equipment(self, equipment: list[str] | None) -> list[str]:
        normalized = list(
            dict.fromkeys(
                [item.strip().lower() for item in equipment or [] if item.strip()]
            )
        )
        if EquipmentType.BODYWEIGHT.value not in normalized:
            normalized.append(EquipmentType.BODYWEIGHT.value)
        return normalized

    def _focus_from_split(self, workout_split: str) -> str | None:
        split = (workout_split or "").strip().lower()
        if split == "upper_body":
            return "upper_body"
        if split == "lower_body":
            return "lower_body"
        if split == "push":
            return "upper_body_push"
        if split == "pull":
            return "upper_body_pull"
        if split == "full_body":
            return "full_body"
        return None

    def _is_lean_goal(self, goal: str) -> bool:
        return goal in {
            Goal.FAT_LOSS.value,
            Goal.GENERAL_HEALTH.value,
            Goal.ENDURANCE.value,
        }

    def _excluded_by_profile(
        self,
        exercise: Exercise,
        goal: str,
        training_level: str,
        injuries: list[str],
    ) -> bool:
        name = exercise.name.lower()
        movement = exercise.movement_pattern or exercise.movement_type or ""
        equipment = exercise.equipment_type.value
        normalized_injuries = " ".join(item.lower() for item in injuries)
        beginner_or_returner = training_level == TrainingLevel.BEGINNER.value

        if beginner_or_returner and (
            "barbell back squat" in name
            or "conventional deadlift" in name
            or "heavy deadlift" in name
        ):
            return True
        if self._is_lean_goal(goal) and beginner_or_returner and equipment == EquipmentType.BARBELL.value and movement in {"squat", "hinge"}:
            return True
        if any(term in normalized_injuries for term in {"back", "lower_back", "spine"}):
            if equipment == EquipmentType.BARBELL.value and movement in {"squat", "hinge"}:
                return True
        if "wrist" in normalized_injuries and name in {"push-up", "handstand push-up"}:
            return True
        return False

    def _plan_focus(
        self, template: WorkoutTemplate, focus_muscle: str | None
    ) -> MuscleGroup:
        requested = (focus_muscle or template.focus_type).strip().lower()
        for value in (requested, template.focus_type):
            try:
                return MuscleGroup(value)
            except ValueError:
                continue
        return MuscleGroup.FULL_BODY

    def _title(
        self,
        template: WorkoutTemplate,
        goal: Goal,
        decision: str,
    ) -> str:
        if decision == WorkoutDecision.RECOVERY.value:
            return "Recovery Session"
        if goal == Goal.STRENGTH:
            return f"{template.title} Strength Day"
        if decision == WorkoutDecision.REDUCED_VOLUME.value:
            return f"{template.title} Reduced Volume Day"
        return template.title

    def _reasoning(
        self,
        template: WorkoutTemplate,
        readiness_score: int,
        readiness_recommendation: str,
    ) -> str:
        if readiness_score < 40:
            return "Rule-based programming selected a recovery template based on low readiness."
        return (
            f"Rule-based programming selected the {template.title} template and adjusted "
            f"volume for readiness recommendation '{readiness_recommendation}'."
        )


class WorkoutSafetyPolicy:
    def validate(self, plan: WorkoutPlan, readiness_score: float) -> None:
        decision = plan.decision or ""

        if readiness_score < 20 and decision not in {
            WorkoutDecision.RECOVERY.value,
            WorkoutDecision.REST_DAY.value,
        }:
            raise ValidationError(
                "Very low readiness only allows recovery or rest_day plans"
            )

        for exercise in plan.exercises:
            is_cardio_interval = bool(
                exercise.target_reps
                and any(
                    term in exercise.target_reps.lower()
                    for term in ["fast", "easy", "minutes"]
                )
            )
            if exercise.target_sets > 5 and not is_cardio_interval:
                raise ValidationError("Workout plan exceeds maximum target sets")
            if exercise.target_sets > 10:
                raise ValidationError("Workout plan exceeds maximum target sets")
            if readiness_score < 40 and exercise.target_rpe > 7:
                raise ValidationError("Low readiness does not allow target_rpe above 7")
            if readiness_score < 40 and exercise.target_sets >= 5:
                raise ValidationError("Low readiness does not allow heavy volume")
        if not plan.exercises and decision != WorkoutDecision.REST_DAY.value:
            raise ValidationError(
                "Unsafe workout generation blocked: no exercises for non-rest day"
            )


class WorkoutVolumeCalculator:
    def calculate_total_volume(self, set_logs: list[WorkoutSetLog]) -> float:
        total = 0.0
        for set_log in set_logs:
            if not set_log.completed:
                continue
            if set_log.weight_kg is None or set_log.reps_completed is None:
                continue
            total += set_log.weight_kg * set_log.reps_completed
        return total
