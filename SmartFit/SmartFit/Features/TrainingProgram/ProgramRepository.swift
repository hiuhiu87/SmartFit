import Foundation

protocol ProgramRepositoryProtocol {
    func createProgram(_ request: CreateProgramRequest) async throws -> TrainingProgramResponse
    func getActiveProgram() async throws -> TrainingProgramResponse?
    func getTodayWorkout(date: String) async throws -> ProgramTodayWorkoutResponse
    func generateTodayWorkout(date: String) async throws -> WorkoutPlanResponse
}

final class ProgramRepository: ProgramRepositoryProtocol {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func createProgram(_ request: CreateProgramRequest) async throws -> TrainingProgramResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/programs", method: .post),
            body: request,
            as: TrainingProgramResponse.self
        )
    }

    func getActiveProgram() async throws -> TrainingProgramResponse? {
        do {
            return try await apiClient.get(
                APIEndpoint(path: "/api/v1/programs/active", method: .get),
                as: TrainingProgramResponse.self
            )
        } catch APIError.server(let code, _) where code == "not_found" {
            return nil
        }
    }

    func getTodayWorkout(date: String) async throws -> ProgramTodayWorkoutResponse {
        try await apiClient.get(
            APIEndpoint(
                path: "/api/v1/programs/active/today",
                method: .get,
                queryItems: [URLQueryItem(name: "date", value: date)]
            ),
            as: ProgramTodayWorkoutResponse.self
        )
    }

    func generateTodayWorkout(date: String) async throws -> WorkoutPlanResponse {
        try await apiClient.post(
            APIEndpoint(
                path: "/api/v1/programs/active/today/generate",
                method: .post,
                queryItems: [URLQueryItem(name: "date", value: date)]
            ),
            body: EmptyProgramRequest(),
            as: WorkoutPlanResponse.self
        )
    }
}

private struct EmptyProgramRequest: Codable {}
