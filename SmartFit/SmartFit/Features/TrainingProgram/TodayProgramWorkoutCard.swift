import SwiftUI

struct TodayProgramWorkoutCard: View {
    let program: ActiveProgramResponse
    let todayWorkout: TodayProgramWorkoutResponse
    let onOpenWorkout: () -> Void
    let onAdjustWorkout: () -> Void
    let onSkip: () -> Void
    let onReschedule: () -> Void

    var body: some View {
        AppCard(cornerRadius: 24, padding: 22) {
            VStack(alignment: .leading, spacing: 18) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(program.name.uppercased())
                            .font(AppTypography.caption.weight(.semibold))
                            .foregroundStyle(AppColors.primary)
                        
                        HStack(spacing: 8) {
                            Text("Week \(todayWorkout.weekNumber)")
                                .font(AppTypography.headline.weight(.semibold))
                            if let phase = todayWorkout.phase {
                                ProgramPhaseBadge(phase: phase)
                            }
                        }
                    }
                    Spacer()
                }

                Divider().overlay(AppColors.border)

                if let scheduled = todayWorkout.scheduledWorkout {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("TODAY'S WORKOUT")
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textSecondary)
                        
                        Text(scheduled.title)
                            .font(AppTypography.hero)
                            .foregroundStyle(AppColors.textPrimary)
                        
                        Text(scheduled.focusType.programDisplayName)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textSecondary)
                    }

                    if let recommendation = todayWorkout.recommendation {
                        HStack(spacing: 12) {
                            Image(systemName: recommendationIcon(recommendation.action))
                                .font(.system(size: 20))
                                .foregroundStyle(recommendationColor(recommendation.action))
                            
                            VStack(alignment: .leading, spacing: 2) {
                                Text(recommendation.message)
                                    .font(AppTypography.caption)
                                    .foregroundStyle(AppColors.textSecondary)
                                    .multilineTextAlignment(.leading)
                            }
                        }
                        .padding(12)
                        .background(AppColors.backgroundSecondary)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                    }

                    if !["completed", "skipped"].contains(scheduled.status.lowercased()) {
                        VStack(spacing: 10) {
                            PrimaryButton(
                                title: actionButtonTitle,
                                systemImage: "play.fill",
                                action: onOpenWorkout
                            )
                            
                            if todayWorkout.recommendation?.action == "adjust_workout" {
                                SecondaryButton(
                                    title: "Adjust Today",
                                    systemImage: "slider.horizontal.3",
                                    action: onAdjustWorkout
                                )
                            }
                            
                            HStack(spacing: 12) {
                                Button(action: onSkip) {
                                    Label("Skip", systemImage: "xmark.circle")
                                        .font(AppTypography.caption.weight(.semibold))
                                        .foregroundStyle(AppColors.danger)
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 12)
                                        .background(AppColors.surfaceMuted)
                                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                                }
                                .buttonStyle(.plain)
                                
                                Button(action: onReschedule) {
                                    Label("Reschedule", systemImage: "calendar")
                                        .font(AppTypography.caption.weight(.semibold))
                                        .foregroundStyle(AppColors.textPrimary)
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 12)
                                        .background(AppColors.surfaceMuted)
                                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(.top, 8)
                    } else {
                        HStack {
                            Image(systemName: scheduled.status.lowercased() == "completed" ? "checkmark.circle.fill" : "arrow.forward.circle.fill")
                                .foregroundStyle(scheduled.status.lowercased() == "completed" ? AppColors.success : AppColors.warning)
                            Text("Workout \(scheduled.status.programDisplayName)")
                                .font(AppTypography.body.weight(.semibold))
                                .foregroundStyle(AppColors.textSecondary)
                            Spacer()
                        }
                        .padding(.top, 8)
                    }
                } else {
                    HStack(spacing: 12) {
                        Image(systemName: "leaf.fill")
                            .font(.system(size: 24))
                            .foregroundStyle(AppColors.success)
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Rest & Recover Today")
                                .font(AppTypography.body.weight(.semibold))
                            Text("No workout scheduled. Allow your muscles to repair.")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                    }
                }
            }
        }
    }

    private var actionButtonTitle: String {
        guard let scheduled = todayWorkout.scheduledWorkout else { return "Open Workout" }
        switch scheduled.status.lowercased() {
        case "generated", "started":
            return "Start Workout"
        default:
            return "Open Planned Workout"
        }
    }

    private func recommendationIcon(_ action: String) -> String {
        switch action {
        case "adjust_workout": return "exclamationmark.triangle.fill"
        case "rest_day": return "leaf.fill"
        default: return "checkmark.circle.fill"
        }
    }

    private func recommendationColor(_ action: String) -> Color {
        switch action {
        case "adjust_workout": return AppColors.warning
        case "rest_day": return AppColors.success
        default: return AppColors.primary
        }
    }
}
