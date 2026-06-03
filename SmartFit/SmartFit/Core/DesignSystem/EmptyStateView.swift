import SwiftUI

struct EmptyStateView: View {
    let title: String
    let message: String
    var systemImage: String = "sparkles"
    var actionTitle: String?
    var action: (() -> Void)?

    var body: some View {
        AppCard(cornerRadius: 18, padding: 22) {
            VStack(alignment: .leading, spacing: 14) {
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
