import SwiftUI

struct LoadingStateView: View {
    var message: String = "Loading..."

    var body: some View {
        AppCard(cornerRadius: 18, padding: 22) {
            HStack(spacing: 12) {
                ProgressView()
                    .tint(AppColors.primary)
                Text(message)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.textSecondary)
            }
        }
        .padding(24)
    }
}
