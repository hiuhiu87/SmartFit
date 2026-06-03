import Combine
import Foundation

@MainActor
final class AuthViewModel: ObservableObject {
    @Published var email = ""
    @Published var password = ""
    @Published var confirmPassword = ""
    @Published var isLoading = false
    @Published var errorMessage: String?

    private var repository: AuthRepository?
    private weak var appState: AppState?

    init() {}

    func configure(appState: AppState) {
        if self.appState === appState { return }
        self.appState = appState
        self.repository = appState.environment.authRepository
    }

    func login() async {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Email and password are required."
            return
        }
        guard let repository else {
            errorMessage = "App environment is not ready."
            return
        }

        await runTask { [self] in
            _ = try await repository.login(email: self.email, password: self.password)
            let user = try await repository.fetchCurrentUser()
            self.appState?.applyAuthenticatedUser(user)
        }
    }

    func register() async {
        guard !email.isEmpty, !password.isEmpty else {
            errorMessage = "Email and password are required."
            return
        }
        guard password == confirmPassword else {
            errorMessage = "Passwords do not match."
            return
        }
        guard let repository else {
            errorMessage = "App environment is not ready."
            return
        }

        await runTask { [self] in
            _ = try await repository.register(email: self.email, password: self.password)
            _ = try await repository.login(email: self.email, password: self.password)
            let user = try await repository.fetchCurrentUser()
            self.appState?.applyAuthenticatedUser(user)
        }
    }

    func logout() {
        guard let repository else { return }
        repository.logout()
        appState?.setLoggedOut()
    }

    func loadCurrentUser() async {
        guard let repository else {
            errorMessage = "App environment is not ready."
            return
        }
        await runTask { [self] in
            let user = try await repository.fetchCurrentUser()
            self.appState?.applyAuthenticatedUser(user)
        }
    }

    private func runTask(_ operation: @escaping () async throws -> Void) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            try await operation()
        } catch {
            #if DEBUG
            print("Auth error: \(error)")
            #endif
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Something went wrong."
        }
    }
}
