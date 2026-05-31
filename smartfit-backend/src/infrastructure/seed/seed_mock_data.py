import asyncio
from dataclasses import dataclass
from datetime import date, timedelta

from sqlmodel import select

from src.infrastructure.database.base import import_models
from src.infrastructure.database.models.ai_model import AIChatMessageModel, AIRequestModel, AnalyticsEventModel
from src.infrastructure.database.models.exercise_model import ExerciseAlternativeModel, ExerciseModel
from src.infrastructure.database.models.health_model import HealthSummaryModel, ManualCheckinModel
from src.infrastructure.database.models.readiness_model import ReadinessScoreModel
from src.infrastructure.database.models.subscription_model import SubscriptionModel
from src.infrastructure.database.models.user_model import NotificationSettingModel, UserEquipmentModel, UserModel, UserPreferenceModel, UserProfileModel
from src.infrastructure.database.models.workout_model import WorkoutFeedbackModel, WorkoutLogModel, WorkoutPlanExerciseModel, WorkoutPlanModel, WorkoutSetLogModel
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.seed.seed_exercises import seed_exercises


@dataclass(frozen=True)
class MockUserSpec:
    email: str
    full_name: str
    age: int
    height_cm: float
    weight_kg: float
    training_level: str
    primary_goal: str
    workout_style: str
    preferred_days: list[str]
    equipment: list[str]
    injuries: list[str]
    subscription_plan: str
    subscription_status: str


USER_SPECS = [
    MockUserSpec(
        email="mock.user1@smartfit.local",
        full_name="Alex Nguyen",
        age=29,
        height_cm=175.0,
        weight_kg=72.5,
        training_level="intermediate",
        primary_goal="muscle_gain",
        workout_style="balanced",
        preferred_days=["monday", "wednesday", "friday"],
        equipment=["dumbbell", "bench", "bodyweight"],
        injuries=["old ankle stiffness"],
        subscription_plan="premium",
        subscription_status="active",
    ),
    MockUserSpec(
        email="mock.user2@smartfit.local",
        full_name="Minh Tran",
        age=34,
        height_cm=168.0,
        weight_kg=64.0,
        training_level="beginner",
        primary_goal="fat_loss",
        workout_style="recovery_focused",
        preferred_days=["tuesday", "thursday", "saturday"],
        equipment=["bodyweight", "resistance_band", "treadmill"],
        injuries=[],
        subscription_plan="free",
        subscription_status="trial",
    ),
    MockUserSpec(
        email="mock.user3@smartfit.local",
        full_name="Linh Pham",
        age=41,
        height_cm=180.0,
        weight_kg=81.0,
        training_level="advanced",
        primary_goal="strength",
        workout_style="strength_focused",
        preferred_days=["monday", "thursday", "sunday"],
        equipment=["barbell", "bench", "cable_machine", "pull_up_bar"],
        injuries=["mild shoulder tightness"],
        subscription_plan="premium",
        subscription_status="active",
    ),
]


def _health_series(base_day: date, offset: int) -> dict:
    return {
        "date": base_day - timedelta(days=offset),
        "sleep_hours": round(6.6 + (offset % 4) * 0.4, 1),
        "sleep_efficiency": 82.0 + (offset % 5) * 2.5,
        "resting_heart_rate": 56.0 + offset,
        "heart_rate_variability": 68.0 - offset * 2,
        "steps": 7000 + offset * 900,
        "active_energy_kcal": 420.0 + offset * 45,
    }


def _readiness_series(base_day: date, offset: int) -> dict:
    score = max(38.0, 84.0 - offset * 6.5)
    if score >= 85:
        category, recommendation = "excellent", "train_hard"
    elif score >= 70:
        category, recommendation = "good", "train_normal"
    elif score >= 50:
        category, recommendation = "moderate", "reduce_volume"
    else:
        category, recommendation = "low", "recovery"

    return {
        "date": base_day - timedelta(days=offset),
        "score": round(score, 1),
        "category": category,
        "recommendation": recommendation,
        "confidence": round(max(0.65, 0.95 - offset * 0.04), 2),
        "explanation": f"Mock readiness sample for day offset {offset}.",
    }


async def _get_one_or_none(session, model, *conditions):
    statement = select(model).where(*conditions)
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def _get_all(session, model):
    result = await session.execute(select(model))
    return result.scalars().all()


