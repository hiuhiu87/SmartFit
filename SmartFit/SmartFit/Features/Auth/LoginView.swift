import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var viewModel = AuthViewModel()

    var body: some View {
        AuthFormContainer(
            title: "Welcome back",
            subtitle: "Sign in to continue your training plan."
        ) {
            TextField("Email", text: $viewModel.email)
                .textInputAutocapitalization(.never)
                .keyboardType(.emailAddress)
                .autocorrectionDisabled()
                .authFieldStyle()

            SecureField("Password", text: $viewModel.password)
                .authFieldStyle()

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.error)
            }

            PrimaryButton(title: "Log In", isLoading: viewModel.isLoading) {
                Task { await viewModel.login() }
            }

            ServerConfigurationSection(style: .authEntry)
        }
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                Button("Back") { appState.authRoute = .welcome }
            }
        }
        .onAppear {
            viewModel.configure(appState: appState)
        }
    }
}
