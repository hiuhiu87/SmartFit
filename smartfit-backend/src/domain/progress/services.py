from src.domain.progress.entities import MuscleDistributionItem, ProgressOverview


class ProgressCalculator:
    def calculate_consistency(
        self, completed_count: int, target_count: int | None
    ) -> int:
        if not target_count or target_count <= 0:
            return 0
        return round(completed_count / target_count * 100)

    def calculate_muscle_percentages(
        self, items: list[MuscleDistributionItem]
    ) -> list[MuscleDistributionItem]:
        if not items:
            return []

        total_volume = sum(item.volume for item in items)
        if total_volume > 0:
            denominators = [item.volume for item in items]
        else:
            denominators = [float(item.set_count) for item in items]

        total = sum(denominators)
        if total <= 0:
            for item in items:
                item.percentage = 0
            return items

        for item, value in zip(items, denominators, strict=False):
            item.percentage = round(value / total * 100)
        return items

    def calculate_estimated_1rm(self, weight: float, reps: int) -> float:
        return round(weight * (1 + reps / 30), 2)

    def build_weekly_insights(
        self, overview: ProgressOverview
    ) -> tuple[list[str], list[str]]:
        highlights = [
            f"Your total training volume this week was {overview.total_volume:,.0f} kg.",
            (
                f"Your average readiness was {round(overview.average_readiness)}."
                if overview.average_readiness is not None
                else "There was no readiness data recorded this week."
            ),
        ]

        if overview.muscle_distribution:
            top = max(
                overview.muscle_distribution,
                key=lambda item: item.volume or item.set_count,
            )
            highlights.append(
                f"{top.muscle.replace('_', ' ').title()} was your most trained muscle group."
            )

        suggestions: list[str] = []
        if overview.weekly_workout_target > overview.weekly_workouts_completed:
            remaining = (
                overview.weekly_workout_target - overview.weekly_workouts_completed
            )
            suggestions.append(
                f"Try to complete {remaining} more workout next week to reach your target."
                if remaining == 1
                else f"Try to complete {remaining} more workouts next week to reach your target."
            )
        else:
            suggestions.append("Maintain your current training consistency next week.")

        if (
            overview.latest_completed_workout
            and overview.latest_completed_workout.total_volume > 0
        ):
            suggestions.append(
                "Consider placing a rest day after your highest-volume session."
            )
        else:
            suggestions.append(
                "Log your sets consistently to improve progress tracking."
            )

        return highlights, suggestions
