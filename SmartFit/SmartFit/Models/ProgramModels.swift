import Foundation

struct CreateProgramRequest: Codable {
    let goal: String
    let durationWeeks: Int
    let daysPerWeek: Int
    let sessionDurationMinutes: Int
    let preferredSplit: String?
    let trainingStyle: String
    let focusAreas: [String]
    let generationMode: String
    let generationStrategy: String

    enum CodingKeys: String, CodingKey {
        case goal
        case durationWeeks = "duration_weeks"
        case daysPerWeek = "days_per_week"
        case sessionDurationMinutes = "session_duration_minutes"
        case preferredSplit = "preferred_split"
        case trainingStyle = "training_style"
        case focusAreas = "focus_areas"
        case generationMode = "generation_mode"
        case generationStrategy = "generation_strategy"
    }
}

struct ProgramWorkoutTemplateSummary: Codable, Identifiable, Hashable {
    var id: String { "\(dayIndex)" }
    let dayIndex: Int
    let title: String
    let focusType: String
    let workoutType: String?
    let estimatedDurationMinutes: Int?

    enum CodingKeys: String, CodingKey {
        case dayIndex = "day_index"
        case title
        case focusType = "focus_type"
        case workoutType = "workout_type"
        case estimatedDurationMinutes = "estimated_duration_minutes"
    }
}

struct ProgramCalendarDay: Codable, Identifiable, Hashable {
    var id: String { instanceId ?? "\(date)_\(dayIndex)" }
    let instanceId: String?
    let date: String
    let weekNumber: Int
    let dayIndex: Int
    let phase: String?
    let title: String
    let focusType: String?
    let status: String
    let workoutPlanId: String?
    let plannedWorkoutPlanId: String?
    let adjustedWorkoutPlanId: String?

    enum CodingKeys: String, CodingKey {
        case instanceId = "instance_id"
        case date
        case weekNumber = "week_number"
        case dayIndex = "day_index"
        case phase
        case title
        case focusType = "focus_type"
        case status
        case workoutPlanId = "workout_plan_id"
        case plannedWorkoutPlanId = "planned_workout_plan_id"
        case adjustedWorkoutPlanId = "adjusted_workout_plan_id"
    }
}

struct CreateProgramResponse: Codable, Identifiable, Hashable {
    var id: String { programId }
    let programId: String
    let name: String
    let durationWeeks: Int
    let daysPerWeek: Int
    let status: String
    let currentWeek: Int
    let currentPhase: String?
    let weeklyStructure: [ProgramWorkoutTemplateSummary]
    let calendarPreview: [ProgramCalendarDay]
    let totalScheduledWorkouts: Int?

    enum CodingKeys: String, CodingKey {
        case programId = "program_id"
        case name
        case durationWeeks = "duration_weeks"
        case daysPerWeek = "days_per_week"
        case status
        case currentWeek = "current_week"
        case currentPhase = "current_phase"
        case weeklyStructure = "weekly_structure"
        case calendarPreview = "calendar_preview"
        case totalScheduledWorkouts = "total_scheduled_workouts"
    }

    private enum AlternateCodingKeys: String, CodingKey {
        case id
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let alternateContainer = try decoder.container(keyedBy: AlternateCodingKeys.self)
        programId = try container.decodeIfPresent(String.self, forKey: .programId)
            ?? alternateContainer.decode(String.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        durationWeeks = try container.decode(Int.self, forKey: .durationWeeks)
        daysPerWeek = try container.decode(Int.self, forKey: .daysPerWeek)
        status = try container.decode(String.self, forKey: .status)
        currentWeek = try container.decodeIfPresent(Int.self, forKey: .currentWeek) ?? 1
        currentPhase = try container.decodeIfPresent(String.self, forKey: .currentPhase)
        weeklyStructure = try container.decodeIfPresent([ProgramWorkoutTemplateSummary].self, forKey: .weeklyStructure) ?? []
        calendarPreview = try container.decodeIfPresent([ProgramCalendarDay].self, forKey: .calendarPreview) ?? []
        totalScheduledWorkouts = try container.decodeIfPresent(Int.self, forKey: .totalScheduledWorkouts)
    }
}

struct ActiveProgramResponse: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let goal: String
    let trainingLevel: String
    let trainingStyle: String?
    let durationWeeks: Int
    let daysPerWeek: Int
    let sessionDurationMinutes: Int
    let preferredSplit: String
    let status: String
    let startDate: String
    let endDate: String
    let currentWeek: Int
    let currentDayIndex: Int
    let generationMode: String
    let focusAreas: [String]
    let generationStrategy: String?
    let currentPhase: String?
    let totalScheduledWorkouts: Int
    let completedWorkoutsCount: Int
    let weeklyStructure: [ProgramWorkoutTemplateSummary]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case goal
        case trainingLevel = "training_level"
        case trainingStyle = "training_style"
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
        case generationStrategy = "generation_strategy"
        case currentPhase = "current_phase"
        case totalScheduledWorkouts = "total_scheduled_workouts"
        case completedWorkoutsCount = "completed_workouts_count"
        case weeklyStructure = "weekly_structure"
    }

    var progress: Double {
        guard durationWeeks > 0 else { return 0 }
        return min(max(Double(currentWeek) / Double(durationWeeks), 0), 1)
    }
}

