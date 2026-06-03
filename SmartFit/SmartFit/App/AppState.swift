import Combine
import Foundation

@MainActor
final class AppState: ObservableObject {
    enum AuthRoute {
        case welcome
        case login
        case register
    }

    @Published var isAuthenticated = false
    @Published var hasCompletedOnboarding = false
    @Published var currentUser: CurrentUserResponse?
    @Published var isLoadingInitialSession = true
    @Published var authRoute: AuthRoute = .welcome

    let environment: AppEnvironment

    init(environment: AppEnvironment) {
        self.environment = environment
        Task {
            await restoreSession()
        }
    }

    func restoreSession() async {
        isLoadingInitialSession = true
        defer { isLoadingInitialSession = false }

        guard environment.tokenStore.getAccessToken() != nil || environment.tokenStore.getRefreshToken() != nil else {
            setLoggedOut()
            return
        }

        do {
            let user = try await environment.authRepository.fetchCurrentUser()
            applyAuthenticatedUser(user)
        } catch {
            #if DEBUG
            print("Failed to restore session: \(error)")
            #endif
            setLoggedOut()
        }
    }

    func applyAuthenticatedUser(_ user: CurrentUserResponse) {
        currentUser = user
        isAuthenticated = true
        hasCompletedOnboarding = user.isOnboardingComplete
    }

    func setLoggedOut() {
        currentUser = nil
        isAuthenticated = false
        hasCompletedOnboarding = false
        authRoute = .welcome
        environment.tokenStore.clearTokens()
    }
}
