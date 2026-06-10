import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 16) {
                Text("Settings")
                    .font(AppTypography.title)
                if let user = appState.currentUser {
                    Text(user.email)
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.textSecondary)
                }
                NavigationLink {
                    OnboardingView()
                } label: {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("Fitness profile")
                                .font(AppTypography.body.weight(.semibold))
                                .foregroundStyle(AppColors.textPrimary)
                            Text("Update goals, experience, lifestyle, and movement comfort.")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.textSecondary)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundStyle(AppColors.textSecondary)
                    }
                    .padding(18)
                    .background(AppColors.surface)
                    .overlay(
                        RoundedRectangle(cornerRadius: 18, style: .continuous)
                            .stroke(AppColors.border, lineWidth: 1)
                    )
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                }
                .buttonStyle(.plain)
                ServerConfigurationSection(style: .settingsPanel)
                PrimaryButton(title: "Log Out") {
                    appState.environment.authRepository.logout()
                    appState.setLoggedOut()
                }
            }
            .padding(24)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
            .background(AppColors.background.ignoresSafeArea())
        }
    }
}
