import Foundation

final class HealthRepository {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func saveHealthSummary(_ request: HealthSummaryRequest) async throws {
        _ = try await apiClient.post(
            APIEndpoint(path: "/api/v1/health/summary", method: .post),
            body: request,
            as: EmptyPayload.self
        )
    }

    func saveManualCheckIn(_ request: ManualCheckInRequest) async throws {
        _ = try await apiClient.post(
            APIEndpoint(path: "/api/v1/health/manual-checkin", method: .post),
            body: request,
            as: EmptyPayload.self
        )
    }
}

private struct EmptyPayload: Codable {}
