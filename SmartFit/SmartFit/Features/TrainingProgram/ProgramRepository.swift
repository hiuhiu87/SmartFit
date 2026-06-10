import Foundation

protocol ProgramRepositoryProtocol {
    func createProgram(_ request: CreateProgramRequest) async throws -> CreateProgramResponse
    func getActiveProgram() async throws -> ActiveProgramResponse?
    func getProgramCalendar(fromDate: String?, toDate: String?) async throws -> [ProgramCalendarDay]
    func getProgramWeek(programId: String, weekNumber: Int) async throws -> ProgramWeekResponse
    func getTodayProgramWorkout() async throws -> TodayProgramWorkoutResponse
    func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse
    func skipProgramWorkout(instanceId: String) async throws
    func rescheduleProgramWorkout(instanceId: String, newDate: String) async throws
    func adjustTodayWorkout(instanceId: String, adjustmentType: String, reason: String?) async throws -> WorkoutPlanResponse
}

final class ProgramRepository: ProgramRepositoryProtocol {
    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func createProgram(_ request: CreateProgramRequest) async throws -> CreateProgramResponse {
        try await apiClient.post(
            APIEndpoint(path: "/api/v1/programs", method: .post),
            body: request,
            as: CreateProgramResponse.self
        )
    }

    func getActiveProgram() async throws -> ActiveProgramResponse? {
        do {
            return try await apiClient.get(
                APIEndpoint(path: "/api/v1/programs/active", method: .get),
                as: ActiveProgramResponse.self
            )
        } catch APIError.server(let code, _) where code == "not_found" {
            return nil
        }
    }

    func getProgramCalendar(fromDate: String?, toDate: String?) async throws -> [ProgramCalendarDay] {
        var queryItems: [URLQueryItem] = []
        if let fromDate = fromDate {
            queryItems.append(URLQueryItem(name: "from_date", value: fromDate))
        }
        if let toDate = toDate {
            queryItems.append(URLQueryItem(name: "to_date", value: toDate))
        }
        
        return try await apiClient.get(
            APIEndpoint(path: "/api/v1/programs/active/calendar", method: .get, queryItems: queryItems),
            as: [ProgramCalendarDay].self
        )
    }

    func getProgramWeek(programId: String, weekNumber: Int) async throws -> ProgramWeekResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/programs/\(programId)/weeks/\(weekNumber)", method: .get),
            as: ProgramWeekResponse.self
        )
    }

    func getTodayProgramWorkout() async throws -> TodayProgramWorkoutResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/programs/active/today", method: .get),
            as: TodayProgramWorkoutResponse.self
        )
    }

    func getWorkoutDetail(workoutId: String) async throws -> WorkoutPlanResponse {
        try await apiClient.get(
            APIEndpoint(path: "/api/v1/workouts/\(workoutId)", method: .get),
            as: WorkoutPlanResponse.self
        )
    }

    func skipProgramWorkout(instanceId: String) async throws {
        _ = try await apiClient.post(
            APIEndpoint(path: "/api/v1/programs/workouts/\(instanceId)/skip", method: .post),
            body: EmptyBody(),
            as: TodayProgramWorkoutResponse.self
        )
    }

    func rescheduleProgramWorkout(instanceId: String, newDate: String) async throws {
        struct RescheduleRequest: Codable {
            let scheduledDate: String
            enum CodingKeys: String, CodingKey {
                case scheduledDate = "scheduled_date"
            }
        }
        
        _ = try await apiClient.post(
            APIEndpoint(path: "/api/v1/programs/workouts/\(instanceId)/reschedule", method: .post),
            body: RescheduleRequest(scheduledDate: newDate),
            as: TodayProgramWorkoutResponse.self
        )
    }

    func adjustTodayWorkout(instanceId: String, adjustmentType: String, reason: String?) async throws -> WorkoutPlanResponse {
        struct AdjustRequest: Codable {
            let instanceId: String
            let adjustmentType: String
            let reason: String?
            enum CodingKeys: String, CodingKey {
                case instanceId = "instance_id"
                case adjustmentType = "adjustment_type"
                case reason
            }
        }
        
        return try await apiClient.post(
            APIEndpoint(path: "/api/v1/programs/active/today/adjust", method: .post),
            body: AdjustRequest(instanceId: instanceId, adjustmentType: adjustmentType, reason: reason),
            as: WorkoutPlanResponse.self
        )
    }
}

private struct EmptyBody: Codable {}
