import Foundation

protocol ProgressRepositoryProtocol {
    func getProgressOverview(fromDate: String?, toDate: String?) async throws -> ProgressOverviewResponse
    func getPersonalRecords(limit: Int, exerciseId: String?, metric: String?) async throws -> PersonalRecordsResponse
    func getWeeklyReport(weekStart: String?) async throws -> WeeklyReportResponse
}

final class ProgressRepository: ProgressRepositoryProtocol {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func getProgressOverview(fromDate: String?, toDate: String?) async throws -> ProgressOverviewResponse {
        var queryItems: [URLQueryItem] = []
        if let fromDate, !fromDate.isEmpty {
            queryItems.append(URLQueryItem(name: "from_date", value: fromDate))
        }
        if let toDate, !toDate.isEmpty {
            queryItems.append(URLQueryItem(name: "to_date", value: toDate))
        }

        return try await apiClient.get(
            APIEndpoint(path: "/api/v1/progress/overview", method: .get, queryItems: queryItems),
            as: ProgressOverviewResponse.self
        )
    }

    func getPersonalRecords(limit: Int, exerciseId: String?, metric: String?) async throws -> PersonalRecordsResponse {
        var queryItems = [URLQueryItem(name: "limit", value: String(limit))]
        if let exerciseId, !exerciseId.isEmpty {
            queryItems.append(URLQueryItem(name: "exercise_id", value: exerciseId))
        }
        if let metric, !metric.isEmpty {
            queryItems.append(URLQueryItem(name: "metric", value: metric))
        }

        return try await apiClient.get(
            APIEndpoint(path: "/api/v1/progress/personal-records", method: .get, queryItems: queryItems),
            as: PersonalRecordsResponse.self
        )
    }

    func getWeeklyReport(weekStart: String?) async throws -> WeeklyReportResponse {
        var queryItems: [URLQueryItem] = []
        if let weekStart, !weekStart.isEmpty {
            queryItems.append(URLQueryItem(name: "week_start", value: weekStart))
        }

        return try await apiClient.get(
            APIEndpoint(path: "/api/v1/progress/weekly-report", method: .get, queryItems: queryItems),
            as: WeeklyReportResponse.self
        )
    }
}
