import Foundation

protocol HistoryRepositoryProtocol {
    func getWorkoutHistory(
        limit: Int,
        offset: Int,
        status: String?,
        fromDate: String?,
        toDate: String?
    ) async throws -> WorkoutHistoryResponse
    func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse
}

final class HistoryRepository: HistoryRepositoryProtocol {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func getWorkoutHistory(
        limit: Int,
        offset: Int,
        status: String?,
        fromDate: String?,
        toDate: String?
    ) async throws -> WorkoutHistoryResponse {
        var queryItems = [
            URLQueryItem(name: "limit", value: String(limit)),
            URLQueryItem(name: "offset", value: String(offset)),
        ]

        if let status, !status.isEmpty {
            queryItems.append(URLQueryItem(name: "status", value: status))
        }
        if let fromDate, !fromDate.isEmpty {
            queryItems.append(URLQueryItem(name: "from_date", value: fromDate))
        }
        if let toDate, !toDate.isEmpty {
            queryItems.append(URLQueryItem(name: "to_date", value: toDate))
        }

        return try await apiClient.get(
            APIEndpoint(path: "/api/v1/workouts/history", method: .get, queryItems: queryItems),
            as: WorkoutHistoryResponse.self
        )
    }

    func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/workouts/\(workoutId)", method: .get),
            as: WorkoutPlanResponse.self
        )
    }
}
