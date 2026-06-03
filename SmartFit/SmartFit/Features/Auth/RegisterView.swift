import SwiftUI

struct RegisterView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var viewModel = AuthViewModel()

    var body: some View {
        AuthFormContainer(
            title: "Create your account",
            subtitle: "Start your AI BioCoach setup in a few steps."
        ) {
            TextField("Email", text: $viewModel.email)
                .textInputAutocapitalization(.never)
                .keyboardType(.emailAddress)
                .autocorrectionDisabled()
                .authFieldStyle()

            SecureField("Password", text: $viewModel.password)
                .authFieldStyle()

            SecureField("Confirm Password", text: $viewModel.confirmPassword)
                .authFieldStyle()

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.error)
            }

            PrimaryButton(title: "Create Account", isLoading: viewModel.isLoading) {
                Task { await viewModel.register() }
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
