from src.domain.ai.entities import AIWorkoutGenerationContext


class GeminiPromptBuilder:
    def build_generate_workout_prompt(
        self, context: AIWorkoutGenerationContext
    ) -> str:
        allowed_lines = "\n".join(
            [
                f"- {item.slug} | {item.name} | {item.primary_muscle} | "
                f"{item.equipment} | {item.difficulty} | {item.movement_type or 'general'}"
                for item in context.allowed_exercises
            ]
        )
        avoid = ", ".join(context.avoid_exercises) if context.avoid_exercises else "none"
        equipment = ", ".join(context.equipment) if context.equipment else "bodyweight"
        focus = context.focus_muscle or "full_body"
        note = context.user_note or "none"

        return (
            "Return JSON only. No markdown. No comments. No extra text.\n"
            "Use only exercise_slug values from allowed_exercises.\n"
            "Do not invent exercises. Respect readiness, equipment, time, avoid list, and level.\n\n"
            f"User:\n"
            f"goal: {context.goal}\n"
            f"training_level: {context.training_level}\n"
            f"available_time_minutes: {context.available_time_minutes}\n"
            f"focus_muscle: {focus}\n"
            f"equipment: {equipment}\n"
            f"avoid_exercises: {avoid}\n"
            f"user_note: {note}\n\n"
            f"Readiness:\n"
            f"score: {context.readiness_score}\n"
            f"category: {context.readiness_category}\n"
            f"recommendation: {context.readiness_recommendation}\n\n"
            f"Allowed exercises:\n{allowed_lines}\n\n"
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
            "}"
        )
