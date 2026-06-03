import Foundation

final class ReadinessRepository {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func calculateReadiness(date: String) async throws -> ReadinessResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/readiness/calculate", method: .post),
            body: CalculateReadinessRequest(date: date),
            as: ReadinessResponse.self
        )
    }

    func getTodayReadiness() async throws -> ReadinessResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/readiness/today", method: .get),
            as: ReadinessResponse.self
        )
    }

    func getReadinessHistory(days: Int) async throws -> [ReadinessHistoryItem] {
        let items = try await apiClient.get(
            APIEndpoint(path: "/api/v1/readiness/history", method: .get),
            as: [ReadinessResponse].self
        )
        return Array(items.prefix(days)).map(ReadinessHistoryItem.init(from:))
    }
}
