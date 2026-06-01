from src.domain.ai.entities import AIChatContext


class GeminiChatPromptBuilder:
    def build_chat_prompt(self, context: AIChatContext) -> str:
        readiness = context.readiness_summary or {}
        workout = context.workout_summary
        current = context.current_exercise or {}
        replacements = "\n".join(
            [
                f"- {item['exercise_id']} | {item['exercise_name']} | {item['slug']} | "
                f"{item['primary_muscle']} | {item['equipment']} | {item['difficulty']}"
                for item in context.available_replacements
            ]
        ) or "- none"

        recent_sets = current.get("logged_sets", []) if current else []
        recent_set_lines = "\n".join(
            [
                f"- set {item['set_number']}: weight={item['weight']} reps={item['reps']} rpe={item['rpe']} completed={item['completed']}"
                for item in recent_sets[-3:]
            ]
        ) or "- none"

        current_exercise_text = (
            "Current exercise:\n"
            f"name: {current.get('name')}\n"
            f"workout_plan_exercise_id: {current.get('workout_plan_exercise_id')}\n"
            f"primary_muscle: {current.get('primary_muscle')}\n"
            f"equipment: {current.get('equipment')}\n"
            f"target_sets: {current.get('target_sets')}\n"
            f"target_reps: {current.get('target_reps')}\n"
            f"target_rpe: {current.get('target_rpe')}\n"
            f"rest_seconds: {current.get('rest_seconds')}\n"
            f"recent_logged_sets:\n{recent_set_lines}\n"
            if current
            else "Current exercise: none\n"
        )

        return (
            "Return JSON only. No markdown. No extra text. Keep reply short and practical.\n"
            "Do not diagnose medical conditions. Do not tell the user to push through sharp pain.\n"
            "If user mentions pain, dizziness, or unusual discomfort, prefer safety_warning.\n"
            "Do not claim the workout was already changed.\n"
            "For replace_exercise, use only exercise_id values from available_replacements.\n\n"
            f"Workout:\n"
            f"title: {workout.get('title')}\n"
            f"status: {workout.get('status')}\n"
            f"source: {workout.get('source')}\n"
            f"focus: {workout.get('focus')}\n\n"
            f"User:\n"
            f"training_level: {context.user_profile_summary.get('training_level')}\n"
            f"goal: {context.user_profile_summary.get('primary_goal')}\n"
            f"injuries: {context.user_profile_summary.get('injuries')}\n"
            f"equipment: {', '.join(context.user_profile_summary.get('equipment', []))}\n\n"
            f"Readiness:\n"
            f"score: {readiness.get('score')}\n"
            f"category: {readiness.get('category')}\n"
            f"recommendation: {readiness.get('recommendation')}\n\n"
            f"{current_exercise_text}\n"
            f"Available replacements:\n{replacements}\n\n"
            f"User message:\n{context.user_message}\n\n"
            "Return JSON schema:\n"
            "{\n"
            '  "reply": "string",\n'
            '  "intent": "replace_exercise | reduce_difficulty | explain_exercise | rest_time_advice | general_workout_question | safety_warning",\n'
            '  "suggested_action": {\n'
            '    "type": "replace_exercise | reduce_current_exercise | adjust_rest_time | none",\n'
            '    "exercise_id": "uuid or null",\n'
            '    "exercise_name": "string or null",\n'
            '    "target_sets": 3,\n'
            '    "target_reps": "10-12",\n'
            '    "rest_seconds": 75,\n'
            '    "target_rpe": 7,\n'
            '    "reason": "string or null"\n'
            "  }\n"
            "}"
        )
