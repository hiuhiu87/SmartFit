import Foundation

final class AuthRepository {
    private let apiClient: APIClient
    private let tokenStore: TokenStore

    init(apiClient: APIClient, tokenStore: TokenStore) {
        self.apiClient = apiClient
        self.tokenStore = tokenStore
    }

    func register(email: String, password: String) async throws -> RegisteredUserResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/auth/register", method: .post),
            body: RegisterRequest(email: email, password: password),
            as: RegisteredUserResponse.self
        )
    }

    func login(email: String, password: String) async throws -> AuthTokenResponse {
        let response = try await apiClient.post(
            APIEndpoint(path: "/api/v1/auth/login", method: .post),
            body: LoginRequest(email: email, password: password),
            as: AuthTokenResponse.self
        )
        tokenStore.saveTokens(accessToken: response.accessToken, refreshToken: response.refreshToken)
        return response
    }

    func fetchCurrentUser() async throws -> CurrentUserResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/users/me", method: .get),
            as: CurrentUserResponse.self
        )
    }

    func logout() {
        tokenStore.clearTokens()
    }
}