async def seed_mock_data() -> dict[str, int]:
    import_models()
    inserted = {
        "users": 0,
        "profiles": 0,
        "equipment": 0,
        "preferences": 0,
        "notification_settings": 0,
        "health_summaries": 0,
        "manual_checkins": 0,
        "readiness_scores": 0,
        "exercise_alternatives": 0,
        "workout_plans": 0,
        "workout_plan_exercises": 0,
        "workout_logs": 0,
        "workout_set_logs": 0,
        "workout_feedback": 0,
        "ai_requests": 0,
        "ai_chat_messages": 0,
        "subscriptions": 0,
        "analytics_events": 0,
    }

    await seed_exercises()

    async with SessionLocal() as session:
        exercises = {exercise.slug: exercise for exercise in await _get_all(session, ExerciseModel)}
        primary_exercise = exercises["dumbbell-goblet-squat"]
        alternative_exercise = exercises["push-up"]
        cardio_exercise = exercises["treadmill-zone-2-walk"]

        exercise_alternative = await _get_one_or_none(
            session,
            ExerciseAlternativeModel,
            ExerciseAlternativeModel.exercise_id == primary_exercise.id,
            ExerciseAlternativeModel.alternative_exercise_id == alternative_exercise.id,
        )
        if exercise_alternative is None:
            session.add(
                ExerciseAlternativeModel(
                    exercise_id=primary_exercise.id,
                    alternative_exercise_id=alternative_exercise.id,
                    reason="Fallback when lower-body loading should be reduced",
                )
            )
            inserted["exercise_alternatives"] += 1

        today = date.today()

        for user_index, spec in enumerate(USER_SPECS, start=1):
            user = await _get_one_or_none(session, UserModel, UserModel.email == spec.email)
            if user is None:
                user = UserModel(
                    email=spec.email,
                    password_hash=f"$argon2id$v=19$m=65536,t=3,p=4$mock{user_index}$mockhash{user_index}",
                    auth_provider="email",
                    is_active=True,
                )
                session.add(user)
                await session.flush()
                inserted["users"] += 1

            profile = await _get_one_or_none(session, UserProfileModel, UserProfileModel.user_id == user.id)
            if profile is None:
                session.add(
                    UserProfileModel(
                        user_id=user.id,
                        full_name=spec.full_name,
                        age=spec.age,
                        height_cm=spec.height_cm,
                        weight_kg=spec.weight_kg,
                        training_level=spec.training_level,
                        primary_goal=spec.primary_goal,
                        injuries=spec.injuries,
                        notes=f"Mock user #{user_index} for local development.",
                    )
                )
                inserted["profiles"] += 1

            for equipment_type in spec.equipment:
                equipment = await _get_one_or_none(
                    session,
                    UserEquipmentModel,
                    UserEquipmentModel.user_id == user.id,
                    UserEquipmentModel.equipment_type == equipment_type,
                )
                if equipment is None:
                    session.add(UserEquipmentModel(user_id=user.id, equipment_type=equipment_type))
                    inserted["equipment"] += 1

            preference = await _get_one_or_none(session, UserPreferenceModel, UserPreferenceModel.user_id == user.id)
            if preference is None:
                session.add(
                    UserPreferenceModel(
                        user_id=user.id,
                        workout_style=spec.workout_style,
                        preferred_workout_days=spec.preferred_days,
                        preferred_session_minutes=40 + user_index * 10,
                        dislikes=["burpees"] if user_index == 1 else ["long planks"],
                        preference_metadata={"mock": True, "user_index": user_index},
                    )
                )
                inserted["preferences"] += 1

            notification_setting = await _get_one_or_none(session, NotificationSettingModel, NotificationSettingModel.user_id == user.id)
            if notification_setting is None:
                session.add(
                    NotificationSettingModel(
                        user_id=user.id,
                        readiness_push_enabled=True,
                        workout_reminder_enabled=True,
                        marketing_enabled=user_index == 2,
                        quiet_hours_start="22:00",
                        quiet_hours_end="06:30",
                    )
                )
                inserted["notification_settings"] += 1

            subscription = await _get_one_or_none(session, SubscriptionModel, SubscriptionModel.user_id == user.id)
            if subscription is None:
                session.add(
                    SubscriptionModel(
                        user_id=user.id,
                        plan=spec.subscription_plan,
                        status=spec.subscription_status,
                    )
                )
                inserted["subscriptions"] += 1

            for day_offset in range(7):
                health_payload = _health_series(today, day_offset)
                summary = await _get_one_or_none(
                    session,
                    HealthSummaryModel,
                    HealthSummaryModel.user_id == user.id,
                    HealthSummaryModel.date == health_payload["date"],
                )
                if summary is None:
                    session.add(
                        HealthSummaryModel(
                            user_id=user.id,
                            date=health_payload["date"],
                            sleep_hours=health_payload["sleep_hours"] + user_index * 0.1,
                            sleep_efficiency=health_payload["sleep_efficiency"],
                            resting_heart_rate=health_payload["resting_heart_rate"] + user_index,
                            heart_rate_variability=max(28.0, health_payload["heart_rate_variability"] - user_index),
                            steps=health_payload["steps"] + user_index * 250,
                            active_energy_kcal=health_payload["active_energy_kcal"] + user_index * 20,
                            source="healthkit",
                        )
                    )
                    inserted["health_summaries"] += 1

                checkin = await _get_one_or_none(
                    session,
                    ManualCheckinModel,
                    ManualCheckinModel.user_id == user.id,
                    ManualCheckinModel.date == health_payload["date"],
                )
                if checkin is None:
                    session.add(
                        ManualCheckinModel(
                            user_id=user.id,
                            date=health_payload["date"],
                            energy=max(2, 5 - (day_offset % 3)),
                            soreness=min(4, 1 + (day_offset % 4)),
                            stress=min(4, 1 + ((day_offset + user_index) % 4)),
                            motivation=max(2, 5 - (day_offset % 2)),
                            sleep_quality=max(2, 5 - (day_offset % 3)),
                            notes=f"Mock check-in for user {user_index}, day offset {day_offset}.",
                        )
                    )
                    inserted["manual_checkins"] += 1

                readiness_payload = _readiness_series(today, day_offset)
                readiness = await _get_one_or_none(
                    session,
                    ReadinessScoreModel,
                    ReadinessScoreModel.user_id == user.id,
                    ReadinessScoreModel.date == readiness_payload["date"],
                )
                if readiness is None:
                    session.add(
                        ReadinessScoreModel(
                            user_id=user.id,
                            date=readiness_payload["date"],
                            score=max(30.0, readiness_payload["score"] - user_index * 1.5),
                            category=readiness_payload["category"],
                            recommendation=readiness_payload["recommendation"],
                            confidence=readiness_payload["confidence"],
                            explanation=readiness_payload["explanation"],
                        )
                    )
                    inserted["readiness_scores"] += 1

            for plan_index in range(1, 4):
                plan_title = f"Mock Plan U{user_index}-{plan_index}"
                plan = await _get_one_or_none(
                    session,
                    WorkoutPlanModel,
                    WorkoutPlanModel.user_id == user.id,
                    WorkoutPlanModel.title == plan_title,
                )
                if plan is None:
                    plan = WorkoutPlanModel(
                        user_id=user.id,
                        title=plan_title,
                        focus=("full_body", "legs", "cardio")[plan_index - 1],
                        status=("completed", "completed", "generated")[plan_index - 1],
                        source=("ai", "manual", "fallback")[plan_index - 1],
                        readiness_score=78.0 - plan_index * 6 - user_index,
                        decision=("normal_volume", "reduced_volume", "recovery")[plan_index - 1],
                    )
                    session.add(plan)
                    await session.flush()
                    inserted["workout_plans"] += 1

                plan_exercise_specs = [
                    (1, primary_exercise.id, 4, "8-10", 7, "Primary movement"),
                    (2, alternative_exercise.id, 3, "10-15", 6, "Accessory push movement"),
                    (3, cardio_exercise.id, 1, "20 min", 5, "Finish with low-intensity cardio"),
                ]
                plan_exercise_ids = []
                for order_index, exercise_id, target_sets, target_reps, target_rpe, notes in plan_exercise_specs:
                    plan_exercise = await _get_one_or_none(
                        session,
                        WorkoutPlanExerciseModel,
                        WorkoutPlanExerciseModel.workout_plan_id == plan.id,
                        WorkoutPlanExerciseModel.order_index == order_index,
                    )
                    if plan_exercise is None:
                        plan_exercise = WorkoutPlanExerciseModel(
                            workout_plan_id=plan.id,
                            exercise_id=exercise_id,
                            order_index=order_index,
                            target_sets=target_sets,
                            target_reps=target_reps,
                            target_rpe=target_rpe,
                            notes=notes,
                        )
                        session.add(plan_exercise)
                        await session.flush()
                        inserted["workout_plan_exercises"] += 1
                    plan_exercise_ids.append(plan_exercise.id)

                if plan.status != "completed":
                    continue

                workout_log = await _get_one_or_none(
                    session,
                    WorkoutLogModel,
                    WorkoutLogModel.workout_plan_id == plan.id,
                    WorkoutLogModel.user_id == user.id,
                )
                if workout_log is None:
                    workout_log = WorkoutLogModel(
                        workout_plan_id=plan.id,
                        user_id=user.id,
                        duration_minutes=40 + plan_index * 7,
                        notes=f"Mock completed workout #{plan_index} for user {user_index}.",
                    )
                    session.add(workout_log)
                    await session.flush()
                    inserted["workout_logs"] += 1

                set_specs = [
                    (plan_exercise_ids[0], 1, 10, 20.0 + user_index * 2, 7),
                    (plan_exercise_ids[0], 2, 9, 22.0 + user_index * 2, 8),
                    (plan_exercise_ids[1], 1, 14, None, 6),
                    (plan_exercise_ids[1], 2, 12, None, 7),
                ]
                for plan_exercise_id, set_number, reps_completed, weight_kg, rpe in set_specs:
                    set_log = await _get_one_or_none(
                        session,
                        WorkoutSetLogModel,
                        WorkoutSetLogModel.workout_log_id == workout_log.id,
                        WorkoutSetLogModel.workout_plan_exercise_id == plan_exercise_id,
                        WorkoutSetLogModel.set_number == set_number,
                    )
                    if set_log is None:
                        session.add(
                            WorkoutSetLogModel(
                                workout_log_id=workout_log.id,
                                workout_plan_exercise_id=plan_exercise_id,
                                set_number=set_number,
                                reps_completed=reps_completed,
                                weight_kg=weight_kg,
                                rpe=rpe,
                            )
                        )
                        inserted["workout_set_logs"] += 1

                feedback = await _get_one_or_none(session, WorkoutFeedbackModel, WorkoutFeedbackModel.workout_log_id == workout_log.id)
                if feedback is None:
                    session.add(
                        WorkoutFeedbackModel(
                            workout_log_id=workout_log.id,
                            difficulty_feedback=("just_right", "too_easy", "too_hard")[user_index % 3],
                            enjoyment_score=7 + (plan_index % 3),
                            comments=f"Mock feedback for workout plan {plan_title}.",
                        )
                    )
                    inserted["workout_feedback"] += 1

            ai_request_specs = [
                ("generate_workout", "success", f"Generate workout for {spec.primary_goal}", "Generated workout plan."),
                ("replace_exercise", "fallback_used", f"Replace exercise for {spec.email}", "Suggested fallback exercise."),
                ("chat", "success", f"How should I recover after session for {spec.email}?", "Prioritize sleep, hydration, and light mobility."),
            ]
            for request_index, (request_type, status, prompt, response) in enumerate(ai_request_specs, start=1):
                ai_request = await _get_one_or_none(
                    session,
                    AIRequestModel,
                    AIRequestModel.user_id == user.id,
                    AIRequestModel.prompt == prompt,
                )
                if ai_request is None:
                    ai_request = AIRequestModel(
                        user_id=user.id,
                        request_type=request_type,
                        status=status,
                        prompt=prompt,
                        response=response,
                        request_metadata={"seed": True, "request_index": request_index, "user_index": user_index},
                    )
                    session.add(ai_request)
                    await session.flush()
                    inserted["ai_requests"] += 1

                for role, content in (
                    ("user", prompt),
                    ("assistant", response),
                ):
                    ai_message = await _get_one_or_none(
                        session,
                        AIChatMessageModel,
                        AIChatMessageModel.ai_request_id == ai_request.id,
                        AIChatMessageModel.role == role,
                    )
                    if ai_message is None:
                        session.add(
                            AIChatMessageModel(
                                ai_request_id=ai_request.id,
                                role=role,
                                content=content,
                            )
                        )
                        inserted["ai_chat_messages"] += 1

            for event_name, payload in (
                ("mock_seed_completed", {"email": spec.email, "user_index": user_index}),
                ("workout_generated", {"email": spec.email, "goal": spec.primary_goal}),
                ("readiness_checked", {"email": spec.email, "days_seeded": 7}),
            ):
                analytics_event = await _get_one_or_none(
                    session,
                    AnalyticsEventModel,
                    AnalyticsEventModel.user_id == user.id,
                    AnalyticsEventModel.event_name == event_name,
                )
                if analytics_event is None:
                    session.add(
                        AnalyticsEventModel(
                            user_id=user.id,
                            event_name=event_name,
                            payload=payload,
                        )
                    )
                    inserted["analytics_events"] += 1

        await session.commit()

    return inserted


async def main() -> None:
    inserted = await seed_mock_data()
    print("Mock data seed completed")
    for key, value in inserted.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
