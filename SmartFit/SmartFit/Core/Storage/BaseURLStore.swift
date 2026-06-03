import Foundation

final class BaseURLStore {
    private enum Keys {
        static let customBaseURL = "smartfit.custom.base_url"
    }

    private let userDefaults: UserDefaults
    private let defaultBaseURL: URL

    init(defaultBaseURL: URL, userDefaults: UserDefaults = .standard) {
        self.defaultBaseURL = defaultBaseURL
        self.userDefaults = userDefaults
    }

    var currentURL: URL {
        if let override = customBaseURL {
            return override
        }
        return defaultBaseURL
    }

    var defaultURL: URL {
        defaultBaseURL
    }

    var customBaseURL: URL? {
        guard let rawValue = userDefaults.string(forKey: Keys.customBaseURL) else {
            return nil
        }
        return URL(string: rawValue)
    }

    func saveCustomBaseURL(_ rawValue: String) throws {
        let trimmed = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard
            let url = URL(string: trimmed),
            let scheme = url.scheme?.lowercased(),
            ["http", "https"].contains(scheme),
            url.host != nil
        else {
            throw URLError(.badURL)
        }

        userDefaults.set(url.absoluteString, forKey: Keys.customBaseURL)
    }

    func clearCustomBaseURL() {
        userDefaults.removeObject(forKey: Keys.customBaseURL)
    }
}
