import Foundation

struct GenerateWorkoutRequest: Codable {
    let date: String
    let workoutSplit: String?
    let focusMuscle: String?
    let availableTimeMinutes: Int
    let equipment: [String]
    let avoidExercises: [String]
    let userNote: String?
    let generationMode: String

    enum CodingKeys: String, CodingKey {
        case date
        case workoutSplit = "workout_split"
        case focusMuscle = "focus_muscle"
        case availableTimeMinutes = "available_time_minutes"
        case equipment
        case avoidExercises = "avoid_exercises"
        case userNote = "user_note"
        case generationMode = "generation_mode"
    }
}

struct StartWorkoutRequest: Codable {
    let startedAt: String?

    enum CodingKeys: String, CodingKey {
        case startedAt = "started_at"
    }
}

struct StartWorkoutResponse: Codable, Hashable {
    let workoutID: String
    let workoutLogID: String
    let status: String
    let startedAt: String?

    enum CodingKeys: String, CodingKey {
        case workoutID = "workout_id"
        case workoutLogID = "workout_log_id"
        case status
        case startedAt = "started_at"
    }
}

struct LogSetRequest: Codable, Hashable {
    let workoutLogId: String
    let workoutPlanExerciseId: String
    let setNumber: Int
    let weight: Double?
    let reps: Int?
    let rpe: Int?
    let completed: Bool

    enum CodingKeys: String, CodingKey {
        case workoutLogId = "workout_log_id"
        case workoutPlanExerciseId = "workout_plan_exercise_id"
        case setNumber = "set_number"
        case weight
        case reps
        case rpe
        case completed
    }
}

struct LogSetResponse: Codable, Hashable {
    let setLogId: String
    let workoutLogId: String
    let workoutPlanExerciseId: String
    let setNumber: Int

    enum CodingKeys: String, CodingKey {
        case setLogId = "set_log_id"
        case workoutLogId = "workout_log_id"
        case workoutPlanExerciseId = "workout_plan_exercise_id"
        case setNumber = "set_number"
    }
}

struct CompleteWorkoutRequest: Codable, Hashable {
    let workoutLogId: String
    let completedAt: String?
    let durationMinutes: Int?
    let caloriesBurned: Double?
    let avgHeartRate: Double?
    let maxHeartRate: Double?
    let minHeartRate: Double?
    let difficultyFeedback: String?
    let energyAfter: Int?
    let notes: String?

    enum CodingKeys: String, CodingKey {
        case workoutLogId = "workout_log_id"
        case completedAt = "completed_at"
        case durationMinutes = "duration_minutes"
        case caloriesBurned = "calories_burned"
        case avgHeartRate = "avg_heart_rate"
        case maxHeartRate = "max_heart_rate"
        case minHeartRate = "min_heart_rate"
        case difficultyFeedback = "difficulty_feedback"
        case energyAfter = "energy_after"
        case notes
    }
}

struct CompleteWorkoutResponse: Codable, Hashable {
    let workoutId: String
    let workoutLogId: String
    let status: String
    let totalVolume: Double
    let completedAt: String?

    enum CodingKeys: String, CodingKey {
        case workoutId = "workout_id"
        case workoutLogId = "workout_log_id"
        case status
        case totalVolume = "total_volume"
        case completedAt = "completed_at"
    }
}

struct LoggedSetResponse: Codable, Identifiable, Hashable {
    let setLogID: String?
    let setNumber: Int
    let weight: Double?
    let reps: Int?
    let rpe: Int?
    let completed: Bool

    var id: String { setLogID ?? "set-\(setNumber)-\(weight ?? 0)-\(reps ?? 0)-\(rpe ?? 0)" }

    enum CodingKeys: String, CodingKey {
        case setLogID = "set_log_id"
        case setNumber = "set_number"
        case weight
        case reps
        case rpe
        case completed
    }
}

