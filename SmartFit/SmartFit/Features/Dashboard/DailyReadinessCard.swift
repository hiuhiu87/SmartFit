import SwiftUI

struct DailyReadinessCard: View {
    let readiness: ReadinessResponse
    let lastSyncDate: Date?
    let onGenerateWorkout: () -> Void
    let onRefresh: () -> Void

    var body: some View {
        AppCard(cornerRadius: 24, padding: 24) {
            VStack(alignment: .leading, spacing: 18) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(greeting)
                            .font(AppTypography.caption)
                            .foregroundStyle(AppColors.textSecondary)
                        Text("Today’s Readiness")
                            .font(AppTypography.title)
                    }
                    Spacer()
                    StatusBadge(
                        title: readiness.category.replacingOccurrences(of: "_", with: " ").capitalized,
                        color: categoryColor
                    )
                }

                HStack(alignment: .bottom, spacing: 12) {
                    Text("\(readiness.displayScore)")
                        .font(.system(size: 72, weight: .bold, design: .rounded))
                        .foregroundStyle(categoryColor)
                    Text("%")
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.textSecondary)
                        .padding(.bottom, 14)
                }

                Text(recommendationText)
                    .font(AppTypography.headline)
                    .foregroundStyle(AppColors.textPrimary)
                    .fixedSize(horizontal: false, vertical: true)

                if let lastSyncDate {
                    Text("Last synced \(lastSyncDate.formatted(date: .omitted, time: .shortened))")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.textSecondary)
                }

                VStack(spacing: 12) {
                    PrimaryButton(
                        title: primaryTitle,
                        systemImage: "figure.strengthtraining.traditional",
                        action: onGenerateWorkout
                    )
                    SecondaryButton(title: "Refresh Health Data", systemImage: "arrow.clockwise", action: onRefresh)
                }
            }
        }
    }

    private var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        switch hour {
        case 5..<12: return "Good morning"
        case 12..<17: return "Good afternoon"
        default: return "Good evening"
        }
    }

    private var categoryColor: Color {
        ReadinessStyle.color(for: readiness.category)
    }

    private var primaryTitle: String {
        switch readiness.recommendation {
        case "recovery", "rest":
            return "Build Recovery Workout"
        default:
            return "Generate Today’s Workout"
        }
    }

    private var recommendationText: String {
        switch readiness.recommendation {
        case "train_hard", "train_normal":
            return "Your body looks ready for normal training."
        case "reduce_volume":
            return "Keep the session focused and a little lighter today."
        case "recovery", "rest":
            return "Recovery still counts. Keep movement calm and easy."
        default:
            return readiness.explanation
        }
    }
}
