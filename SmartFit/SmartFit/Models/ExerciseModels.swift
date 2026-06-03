import Foundation

struct ExerciseSummary: Codable, Identifiable {
    let id: UUID
    let name: String
    let primaryMuscle: String
    let equipment: String

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case primaryMuscle = "primary_muscle"
        case equipment
    }
}

struct ReplaceExerciseRequest: Codable, Hashable {
    let workoutId: String
    let workoutPlanExerciseId: String
    let reason: String
    let availableEquipment: [String]
    let userNote: String?

    enum CodingKeys: String, CodingKey {
        case workoutId = "workout_id"
        case workoutPlanExerciseId = "workout_plan_exercise_id"
        case reason
        case availableEquipment = "available_equipment"
        case userNote = "user_note"
    }
}

struct ReplacementCurrentExerciseResponse: Codable, Hashable {
    let exerciseId: String
    let name: String
    let primaryMuscle: String
    let equipment: String

    enum CodingKeys: String, CodingKey {
        case exerciseId = "exercise_id"
        case name
        case primaryMuscle = "primary_muscle"
        case equipment
    }
}

struct ReplacementOptionResponse: Codable, Identifiable, Hashable {
    let exerciseId: String
    let name: String
    let primaryMuscle: String
    let equipment: String
    let difficulty: String?
    let targetSets: Int
    let targetReps: String
    let restSeconds: Int
    let targetRpe: Int?
    let reason: String
    let safetyNote: String?

    var id: String { exerciseId }

    enum CodingKeys: String, CodingKey {
        case exerciseId = "exercise_id"
        case name
        case primaryMuscle = "primary_muscle"
        case equipment
        case difficulty
        case targetSets = "target_sets"
        case targetReps = "target_reps"
        case restSeconds = "rest_seconds"
        case targetRpe = "target_rpe"
        case reason
        case safetyNote = "safety_note"
    }
}

struct ReplaceExerciseResponse: Codable, Hashable {
    let currentExercise: ReplacementCurrentExerciseResponse
    let replacementOptions: [ReplacementOptionResponse]
    let safetyNote: String?

    enum CodingKeys: String, CodingKey {
        case currentExercise = "current_exercise"
        case replacementOptions = "replacement_options"
        case safetyNote = "safety_note"
    }
}

struct ApplyExerciseReplacementRequest: Codable, Hashable {
    let replacementExerciseId: String
    let targetSets: Int
    let targetReps: String
    let restSeconds: Int
    let targetRpe: Int?
    let reason: String?

    enum CodingKeys: String, CodingKey {
        case replacementExerciseId = "replacement_exercise_id"
        case targetSets = "target_sets"
        case targetReps = "target_reps"
        case restSeconds = "rest_seconds"
        case targetRpe = "target_rpe"
        case reason
    }
}

struct ApplyExerciseReplacementResponse: Codable, Hashable {
    let workoutId: String
    let workoutPlanExerciseId: String
    let replacedExerciseId: String
    let replacementExerciseId: String
    let name: String
    let primaryMuscle: String
    let equipment: String
    let targetSets: Int
    let targetReps: String
    let restSeconds: Int
    let targetRpe: Int?
    let isReplacement: Bool

    enum CodingKeys: String, CodingKey {
        case workoutId = "workout_id"
        case workoutPlanExerciseId = "workout_plan_exercise_id"
        case replacedExerciseId = "replaced_exercise_id"
        case replacementExerciseId = "replacement_exercise_id"
        case name
        case primaryMuscle = "primary_muscle"
        case equipment
        case targetSets = "target_sets"
        case targetReps = "target_reps"
        case restSeconds = "rest_seconds"
        case targetRpe = "target_rpe"
        case isReplacement = "is_replacement"
    }
}

#if DEBUG
extension ReplacementOptionResponse {
    static let mockPushUp = ReplacementOptionResponse(
        exerciseId: UUID().uuidString,
        name: "Incline Push-up",
        primaryMuscle: "chest",
        equipment: "bodyweight",
        difficulty: "moderate",
        targetSets: 3,
        targetReps: "10-12",
        restSeconds: 60,
        targetRpe: 6,
        reason: "Keeps the same movement pattern with less equipment.",
        safetyNote: "Use a stable bench or rack support."
    )

    static let mockCablePress = ReplacementOptionResponse(
        exerciseId: UUID().uuidString,
        name: "Standing Cable Chest Press",
        primaryMuscle: "chest",
        equipment: "cable_machine",
        difficulty: "moderate",
        targetSets: 3,
        targetReps: "8-10",
        restSeconds: 75,
        targetRpe: 7,
        reason: "Matches the target muscle with controlled loading.",
        safetyNote: nil
    )
}
#endif