struct WorkoutExerciseResponse: Codable, Identifiable, Hashable {
    let workoutPlanExerciseID: String
    let exerciseID: String
    let name: String
    let orderIndex: Int
    let primaryMuscle: String
    let equipment: String
    let targetSets: Int
    let targetReps: String
    let targetWeight: Double?
    let restSeconds: Int?
    let targetRpe: Int?
    let notes: String?
    let loggedSets: [LoggedSetResponse]?

    var id: String { workoutPlanExerciseID }

    enum CodingKeys: String, CodingKey {
        case workoutPlanExerciseID = "workout_plan_exercise_id"
        case exerciseID = "exercise_id"
        case name
        case orderIndex = "order_index"
        case primaryMuscle = "primary_muscle"
        case equipment
        case targetSets = "target_sets"
        case targetReps = "target_reps"
        case targetWeight = "target_weight"
        case restSeconds = "rest_seconds"
        case targetRpe = "target_rpe"
        case notes
        case loggedSets = "logged_sets"
    }
}

struct WorkoutPlanResponse: Codable, Identifiable, Hashable {
    let workoutID: String
    let workoutLogID: String?
    let title: String
    let goal: String
    let focusMuscle: String?
    let estimatedDurationMinutes: Int?
    let trainingDecision: String?
    let aiReasoningSummary: String?
    let safetyNote: String?
    let status: String
    let source: String
    let exercises: [WorkoutExerciseResponse]

    var id: String { workoutID }

    enum CodingKeys: String, CodingKey {
        case workoutID = "workout_id"
        case workoutLogID = "workout_log_id"
        case title
        case goal
        case focusMuscle = "focus_muscle"
        case estimatedDurationMinutes = "estimated_duration_minutes"
        case trainingDecision = "training_decision"
        case aiReasoningSummary = "ai_reasoning_summary"
        case safetyNote = "safety_note"
        case status
        case source
        case exercises
    }

    var sourceBadgeTitle: String {
        switch source {
        case "ai":
            return "AI Generated"
        case "fallback":
            return "Safe Fallback"
        case "manual":
            return "Manual"
        default:
            return source.replacingOccurrences(of: "_", with: " ").capitalized
        }
    }

    var trainingDecisionLabel: String {
        switch trainingDecision {
        case "normal_volume":
            return "Normal volume"
        case "reduced_volume":
            return "Reduced volume"
        case "recovery":
            return "Recovery"
        case "rest_day":
            return "Rest day"
        case .some(let value):
            return value.replacingOccurrences(of: "_", with: " ").capitalized
        case .none:
            return "Not specified"
        }
    }
}

struct WorkoutHistoryResponse: Codable, Hashable {
    let items: [WorkoutHistoryItem]
    let limit: Int
    let offset: Int
    let total: Int
}

struct WorkoutHistoryItem: Codable, Identifiable, Hashable {
    let workoutId: String
    let workoutLogId: String?
    let title: String
    let date: String?
    let status: String
    let durationMinutes: Int?
    let totalVolume: Double?
    let difficultyFeedback: String?
    let focusMuscle: String?
    let trainingDecision: String?
    let source: String?

    var id: String { workoutId }

    enum CodingKeys: String, CodingKey {
        case workoutId = "workout_id"
        case workoutLogId = "workout_log_id"
        case title
        case date
        case status
        case durationMinutes = "duration_minutes"
        case totalVolume = "total_volume"
        case difficultyFeedback = "difficulty_feedback"
        case focusMuscle = "focus_muscle"
        case trainingDecision = "training_decision"
        case source
    }

    var sourceBadgeTitle: String {
        switch source {
        case "ai":
            return "AI"
        case "fallback":
            return "Fallback"
        case "manual":
            return "Manual"
        case .some(let value):
            return value.replacingOccurrences(of: "_", with: " ").capitalized
        case .none:
            return "Unknown"
        }
    }

    var statusLabel: String {
        status.replacingOccurrences(of: "_", with: " ").capitalized
    }
}

