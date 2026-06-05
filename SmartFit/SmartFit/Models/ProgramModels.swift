import Foundation

struct CreateProgramRequest: Codable {
    let goal: String
    let durationWeeks: Int
    let daysPerWeek: Int
    let sessionDurationMinutes: Int
    let preferredSplit: String
    let focusAreas: [String]
    let generationMode: String
    let trainingStyle: String?

    enum CodingKeys: String, CodingKey {
        case goal
        case durationWeeks = "duration_weeks"
        case daysPerWeek = "days_per_week"
        case sessionDurationMinutes = "session_duration_minutes"
        case preferredSplit = "preferred_split"
        case focusAreas = "focus_areas"
        case generationMode = "generation_mode"
        case trainingStyle = "training_style"
    }
}

struct ProgramTemplateSlot: Codable, Identifiable, Hashable {
    let id: String
    let slotOrder: Int
    let slotType: String
    let movementPatterns: [String]
    let primaryMuscles: [String]
    let exerciseRoles: [String]
    let required: Bool
    let baseSets: Int
    let baseReps: String
    let baseRestSeconds: Int
    let baseRpe: Int
    let progressionRule: String

    enum CodingKeys: String, CodingKey {
        case id
        case slotOrder = "slot_order"
        case slotType = "slot_type"
        case movementPatterns = "movement_patterns"
        case primaryMuscles = "primary_muscles"
        case exerciseRoles = "exercise_roles"
        case required
        case baseSets = "base_sets"
        case baseReps = "base_reps"
        case baseRestSeconds = "base_rest_seconds"
        case baseRpe = "base_rpe"
        case progressionRule = "progression_rule"
    }
}

struct ProgramWorkoutTemplate: Codable, Identifiable, Hashable {
    let id: String
    let dayIndex: Int
    let title: String
    let focusType: String
    let workoutType: String
    let estimatedDurationMinutes: Int
    let sequenceOrder: Int
    let slots: [ProgramTemplateSlot]

    enum CodingKeys: String, CodingKey {
        case id
        case dayIndex = "day_index"
        case title
        case focusType = "focus_type"
        case workoutType = "workout_type"
        case estimatedDurationMinutes = "estimated_duration_minutes"
        case sequenceOrder = "sequence_order"
        case slots
    }
}

struct TrainingProgramResponse: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let goal: String
    let trainingLevel: String
    let durationWeeks: Int
    let daysPerWeek: Int
    let sessionDurationMinutes: Int
    let preferredSplit: String
    let status: String
    let trainingStyle: String?
    let startDate: String
    let endDate: String
    let currentWeek: Int
    let currentDayIndex: Int
    let generationMode: String
    let focusAreas: [String]
    let weeklyStructure: [ProgramWorkoutTemplate]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case goal
        case trainingLevel = "training_level"
        case durationWeeks = "duration_weeks"
        case daysPerWeek = "days_per_week"
        case sessionDurationMinutes = "session_duration_minutes"
        case preferredSplit = "preferred_split"
        case status
        case startDate = "start_date"
        case endDate = "end_date"
        case currentWeek = "current_week"
        case currentDayIndex = "current_day_index"
        case generationMode = "generation_mode"
        case focusAreas = "focus_areas"
        case weeklyStructure = "weekly_structure"
        case trainingStyle = "training_style"
    }

    var progress: Double {
        guard durationWeeks > 0 else { return 0 }
        return min(max(Double(currentWeek) / Double(durationWeeks), 0), 1)
    }
}

struct ProgramTodayWorkoutResponse: Codable, Hashable {
    let programID: String
    let scheduled: Bool
    let recommendation: String
    let weekNumber: Int?
    let dayIndex: Int?
    let instanceID: String?
    let template: ProgramWorkoutTemplate?
    let status: String?
    let workoutPlanID: String?

    enum CodingKeys: String, CodingKey {
        case programID = "program_id"
        case scheduled
        case recommendation
        case weekNumber = "week_number"
        case dayIndex = "day_index"
        case instanceID = "instance_id"
        case template
        case status
        case workoutPlanID = "workout_plan_id"
    }
}

extension String {
    var programDisplayName: String {
        replacingOccurrences(of: "_", with: " ").capitalized
    }
}
