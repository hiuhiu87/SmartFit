import Foundation

struct ProgressOverviewResponse: Codable, Hashable {
    let fromDate: String
    let toDate: String
    let weeklyWorkoutsCompleted: Int
    let weeklyWorkoutTarget: Int
    let consistencyPercentage: Int
    let totalVolumeThisWeek: Double
    let averageReadinessThisWeek: Double?
    let completedWorkoutDays: [String]
    let latestCompletedWorkout: LatestCompletedWorkout?
    let muscleDistribution: [MuscleDistributionItem]

    enum CodingKeys: String, CodingKey {
        case fromDate = "from_date"
        case toDate = "to_date"
        case weeklyWorkoutsCompleted = "weekly_workouts_completed"
        case weeklyWorkoutTarget = "weekly_workout_target"
        case consistencyPercentage = "consistency_percentage"
        case totalVolumeThisWeek = "total_volume_this_week"
        case averageReadinessThisWeek = "average_readiness_this_week"
        case completedWorkoutDays = "completed_workout_days"
        case latestCompletedWorkout = "latest_completed_workout"
        case muscleDistribution = "muscle_distribution"
    }
}

struct LatestCompletedWorkout: Codable, Hashable {
    let workoutId: String
    let workoutLogId: String?
    let title: String
    let completedAt: String?
    let durationMinutes: Int?
    let totalVolume: Double?
    let focusMuscle: String?

    enum CodingKeys: String, CodingKey {
        case workoutId = "workout_id"
        case workoutLogId = "workout_log_id"
        case title
        case completedAt = "completed_at"
        case durationMinutes = "duration_minutes"
        case totalVolume = "total_volume"
        case focusMuscle = "focus_muscle"
    }
}

struct MuscleDistributionItem: Codable, Identifiable, Hashable {
    var id: String { muscle }

    let muscle: String
    let workoutCount: Int
    let setCount: Int
    let volume: Double
    let percentage: Int

    enum CodingKeys: String, CodingKey {
        case muscle
        case workoutCount = "workout_count"
        case setCount = "set_count"
        case volume
        case percentage
    }
}

struct PersonalRecordsResponse: Codable, Hashable {
    let items: [PersonalRecordItem]
    let limit: Int
    let total: Int
}

struct PersonalRecordItem: Codable, Identifiable, Hashable {
    let exerciseId: String
    let exerciseName: String
    let primaryMuscle: String
    let bestWeight: Double?
    let bestReps: Int?
    let bestSetVolume: Double?
    let estimatedOneRepMax: Double?
    let workoutId: String?
    let workoutLogId: String?
    let achievedAt: String?

    var id: String { workoutLogId ?? exerciseId }

    enum CodingKeys: String, CodingKey {
        case exerciseId = "exercise_id"
        case exerciseName = "exercise_name"
        case primaryMuscle = "primary_muscle"
        case bestWeight = "best_weight"
        case bestReps = "best_reps"
        case bestSetVolume = "best_set_volume"
        case estimatedOneRepMax = "estimated_1rm"
        case workoutId = "workout_id"
        case workoutLogId = "workout_log_id"
        case achievedAt = "achieved_at"
    }
}

struct WeeklyReportResponse: Codable, Hashable {
    let weekStart: String
    let weekEnd: String
    let summary: String
    let highlights: [String]
    let suggestions: [String]
    let overview: ProgressOverviewResponse?

    enum CodingKeys: String, CodingKey {
        case weekStart = "week_start"
        case weekEnd = "week_end"
        case summary
        case highlights
        case suggestions
        case overview
    }
}

extension ProgressOverviewResponse {
    static let mock = ProgressOverviewResponse(
        fromDate: "2026-05-26",
        toDate: "2026-06-01",
        weeklyWorkoutsCompleted: 3,
        weeklyWorkoutTarget: 4,
        consistencyPercentage: 75,
        totalVolumeThisWeek: 14950,
        averageReadinessThisWeek: 68,
        completedWorkoutDays: ["2026-05-26", "2026-05-28", "2026-06-01"],
        latestCompletedWorkout: .mock,
        muscleDistribution: [
            .init(muscle: "chest", workoutCount: 1, setCount: 9, volume: 4250, percentage: 30),
            .init(muscle: "back", workoutCount: 1, setCount: 8, volume: 3900, percentage: 25),
            .init(muscle: "legs", workoutCount: 1, setCount: 10, volume: 4800, percentage: 35),
        ]
    )
}

extension LatestCompletedWorkout {
    static let mock = LatestCompletedWorkout(
        workoutId: UUID().uuidString,
        workoutLogId: UUID().uuidString,
        title: "Chest Dumbbell Day",
        completedAt: "2026-06-01T19:00:00Z",
        durationMinutes: 58,
        totalVolume: 4250,
        focusMuscle: "chest"
    )
}

extension PersonalRecordItem {
    static let mock = PersonalRecordItem(
        exerciseId: UUID().uuidString,
        exerciseName: "Dumbbell Bench Press",
        primaryMuscle: "chest",
        bestWeight: 22,
        bestReps: 8,
        bestSetVolume: 176,
        estimatedOneRepMax: 27.87,
        workoutId: UUID().uuidString,
        workoutLogId: UUID().uuidString,
        achievedAt: "2026-06-01T19:00:00Z"
    )
}

extension WeeklyReportResponse {
    static let mock = WeeklyReportResponse(
        weekStart: "2026-05-26",
        weekEnd: "2026-06-01",
        summary: "You completed 3 out of 4 planned workouts this week.",
        highlights: [
            "Your total training volume this week was 14,950 kg.",
            "Your average readiness was 68.",
            "Chest was your most trained muscle group.",
        ],
        suggestions: [
            "Try to complete one more workout next week to reach your target.",
            "Consider placing a rest day after your highest-volume session.",
        ],
        overview: .mock
    )
}