// Keep TrainingProgramResponse as alias for ActiveProgramResponse to avoid breaking existing code
typealias TrainingProgramResponse = ActiveProgramResponse

struct ProgramWeekResponse: Codable, Hashable {
    let programId: String
    let weekNumber: Int
    let phase: String?
    let workouts: [ProgramCalendarDay]

    enum CodingKeys: String, CodingKey {
        case programId = "program_id"
        case weekNumber = "week_number"
        case phase
        case workouts
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        programId = try container.decodeIfPresent(String.self, forKey: .programId) ?? ""
        weekNumber = try container.decodeIfPresent(Int.self, forKey: .weekNumber) ?? 0
        phase = try container.decodeIfPresent(String.self, forKey: .phase)
        workouts = try container.decodeIfPresent([ProgramCalendarDay].self, forKey: .workouts) ?? []
    }
}

struct ScheduledProgramWorkout: Codable, Hashable {
    let instanceId: String
    let title: String
    let focusType: String
    let status: String
    let plannedWorkoutPlanId: String?

    enum CodingKeys: String, CodingKey {
        case instanceId = "instance_id"
        case title
        case focusType = "focus_type"
        case status
        case plannedWorkoutPlanId = "planned_workout_plan_id"
    }
}

struct ProgramWorkoutRecommendation: Codable, Hashable {
    let action: String
    let readinessAdjustment: String?
    let message: String

    enum CodingKeys: String, CodingKey {
        case action
        case readinessAdjustment = "readiness_adjustment"
        case message
    }

    init(action: String, readinessAdjustment: String?, message: String) {
        self.action = action
        self.readinessAdjustment = readinessAdjustment
        self.message = message
    }

    init(from decoder: Decoder) throws {
        if let message = try? decoder.singleValueContainer().decode(String.self) {
            self.action = "info"
            self.readinessAdjustment = nil
            self.message = message
            return
        }

        let container = try decoder.container(keyedBy: CodingKeys.self)
        action = try container.decodeIfPresent(String.self, forKey: .action) ?? "info"
        readinessAdjustment = try container.decodeIfPresent(String.self, forKey: .readinessAdjustment)
        message = try container.decodeIfPresent(String.self, forKey: .message) ?? ""
    }
}

struct TodayProgramWorkoutResponse: Codable, Hashable {
    let programId: String
    let weekNumber: Int
    let phase: String?
    let scheduledWorkout: ScheduledProgramWorkout?
    let recommendation: ProgramWorkoutRecommendation?

    // Backward compatibility
    let scheduled: Bool?
    let instanceId: String?
    let template: ProgramWorkoutTemplateSummary?
    let status: String?
    let workoutPlanId: String?
    let dayIndex: Int?

    enum CodingKeys: String, CodingKey {
        case programId = "program_id"
        case weekNumber = "week_number"
        case phase
        case scheduledWorkout = "scheduled_workout"
        case recommendation
        case scheduled
        case instanceId = "instance_id"
        case template
        case status
        case workoutPlanId = "workout_plan_id"
        case dayIndex = "day_index"
    }
}

extension String {
    var programDisplayName: String {
        replacingOccurrences(of: "_", with: " ").capitalized
    }
}
