import Foundation

struct AuthInterceptor {
    private let tokenStore: TokenStore

    init(tokenStore: TokenStore) {
        self.tokenStore = tokenStore
    }

    func adapt(_ request: URLRequest) -> URLRequest {
        var request = request
        if let token = tokenStore.getAccessToken(), !token.isEmpty {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        return request
    }
}
