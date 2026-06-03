import SwiftUI

struct WelcomeView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        VStack(alignment: .leading, spacing: 24) {
            Spacer()
            Text("SmartFit")
                .font(AppTypography.hero)
                .foregroundStyle(AppColors.textPrimary)
            Text("AI BioCoach for readiness-aware training, built around your daily recovery and workout flow.")
                .font(AppTypography.body)
                .foregroundStyle(AppColors.textSecondary)
            Spacer()
            VStack(spacing: 12) {
                PrimaryButton(title: "Log In") {
                    appState.authRoute = .login
                }
                Button("Create Account") {
                    appState.authRoute = .register
                }
                .font(AppTypography.body.weight(.semibold))
                .foregroundStyle(AppColors.textPrimary)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(AppColors.surfaceElevated)
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(AppColors.border, lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            }
            ServerConfigurationSection(style: .authEntry)
        }
        .padding(24)
        .background(AppColors.background.ignoresSafeArea())
    }
}
