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
