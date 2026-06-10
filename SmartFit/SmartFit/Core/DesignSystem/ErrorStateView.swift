import SwiftUI

struct ErrorStateView: View {
    let message: String
    var retryTitle = "Try Again"
    var retryAction: (() -> Void)?

    var body: some View {
        AppCard(cornerRadius: AppRadius.card, padding: AppSpacing.xxl) {
            VStack(spacing: AppSpacing.lg) {
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
            .frame(maxWidth: .infinity)
        }
        .padding(AppSpacing.xxl)
    }
}

struct ErrorStateView_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            AppColors.background.ignoresSafeArea()
            ErrorStateView(message: "We could not refresh your workout plan.", retryAction: {})
        }
        .preferredColorScheme(.dark)
        .previewDisplayName("ErrorStateView")
    }
}
