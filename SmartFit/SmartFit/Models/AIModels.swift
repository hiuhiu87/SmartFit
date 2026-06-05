import Foundation

struct AIChatRequest: Codable {
    let workoutId: String
    let currentWorkoutPlanExerciseId: String?
    let message: String

    enum CodingKeys: String, CodingKey {
        case workoutId = "workout_id"
        case currentWorkoutPlanExerciseId = "current_workout_plan_exercise_id"
        case message
    }
}

struct AIChatSuggestedAction: Codable, Hashable {
    let type: String
    let exerciseId: String?
    let exerciseName: String?
    let targetSets: Int?
    let targetReps: String?
    let restSeconds: Int?
    let targetRpe: Int?
    let reason: String?

    enum CodingKeys: String, CodingKey {
        case type
        case exerciseId = "exercise_id"
        case exerciseName = "exercise_name"
        case targetSets = "target_sets"
        case targetReps = "target_reps"
        case restSeconds = "rest_seconds"
        case targetRpe = "target_rpe"
        case reason
    }
}

struct AIChatResponse: Codable, Hashable {
    let reply: String
    let intent: String
    let suggestedAction: AIChatSuggestedAction?

    enum CodingKeys: String, CodingKey {
        case reply
        case intent
        case suggestedAction = "suggested_action"
    }
}

struct AIChatHistoryItem: Codable, Identifiable, Hashable {
    let id: String
    let role: String
    let message: String
    let suggestedAction: AIChatSuggestedAction?
    let workoutPlanExerciseId: String?
    let createdAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case role
        case message
        case suggestedAction = "suggested_action"
        case workoutPlanExerciseId = "workout_plan_exercise_id"
        case createdAt = "created_at"
    }
}

struct AIChatHistoryResponse: Codable, Hashable {
    let items: [AIChatHistoryItem]
    let limit: Int
    let offset: Int
    let total: Int
}

struct AIUsageTodayResponse: Codable {
    let date: String
    let plan: String
    let usage: AIUsageCounts
    let limits: AIUsageLimits
}

struct AIUsageCounts: Codable {
    let aiWorkoutCount: Int
    let aiChatCount: Int
    let aiReplacementCount: Int
    let aiWeeklyReportCount: Int
    let totalAICount: Int

    enum CodingKeys: String, CodingKey {
        case aiWorkoutCount = "ai_workout_count"
        case aiChatCount = "ai_chat_count"
        case aiReplacementCount = "ai_replacement_count"
        case aiWeeklyReportCount = "ai_weekly_report_count"
        case totalAICount = "total_ai_count"
    }
}

struct AIUsageLimits: Codable {
    let aiWorkoutLimit: Int
    let aiChatLimit: Int
    let aiReplacementLimit: Int
    let aiWeeklyReportLimit: Int
    let totalAILimit: Int

    enum CodingKeys: String, CodingKey {
        case aiWorkoutLimit = "ai_workout_limit"
        case aiChatLimit = "ai_chat_limit"
        case aiReplacementLimit = "ai_replacement_limit"
        case aiWeeklyReportLimit = "ai_weekly_report_limit"
        case totalAILimit = "total_ai_limit"
    }
}
