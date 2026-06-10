import Foundation

final class APIClient {
    private let baseURLStore: BaseURLStore
    private let session: URLSession
    private let authInterceptor: AuthInterceptor
    private let tokenStore: TokenStore
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(
        baseURLStore: BaseURLStore,
        session: URLSession = .shared,
        authInterceptor: AuthInterceptor,
        tokenStore: TokenStore
    ) {
        self.baseURLStore = baseURLStore
        self.session = session
        self.authInterceptor = authInterceptor
        self.tokenStore = tokenStore
        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
    }

    func get<T: Decodable>(_ endpoint: APIEndpoint, as type: T.Type) async throws -> T {
        try await send(endpoint, body: Optional<Data>.none, as: type)
    }

    func post<T: Decodable, Body: Encodable>(
        _ endpoint: APIEndpoint,
        body: Body,
        as type: T.Type
    ) async throws -> T {
        let bodyData = try encoder.encode(body)
        return try await send(endpoint, body: bodyData, as: type)
    }

    func put<T: Decodable, Body: Encodable>(
        _ endpoint: APIEndpoint,
        body: Body,
        as type: T.Type
    ) async throws -> T {
        let bodyData = try encoder.encode(body)
        return try await send(endpoint, body: bodyData, as: type)
    }

    private func send<T: Decodable>(
        _ endpoint: APIEndpoint,
        body: Data?,
        as type: T.Type
    ) async throws -> T {
        try await send(endpoint, body: body, as: type, allowTokenRefresh: true)
    }

    private func send<T: Decodable>(
        _ endpoint: APIEndpoint,
        body: Data?,
        as type: T.Type,
        allowTokenRefresh: Bool
    ) async throws -> T {
        let request = try buildRequest(for: endpoint, body: body)

        #if DEBUG
        print("➡️ \(endpoint.method.rawValue) \(request.url?.absoluteString ?? "")")
        #endif

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            if error.isCancellation {
                throw CancellationError()
            }
            throw APIError.transport(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        if httpResponse.statusCode == 401 {
            if allowTokenRefresh, endpoint.canRefreshToken, try await refreshAccessToken() {
                return try await send(endpoint, body: body, as: type, allowTokenRefresh: false)
            }
            throw APIError.unauthorized
        }

        let envelope: APIResponseEnvelope<T>
        do {
            envelope = try decoder.decode(APIResponseEnvelope<T>.self, from: data)
        } catch {
            #if DEBUG
            print("Decoding error: \(error)")
            print(String(data: data, encoding: .utf8) ?? "No response body")
            #endif
            throw APIError.decodingError
        }

        if envelope.success, let payload = envelope.data {
            return payload
        }

        if let error = envelope.error {
            throw APIError.server(code: error.code, message: error.message)
        }

        throw APIError.server(
            code: envelope.code ?? "UNKNOWN_ERROR",
            message: envelope.message ?? "Something went wrong."
        )
    }

    private func refreshAccessToken() async throws -> Bool {
        guard let refreshToken = tokenStore.getRefreshToken(), !refreshToken.isEmpty else {
            return false
        }

        let endpoint = APIEndpoint(path: "/api/v1/auth/refresh", method: .post)
        let body = try encoder.encode(RefreshTokenRequest(refreshToken: refreshToken))
        let request = try buildRequest(for: endpoint, body: body, includeAuthorization: false)

        #if DEBUG
        print("🔄 POST \(request.url?.absoluteString ?? "")")
        #endif

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            if error.isCancellation {
                throw CancellationError()
            }
            throw APIError.transport(error)
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        guard httpResponse.statusCode != 401 else {
            tokenStore.clearTokens()
            return false
        }

        let envelope: APIResponseEnvelope<AuthTokenResponse>
        do {
            envelope = try decoder.decode(APIResponseEnvelope<AuthTokenResponse>.self, from: data)
        } catch {
            #if DEBUG
            print("Refresh token decoding error: \(error)")
            print(String(data: data, encoding: .utf8) ?? "No response body")
            #endif
            throw APIError.decodingError
        }

        if envelope.success, let payload = envelope.data {
            tokenStore.saveTokens(accessToken: payload.accessToken, refreshToken: payload.refreshToken)
            return true
        }

        if let error = envelope.error {
            throw APIError.server(code: error.code, message: error.message)
        }

        throw APIError.server(
            code: envelope.code ?? "UNKNOWN_ERROR",
            message: envelope.message ?? "Unable to refresh session."
        )
    }

    private func buildRequest(
        for endpoint: APIEndpoint,
        body: Data?,
        includeAuthorization: Bool = true
    ) throws -> URLRequest {
        guard var components = URLComponents(
            url: baseURL.appendingPathComponent(
                endpoint.path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
            ),
            resolvingAgainstBaseURL: false
        ) else {
            throw APIError.invalidURL
        }
        if !endpoint.queryItems.isEmpty {
            components.queryItems = endpoint.queryItems
        }
        guard let url = components.url else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.httpBody = body

        guard includeAuthorization else {
            return request
        }
        return authInterceptor.adapt(request)
    }

    private var baseURL: URL {
        baseURLStore.currentURL
    }
}

private extension APIEndpoint {
    var canRefreshToken: Bool {
        ![
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh"
        ].contains(path)
    }
}
