import Foundation

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
