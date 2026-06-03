import SwiftUI

struct ErrorStateView: View {
    let message: String
    var retryTitle = "Try Again"
    var retryAction: (() -> Void)?

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 36))
                .foregroundStyle(AppColors.error)
            Text(message)
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textPrimary)
                .multilineTextAlignment(.center)
            if let retryAction {
                PrimaryButton(title: retryTitle, action: retryAction)
            }
        }
        .padding(24)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(AppColors.background.ignoresSafeArea())
    }
}
