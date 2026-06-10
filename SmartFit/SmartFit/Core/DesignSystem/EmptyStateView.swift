import SwiftUI

struct EmptyStateView: View {
    let title: String
    let message: String
    var systemImage: String = "sparkles"
    var actionTitle: String?
    var action: (() -> Void)?

    var body: some View {
        AppCard(cornerRadius: AppRadius.card, padding: AppSpacing.xxl) {
            VStack(alignment: .leading, spacing: AppSpacing.md) {
                Image(systemName: systemImage)
                    .font(.system(size: 24, weight: .semibold))
                    .foregroundStyle(AppColors.primary)
                Text(title)
                    .font(AppTypography.title)
                Text(message)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
                if let actionTitle, let action {
                    PrimaryButton(title: actionTitle, action: action)
                }
            }
        }
    }
}

struct EmptyStateView_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            EmptyStateView(
                title: "No workouts yet",
                message: "Your completed sessions will appear here after you finish a workout.",
                systemImage: "figure.strengthtraining.traditional",
                actionTitle: "Build Workout"
            ) {}
            .padding(AppSpacing.xxl)
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("EmptyStateView")
    }
}
