import Foundation

protocol AIChatRepositoryProtocol {
    func getHistory(workoutId: String, limit: Int, offset: Int) async throws -> AIChatHistoryResponse
    func sendMessage(_ request: AIChatRequest) async throws -> AIChatResponse
}

final class AIChatRepository: AIChatRepositoryProtocol {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func getHistory(workoutId: String, limit: Int = 50, offset: Int = 0) async throws -> AIChatHistoryResponse {
        try await apiClient.get(
            APIEndpoint(
                path: "/api/v1/ai/chat/history",
                method: .get,
                queryItems: [
                    URLQueryItem(name: "workout_id", value: workoutId),
                    URLQueryItem(name: "limit", value: String(limit)),
                    URLQueryItem(name: "offset", value: String(offset)),
                ]
            ),
            as: AIChatHistoryResponse.self
        )
    }

    func sendMessage(_ request: AIChatRequest) async throws -> AIChatResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/ai/chat", method: .post),
            body: request,
            as: AIChatResponse.self
        )
    }
}
