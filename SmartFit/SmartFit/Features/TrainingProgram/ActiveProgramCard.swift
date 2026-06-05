import SwiftUI

struct ActiveProgramCard: View {
    let program: TrainingProgramResponse
    let todayWorkout: ProgramTodayWorkoutResponse?
    let isGenerating: Bool
    let onOpenProgram: () -> Void
    let onGenerateWorkout: () -> Void

    var body: some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 18) {
                Button(action: onOpenProgram) {
                    HStack(alignment: .top, spacing: 14) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("ACTIVE PROGRAM")
                                .font(AppTypography.caption.weight(.semibold))
                                .foregroundStyle(AppColors.primary)
                            Text(program.name)
                                .font(AppTypography.title)
                                .foregroundStyle(AppColors.textPrimary)
                                .multilineTextAlignment(.leading)
                            Text("Week \(program.currentWeek) of \(program.durationWeeks)")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundStyle(AppColors.textSecondary)
                    }
                }
                .buttonStyle(.plain)

                ProgressView(value: program.progress)
                    .tint(AppColors.primary)

                Divider().overlay(AppColors.border)

                if let todayWorkout, todayWorkout.scheduled, let template = todayWorkout.template {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(dayLabel(todayWorkout))
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textSecondary)
                        Text(template.title)
                            .font(AppTypography.headline)
                        HStack(spacing: 14) {
                            Label("\(template.estimatedDurationMinutes) min", systemImage: "clock")
                            Label(template.focusType.programDisplayName, systemImage: "scope")
                        }
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    }

                    if !["completed", "skipped"].contains(todayWorkout.status ?? "") {
                        PrimaryButton(
                            title: actionTitle(todayWorkout),
                            isLoading: isGenerating,
                            systemImage: "figure.strengthtraining.traditional",
                            action: onGenerateWorkout
                        )
                    }
                } else {
                    HStack(spacing: 12) {
                        Image(systemName: "leaf.fill")
                            .foregroundStyle(AppColors.success)
                        VStack(alignment: .leading, spacing: 3) {
                            Text("Program rest day")
                                .font(AppTypography.body.weight(.semibold))
                            Text("Recover now so the next session stays productive.")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }
                }
            }
        }
    }

    private func dayLabel(_ workout: ProgramTodayWorkoutResponse) -> String {
        let week = workout.weekNumber ?? program.currentWeek
        let day = (workout.dayIndex ?? program.currentDayIndex) + 1
        return "WEEK \(week) · DAY \(day)"
    }

    private func actionTitle(_ workout: ProgramTodayWorkoutResponse) -> String {
        switch workout.status {
        case "generated", "started":
            return "Open Today’s Workout"
        case "completed":
            return "Workout Completed"
        case "skipped":
            return "Workout Skipped"
        default:
            return "Generate Today’s Workout"
        }
    }
}
