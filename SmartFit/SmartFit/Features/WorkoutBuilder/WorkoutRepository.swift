import Foundation

protocol WorkoutRepositoryProtocol {
    func generateWorkout(_ request: GenerateWorkoutRequest) async throws -> WorkoutPlanResponse
    func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse
    func startWorkout(workoutId: String, request: StartWorkoutRequest) async throws -> StartWorkoutResponse
    func logSet(workoutId: String, request: LogSetRequest) async throws -> LogSetResponse
    func completeWorkout(workoutId: String, request: CompleteWorkoutRequest) async throws -> CompleteWorkoutResponse
    func suggestReplacement(_ request: ReplaceExerciseRequest) async throws -> ReplaceExerciseResponse
    func applyReplacement(
        workoutId: String,
        workoutPlanExerciseId: String,
        request: ApplyExerciseReplacementRequest
    ) async throws -> ApplyExerciseReplacementResponse
}

final class WorkoutRepository: WorkoutRepositoryProtocol {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func generateWorkout(_ request: GenerateWorkoutRequest) async throws -> WorkoutPlanResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/workouts/generate", method: .post),
            body: request,
            as: WorkoutPlanResponse.self
        )
    }

    func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/workouts/\(workoutId)", method: .get),
            as: WorkoutPlanResponse.self
        )
    }

    func startWorkout(workoutId: String, request: StartWorkoutRequest) async throws -> StartWorkoutResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/workouts/\(workoutId)/start", method: .post),
            body: request,
            as: StartWorkoutResponse.self
        )
    }

    func logSet(workoutId: String, request: LogSetRequest) async throws -> LogSetResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/workouts/\(workoutId)/sets", method: .post),
            body: request,
            as: LogSetResponse.self
        )
    }

    func completeWorkout(workoutId: String, request: CompleteWorkoutRequest) async throws -> CompleteWorkoutResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/workouts/\(workoutId)/complete", method: .post),
            body: request,
            as: CompleteWorkoutResponse.self
        )
    }

    func suggestReplacement(_ request: ReplaceExerciseRequest) async throws -> ReplaceExerciseResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/exercises/replace", method: .post),
            body: request,
            as: ReplaceExerciseResponse.self
        )
    }

    func applyReplacement(
        workoutId: String,
        workoutPlanExerciseId: String,
        request: ApplyExerciseReplacementRequest
    ) async throws -> ApplyExerciseReplacementResponse {
        try await apiClient.post(
            APIEndpoint(
                path: "/api/v1/workouts/\(workoutId)/exercises/\(workoutPlanExerciseId)/replace",
                method: .post
            ),
            body: request,
            as: ApplyExerciseReplacementResponse.self
        )
    }
}
