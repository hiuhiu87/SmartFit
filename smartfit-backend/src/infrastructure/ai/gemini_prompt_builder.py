from src.domain.ai.entities import AIWorkoutGenerationContext


class GeminiPromptBuilder:
    def build_generate_workout_prompt(self, context: AIWorkoutGenerationContext) -> str:
        allowed_lines = "\n".join(
            [
                f"- {item.slug} | {item.name} | {item.primary_muscle} | "
                f"{item.equipment} | {item.difficulty} | {item.movement_type or 'general'}"
                for item in context.allowed_exercises
            ]
        )
        avoid = (
            ", ".join(context.avoid_exercises) if context.avoid_exercises else "none"
        )
        equipment = ", ".join(context.equipment) if context.equipment else "bodyweight"
        focus = context.focus_muscle or "full_body"
        split = context.workout_split or "full_body"
        note = context.user_note or "none"

        return (
            "Return JSON only. No markdown. No comments. No extra text.\n"
            "Use only exercise_slug values from allowed_exercises.\n"
            "Do not invent exercises. Respect readiness, equipment, time, avoid list, and level.\n\n"
            "rest_seconds rules:\n"
            "- Use 15 to 300 for normal strength/resistance exercises.\n"
            "- Use 0 only for continuous cardio or mobility blocks where there is no rest interval.\n"
            "- Do not use 0 for normal lifting exercises.\n\n"
            f"User:\n"
            f"goal: {context.goal}\n"
            f"training_level: {context.training_level}\n"
            f"available_time_minutes: {context.available_time_minutes}\n"
            f"workout_split: {split}\n"
            f"focus_muscle: {focus}\n"
            f"equipment: {equipment}\n"
            f"avoid_exercises: {avoid}\n"
            f"user_note: {note}\n\n"
            f"Readiness:\n"
            f"score: {context.readiness_score}\n"
            f"category: {context.readiness_category}\n"
            f"recommendation: {context.readiness_recommendation}\n\n"
            f"Allowed exercises:\n{allowed_lines}\n\n"
            "Workout split guidance:\n"
            "- full_body: include a balanced mix of push, pull, lower-body, and core/cardio when available.\n"
            "- upper_body: prioritize chest, back, shoulders, and arms.\n"
            "- lower_body: prioritize legs, squat/hinge patterns, and core.\n"
            "- push: prioritize chest, shoulders, triceps, and push movements.\n"
            "- pull: prioritize back, biceps, posterior-chain, and pull/hinge movements.\n\n"
            "Return JSON schema:\n"
            "{\n"
            '  "workout_title": "string",\n'
            '  "training_decision": "normal_volume | reduced_volume | recovery | rest_day",\n'
            '  "estimated_duration_minutes": 45,\n'
            '  "exercises": [\n'
            "    {\n"
            '      "exercise_slug": "string",\n'
            '      "sets": 3,\n'
            '      "reps": "8-10",\n'
            '      "rest_seconds": 90,\n'
            '      "rpe": 7,\n'
            '      "notes": "string"\n'
            "    }\n"
            "  ],\n"
            '  "reasoning_summary": "string",\n'
            '  "safety_note": "string"\n'
            "}\n\n"
            "Example continuous cardio block:\n"
            '{ "exercise_slug": "treadmill-zone-2-walk", "sets": 1, "reps": "20 minutes", "rest_seconds": 0, "rpe": 5, "notes": "Steady conversational pace." }'
        )
