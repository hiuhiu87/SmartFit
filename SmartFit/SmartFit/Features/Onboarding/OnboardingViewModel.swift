import Combine
import Foundation

@MainActor
final class OnboardingViewModel: ObservableObject {
    enum Step: Int, CaseIterable {
        case goal
        case trainingLevel
        case lifestyle
        case trainingHistory
        case limitations
        case trainingStyle
        case schedule
        case equipment
        case safety

        var title: String {
            switch self {
            case .goal: "Your Goal"
            case .trainingLevel: "Training Level"
            case .lifestyle: "Daily Lifestyle"
            case .trainingHistory: "Training History"
            case .limitations: "Movement Comfort"
            case .trainingStyle: "Training Style"
            case .schedule: "Weekly Schedule"
            case .equipment: "Available Equipment"
            case .safety: "Safety First"
            }
        }
    }

    @Published var currentStep: Step = .goal
    @Published var selectedGoal = "general_health"
    @Published var selectedTrainingLevel = "beginner"
    @Published var selectedTrainingStyle = "balanced"
    @Published var selectedLifestyleType: String?
    @Published var sittingHoursPerDay = 8.0
    @Published var selectedTrainingHistory: String?
    @Published var monthsInactive = 3
    @Published var selectedLimitations: Set<String> = []
    @Published var trainingDaysPerWeek = 3
    @Published var selectedEquipment: Set<String> = ["bodyweight"]
    @Published var acceptedSafetyDisclaimer = false
    @Published var isSubmitting = false
    @Published var errorMessage: String?

    private var repository: OnboardingRepository?
    private weak var appState: AppState?

    let goalOptions: [OnboardingOption] = [
        .init(id: "general_health", title: "General Health", subtitle: "Train consistently and feel better day to day."),
        .init(id: "muscle_gain", title: "Muscle Gain", subtitle: "Focus on hypertrophy and progressive overload."),
        .init(id: "fat_loss", title: "Fat Loss", subtitle: "Train around energy balance and sustainability."),
        .init(id: "strength", title: "Strength", subtitle: "Bias toward lower reps and heavier compound work."),
    ]

    let trainingLevelOptions: [OnboardingOption] = [
        .init(id: "beginner", title: "Beginner", subtitle: "New to structured training or restarting."),
        .init(id: "intermediate", title: "Intermediate", subtitle: "Comfortable with consistent gym sessions."),
        .init(id: "advanced", title: "Advanced", subtitle: "Experienced lifter with strong exercise literacy."),
    ]

    let lifestyleOptions: [OnboardingOption] = [
        .init(id: "sedentary", title: "Mostly sitting", subtitle: "Most of my day is spent seated, with light movement."),
        .init(id: "moderately_active", title: "Moderately active", subtitle: "I move regularly through errands, walking, or a mixed workday."),
        .init(id: "active", title: "Active job or lifestyle", subtitle: "My day already includes plenty of standing, walking, or physical work."),
    ]

    let trainingHistoryOptions: [OnboardingOption] = [
        .init(id: "new_to_training", title: "New to training", subtitle: "I am learning the basics and building a comfortable routine."),
        .init(id: "returning_after_break", title: "Returning after a break", subtitle: "I have trained before and want a gradual return."),
        .init(id: "beginner_consistent", title: "Beginner but consistent", subtitle: "I train regularly and am still building confidence."),
        .init(id: "intermediate", title: "Intermediate", subtitle: "I am comfortable with structured workouts and common exercises."),
        .init(id: "advanced", title: "Advanced", subtitle: "I have substantial training experience and strong exercise awareness."),
    ]

    let limitationOptions: [OnboardingOption] = [
        .init(id: "shoulder_overhead", title: "Shoulder overhead discomfort", subtitle: "Overhead positions may need a more comfortable alternative."),
        .init(id: "lower_back_sensitive", title: "Lower back sensitive", subtitle: "Supported and stable positions usually feel better."),
        .init(id: "knee_discomfort", title: "Knee discomfort", subtitle: "Squat and lunge choices may need thoughtful adjustments."),
        .init(id: "wrist_pressure", title: "Wrist pressure", subtitle: "Loaded wrist positions can sometimes feel uncomfortable."),
        .init(id: "hip_mobility_limitation", title: "Hip mobility limitation", subtitle: "Some deep hip positions may need a smaller range of motion."),
        .init(id: "none", title: "None", subtitle: "I do not have a movement limitation to note right now."),
    ]