extension WorkoutPlanResponse {
    static let mockAI = WorkoutPlanResponse(
        workoutID: UUID().uuidString,
        workoutLogID: nil,
        title: "Chest Dumbbell Day",
        goal: "muscle_gain",
        focusMuscle: "chest",
        estimatedDurationMinutes: 60,
        trainingDecision: "normal_volume",
        aiReasoningSummary: "Generated from your readiness and available equipment.",
        safetyNote: "Stop if you feel sharp pain, dizziness, or unusual discomfort.",
        status: "generated",
        source: "ai",
        exercises: [
            WorkoutExerciseResponse(
                workoutPlanExerciseID: UUID().uuidString,
                exerciseID: UUID().uuidString,
                name: "Dumbbell Bench Press",
                orderIndex: 1,
                primaryMuscle: "chest",
                equipment: "dumbbell",
                targetSets: 4,
                targetReps: "8-10",
                targetWeight: nil,
                restSeconds: 90,
                targetRpe: 7,
                notes: "Keep shoulder blades stable.",
                loggedSets: nil
            ),
            WorkoutExerciseResponse(
                workoutPlanExerciseID: UUID().uuidString,
                exerciseID: UUID().uuidString,
                name: "Incline Dumbbell Press",
                orderIndex: 2,
                primaryMuscle: "chest",
                equipment: "dumbbell",
                targetSets: 3,
                targetReps: "10-12",
                targetWeight: nil,
                restSeconds: 75,
                targetRpe: 7,
                notes: nil,
                loggedSets: nil
            ),
            WorkoutExerciseResponse(
                workoutPlanExerciseID: UUID().uuidString,
                exerciseID: UUID().uuidString,
                name: "Push-up",
                orderIndex: 3,
                primaryMuscle: "chest",
                equipment: "bodyweight",
                targetSets: 3,
                targetReps: "12-15",
                targetWeight: nil,
                restSeconds: 60,
                targetRpe: 6,
                notes: "Move with control.",
                loggedSets: nil
            ),
            WorkoutExerciseResponse(
                workoutPlanExerciseID: UUID().uuidString,
                exerciseID: UUID().uuidString,
                name: "Plank",
                orderIndex: 4,
                primaryMuscle: "core",
                equipment: "bodyweight",
                targetSets: 3,
                targetReps: "30-45 sec",
                targetWeight: nil,
                restSeconds: 45,
                targetRpe: 5,
                notes: nil,
                loggedSets: nil
            ),
        ]
    )

    static let mockFallback = WorkoutPlanResponse(
        workoutID: UUID().uuidString,
        workoutLogID: nil,
        title: "Full Body Recovery Session",
        goal: "general_health",
        focusMuscle: "full_body",
        estimatedDurationMinutes: 45,
        trainingDecision: "recovery",
        aiReasoningSummary: "Generated using safe rule-based fallback.",
        safetyNote: "Stop if you feel sharp pain, dizziness, or unusual discomfort.",
        status: "generated",
        source: "fallback",
        exercises: Array(mockAI.exercises.prefix(4))
    )
}

extension WorkoutExerciseResponse {
    var suggestedDefaultReps: Int {
        let parts = targetReps
            .split(whereSeparator: { !$0.isNumber })
            .compactMap { Int($0) }
        return parts.max() ?? 10
    }

    var suggestedDefaultRPE: Int {
        targetRpe ?? 7
    }
}

extension WorkoutHistoryItem {
    static let mockCompleted = WorkoutHistoryItem(
        workoutId: UUID().uuidString,
        workoutLogId: UUID().uuidString,
        title: "Chest Dumbbell Day",
        date: "2026-06-01",
        status: "completed",
        durationMinutes: 58,
        totalVolume: 4250,
        difficultyFeedback: "just_right",
        focusMuscle: "chest",
        trainingDecision: "normal_volume",
        source: "ai"
    )

    static let mockStarted = WorkoutHistoryItem(
        workoutId: UUID().uuidString,
        workoutLogId: UUID().uuidString,
        title: "Leg Strength Session",
        date: "2026-05-30",
        status: "started",
        durationMinutes: nil,
        totalVolume: nil,
        difficultyFeedback: nil,
        focusMuscle: "legs",
        trainingDecision: "reduced_volume",
        source: "fallback"
    )
}
