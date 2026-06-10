import SwiftUI

struct LoadingStateView: View {
    var message: String = "Loading..."

    var body: some View {
        AppCard(cornerRadius: AppRadius.card, padding: AppSpacing.xxl) {
            HStack(spacing: AppSpacing.md) {
                ProgressView()
                    .tint(AppColors.primary)
                Text(message)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
            }
        }
        .padding(AppSpacing.xxl)
    }
}
