import Foundation

final class TokenStore {
    private enum Keys {
        static let accessToken = "smartfit.access.token"
        static let refreshToken = "smartfit.refresh.token"
    }

    private let keychain: KeychainService

    init(keychain: KeychainService) {
        self.keychain = keychain
    }

    func saveTokens(accessToken: String, refreshToken: String) {
        keychain.set(accessToken, for: Keys.accessToken)
        keychain.set(refreshToken, for: Keys.refreshToken)
    }

    func getAccessToken() -> String? {
        keychain.get(Keys.accessToken)
    }

    func getRefreshToken() -> String? {
        keychain.get(Keys.refreshToken)
    }

    func clearTokens() {
        keychain.delete(Keys.accessToken)
        keychain.delete(Keys.refreshToken)
    }
}