    let trainingStyleOptions: [OnboardingOption] = [
        .init(id: "balanced", title: "Balanced Fitness", subtitle: "Strength, muscle, cardio, and core"),
        .init(id: "hypertrophy", title: "Muscle Growth", subtitle: "More volume and muscle-focused training"),
        .init(id: "strength", title: "Strength Focus", subtitle: "Heavier compound lifts, longer rest"),
        .init(id: "conditioning", title: "Conditioning", subtitle: "More cardio and full-body work"),
        .init(id: "posture", title: "Posture & Back", subtitle: "More back, rear delts, and core stability"),
        .init(id: "glute_core", title: "Glutes & Core", subtitle: "Lower body and core emphasis"),
        .init(id: "returning", title: "Returning Beginner", subtitle: "Moderate volume and safer exercise choices"),
    ]

    let equipmentOptions: [OnboardingOption] = [
        .init(id: "bodyweight", title: "Bodyweight", subtitle: "Floor work and mobility only."),
        .init(id: "dumbbell", title: "Dumbbells", subtitle: "Adjustable or fixed dumbbells."),
        .init(id: "bench", title: "Bench", subtitle: "Flat or adjustable bench."),
        .init(id: "barbell", title: "Barbell", subtitle: "Barbell and plates."),
        .init(id: "cable_machine", title: "Cable Machine", subtitle: "Functional trainer or pulley stack."),
        .init(id: "smith_machine", title: "Smith Machine", subtitle: "Guided bar path station."),
        .init(id: "machine", title: "Selectorized Machines", subtitle: "Chest press, row, leg press, etc."),
        .init(id: "pull_up_bar", title: "Pull-up Bar", subtitle: "Fixed bar for hangs, pull-ups, leg raises."),
        .init(id: "resistance_band", title: "Resistance Bands", subtitle: "Loop or tube bands."),
        .init(id: "treadmill", title: "Treadmill", subtitle: "Cardio or incline walking."),
    ]

    func configure(appState: AppState) {
        if self.appState === appState { return }
        self.appState = appState
        self.repository = appState.environment.onboardingRepository
        hydrateFromCurrentUser(appState.currentUser)
    }

    func goToNextStep() {
        errorMessage = nil
        guard validateCurrentStep() else { return }
        if let next = Step(rawValue: currentStep.rawValue + 1) {
            currentStep = next
        }
    }

    func goToPreviousStep() {
        errorMessage = nil
        if let previous = Step(rawValue: currentStep.rawValue - 1) {
            currentStep = previous
        }
    }

    func toggleEquipment(_ equipmentType: String) {
        if selectedEquipment.contains(equipmentType) {
            if selectedEquipment.count > 1 {
                selectedEquipment.remove(equipmentType)
            }
        } else {
            selectedEquipment.insert(equipmentType)
        }
    }

    func selectTrainingHistory(_ history: String) {
        selectedTrainingHistory = history
        switch history {
        case "new_to_training", "returning_after_break", "beginner_consistent":
            selectedTrainingLevel = "beginner"
        case "intermediate":
            selectedTrainingLevel = "intermediate"
        case "advanced":
            selectedTrainingLevel = "advanced"
        default:
            break
        }
        if history == "returning_after_break" {
            selectedTrainingStyle = "returning"
        }
    }

    func toggleLimitation(_ limitation: String) {
        if limitation == "none" {
            selectedLimitations = selectedLimitations == ["none"] ? [] : ["none"]
            return
        }
        selectedLimitations.remove("none")
        if selectedLimitations.contains(limitation) {
            selectedLimitations.remove(limitation)
        } else {
            selectedLimitations.insert(limitation)
        }
    }

