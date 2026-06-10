from src.domain.ai.entities import AIWorkoutGenerationContext


class GeminiPromptBuilder:
    def build_generate_workout_prompt(self, context: AIWorkoutGenerationContext) -> str:
        # Format progression suggestions
        progression_lines = "none"
        if context.progression_context:
            progression_lines = "\n".join(
                [
                    f"- {p.exercise_slug} | Last Performance: {p.last_performance or 'none'} | "
                    f"Action: {p.progression_action} | Suggested Weight: {p.suggested_weight or 'bodyweight'} | "
                    f"Suggested Reps: {p.suggested_reps} | Reason: {p.reason}"
                    for p in context.progression_context
                ]
            )

        avoid = (
            ", ".join(context.avoid_exercises) if context.avoid_exercises else "none"
        )
        equipment = ", ".join(context.equipment) if context.equipment else "bodyweight"
        focus = context.focus_muscle or "full_body"
        split = context.workout_split or "full_body"
        note = context.user_note or "none"

        injuries = ", ".join(context.injuries) if context.injuries else "none"
        limitations = (
            ", ".join(context.movement_limitations)
            if context.movement_limitations
            else "none"
        )
        lifestyle = context.lifestyle_type or "none"
        sitting_hours = (
            f"{context.sitting_hours_per_day} hours/day"
            if context.sitting_hours_per_day is not None
            else "none"
        )
        history = context.training_history or "none"

        patterns = (
            ", ".join(context.movement_pattern_requirements)
            if context.movement_pattern_requirements
            else "none"
        )
        eq_mix = (
            "\n".join([f"- {item}" for item in context.equipment_mix_requirements])
            if context.equipment_mix_requirements
            else "none"
        )
        ordering = (
            "\n".join([f"- {item}" for item in context.ordering_guidelines])
            if context.ordering_guidelines
            else "none"
        )
        role_dist = (
            ", ".join(
                f"{role}: {minimum}-{maximum}"
                for role, (minimum, maximum) in context.role_distribution.items()
            )
            if context.role_distribution
            else "none"
        )
        allowed_catalog = (
            "\n".join(
                [
                    "- "
                    f"slug={item.slug} | name={item.name} | muscle={item.primary_muscle} | "
                    f"equipment={item.equipment} | pattern={item.movement_pattern or item.movement_type or 'unknown'} | "
                    f"role={item.exercise_role or 'accessory'}"
                    for item in context.allowed_exercises
                ]
            )
            if context.allowed_exercises
            else "none"
        )
        allowed_slugs = (
            ", ".join(item.slug for item in context.allowed_exercises)
            if context.allowed_exercises
            else "none"
        )

        return (
            "Return JSON only. No markdown. No comments. No extra text.\n"
            "Do not invent exercises. Respect readiness, equipment, time, avoid list, and level.\n"
            "CRITICAL EXERCISE SLUG RULE:\n"
            "- You must choose exercise_slug values by copying exact slugs from the Allowed exercise catalog below.\n"
            "- Never create, translate, rename, abbreviate, or guess exercise_slug values.\n"
            "- If an exercise is not in the catalog, do not use it.\n"
            f"- Valid exercise_slug values are exactly: {allowed_slugs}.\n\n"
            "Do not invent previous performance. If progression data is absent, leave weight unspecified.\n"
            "Do not select any exercise that conflicts with injuries, pain, or movement limitations.\n\n"
            "rest_seconds rules:\n"
            "- Use 15 to 300 for normal strength/resistance exercises.\n"
            "- Use 0 only for continuous cardio or mobility blocks where there is no rest interval.\n"
            "- Do not use 0 for normal lifting exercises.\n\n"
            "CRITICAL PT PROGRAMMING RULES:\n"
            f"- TARGET EXERCISE COUNT: Generate exactly {context.target_exercise_count_min} to {context.target_exercise_count_max} exercises.\n"
            f"- ROLE DISTRIBUTION: Prefer this distribution if possible: {role_dist}.\n"
            f"- MOVEMENT PATTERNS REQUIRED: Make sure the workout includes the following movement patterns: {patterns}.\n"
            f"- EQUIPMENT MIX RULES:\n{eq_mix}\n"
            f"- EXERCISE ORDERING RULES:\n{ordering}\n"
            f"- PROGRESSIVE OVERLOAD: Use the suggested weights/reps below for exercises you select. Do not make up random weights.\n\n"
            f"User Profile & Initial Assessment:\n"
            f"goal: {context.goal}\n"
            f"training_level: {context.training_level}\n"
            f"available_time_minutes: {context.available_time_minutes}\n"
            f"workout_split: {split}\n"
            f"focus_muscle: {focus}\n"
            f"equipment: {equipment}\n"
            f"avoid_exercises: {avoid}\n"
            f"user_note: {note}\n"
            f"injuries: {injuries}\n"
            f"movement_limitations: {limitations}\n"
            f"lifestyle_type: {lifestyle}\n"
            f"sitting_hours_per_day: {sitting_hours}\n"
            f"training_history: {history}\n\n"
            f"Readiness:\n"
            f"score: {context.readiness_score}\n"
            f"category: {context.readiness_category}\n"
            f"recommendation: {context.readiness_recommendation}\n\n"
            f"Allowed exercise catalog:\n{allowed_catalog}\n\n"
            f"Progression Suggestions per exercise:\n{progression_lines}\n\n"
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
            '      "target_weight": 20.0,\n'
            '      "rest_seconds": 90,\n'
            '      "rpe": 7,\n'
            '      "notes": "string"\n'
            "    }\n"
            "  ],\n"
            '  "reasoning_summary": "string",\n'
            '  "safety_note": "string"\n'
            "}\n\n"
            "Example continuous cardio block:\n"
            '{ "exercise_slug": "treadmill-zone-2-walk", "sets": 1, "reps": "20 minutes", "target_weight": null, "rest_seconds": 0, "rpe": 5, "notes": "Steady conversational pace." }'
        )
