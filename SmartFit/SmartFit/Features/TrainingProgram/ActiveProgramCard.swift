import SwiftUI

struct ActiveProgramCard: View {
    let program: ActiveProgramResponse
    let todayWorkout: TodayProgramWorkoutResponse?
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

                if let todayWorkout, let scheduled = todayWorkout.scheduledWorkout {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(dayLabel(todayWorkout))
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textSecondary)
                        Text(scheduled.title)
                            .font(AppTypography.headline)
                        HStack(spacing: 14) {
                            Label(scheduled.focusType.programDisplayName, systemImage: "scope")
                        }
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                    }

                    if !["completed", "skipped"].contains(scheduled.status.lowercased()) {
                        PrimaryButton(
                            title: actionTitle(scheduled.status),
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

    private func dayLabel(_ workout: TodayProgramWorkoutResponse) -> String {
        let week = workout.weekNumber
        let day = (workout.dayIndex ?? 0) + 1
        return "WEEK \(week) · DAY \(day)"
    }

    private func actionTitle(_ status: String) -> String {
        switch status.lowercased() {
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