    func submitOnboarding() async -> Bool {
        guard validateCurrentStep() else { return false }
        guard let repository else {
            errorMessage = "App environment is not ready."
            return false
        }

        isSubmitting = true
        errorMessage = nil
        defer { isSubmitting = false }

        let profileRequest = ProfileUpdateRequest(
            fullName: appState?.currentUser?.profile?.fullName,
            age: appState?.currentUser?.profile?.age,
            heightCM: appState?.currentUser?.profile?.heightCM,
            weightKG: appState?.currentUser?.profile?.weightKG,
            trainingLevel: selectedTrainingLevel,
            primaryGoal: selectedGoal,
            injuries: appState?.currentUser?.profile?.injuries ?? [],
            notes: "preferred_workout_days_per_week=\(trainingDaysPerWeek)",
            trainingStyle: selectedTrainingStyle,
            lifestyleType: selectedLifestyleType,
            sittingHoursPerDay: selectedLifestyleType == nil ? nil : sittingHoursPerDay,
            trainingHistory: selectedTrainingHistory,
            monthsInactive: selectedTrainingHistory == "returning_after_break" ? monthsInactive : nil,
            movementLimitations: movementLimitations,
            painAreas: painAreas,
            painMovements: painMovements
        )

        do {
            _ = try await repository.updateProfile(profileRequest)
            _ = try await repository.updateEquipment(
                EquipmentUpdateRequest(equipmentTypes: Array(selectedEquipment).sorted())
            )
            let user = try await repository.fetchCurrentUser()
            appState?.applyAuthenticatedUser(user)
            return true
        } catch {
            #if DEBUG
            print("Onboarding submit error: \(error)")
            #endif
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to complete onboarding."
            return false
        }
    }

    private func validateCurrentStep() -> Bool {
        switch currentStep {
        case .goal:
            return true
        case .trainingLevel:
            return true
        case .lifestyle, .trainingHistory, .limitations:
            return true
        case .trainingStyle:
            return true
        case .schedule:
            if !(1...7).contains(trainingDaysPerWeek) {
                errorMessage = "Choose between 1 and 7 training days."
                return false
            }
            return true
        case .equipment:
            if selectedEquipment.isEmpty {
                errorMessage = "Pick at least one equipment option."
                return false
            }
            return true
        case .safety:
            if !acceptedSafetyDisclaimer {
                errorMessage = "Please accept the safety disclaimer to continue."
                return false
            }
            return true
        }
    }

    private func hydrateFromCurrentUser(_ user: CurrentUserResponse?) {
        guard let user else { return }
        selectedGoal = user.profile?.primaryGoal ?? selectedGoal
        selectedTrainingLevel = user.profile?.trainingLevel ?? selectedTrainingLevel
        selectedTrainingStyle = user.profile?.trainingStyle ?? selectedTrainingStyle
        selectedLifestyleType = user.profile?.lifestyleType
        sittingHoursPerDay = user.profile?.sittingHoursPerDay ?? sittingHoursPerDay
        selectedTrainingHistory = user.profile?.trainingHistory
        monthsInactive = user.profile?.monthsInactive ?? monthsInactive
        selectedLimitations = Set(user.profile?.movementLimitations ?? [])
        if let notes = user.profile?.notes,
           let days = notes.components(separatedBy: "=").last,
           let value = Int(days.trimmingCharacters(in: .whitespacesAndNewlines)),
           (1...7).contains(value) {
            trainingDaysPerWeek = value
        }
        if !user.equipmentTypes.isEmpty {
            selectedEquipment = Set(user.equipmentTypes)
        }
    }

    private var movementLimitations: [String] {
        selectedLimitations
            .filter { $0 != "none" }
            .sorted()
    }

    private var painAreas: [String] {
        let mapping = [
            "shoulder_overhead": "shoulder",
            "lower_back_sensitive": "lower_back",
            "knee_discomfort": "knee",
            "wrist_pressure": "wrist",
            "hip_mobility_limitation": "hip",
        ]
        return movementLimitations.compactMap { mapping[$0] }.sorted()
    }

    private var painMovements: [String] {
        let mapping = [
            "shoulder_overhead": "overhead_press",
            "lower_back_sensitive": "unsupported_hinge_or_row",
            "knee_discomfort": "squat_or_lunge",
            "wrist_pressure": "loaded_wrist_extension",
            "hip_mobility_limitation": "deep_hip_flexion",
        ]
        return movementLimitations.compactMap { mapping[$0] }.sorted()
    }
}

struct OnboardingOption: Identifiable, Hashable {
    let id: String
    let title: String
    let subtitle: String
}
