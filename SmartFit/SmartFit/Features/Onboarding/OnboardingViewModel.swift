import Combine
import Foundation

@MainActor
final class OnboardingViewModel: ObservableObject {
    enum Step: Int, CaseIterable {
        case goal
        case trainingLevel
        case schedule
        case equipment
        case safety

        var title: String {
            switch self {
            case .goal: "Your Goal"
            case .trainingLevel: "Training Level"
            case .schedule: "Weekly Schedule"
            case .equipment: "Available Equipment"
            case .safety: "Safety First"
            }
        }
    }

    @Published var currentStep: Step = .goal
    @Published var selectedGoal = "general_health"
    @Published var selectedTrainingLevel = "beginner"
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

    func submitOnboarding() async {
        guard validateCurrentStep() else { return }
        guard let repository else {
            errorMessage = "App environment is not ready."
            return
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
            notes: "preferred_workout_days_per_week=\(trainingDaysPerWeek)"
        )

        do {
            _ = try await repository.updateProfile(profileRequest)
            _ = try await repository.updateEquipment(
                EquipmentUpdateRequest(equipmentTypes: Array(selectedEquipment).sorted())
            )
            let user = try await repository.fetchCurrentUser()
            appState?.applyAuthenticatedUser(user)
        } catch {
            #if DEBUG
            print("Onboarding submit error: \(error)")
            #endif
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to complete onboarding."
        }
    }

    private func validateCurrentStep() -> Bool {
        switch currentStep {
        case .goal:
            return true
        case .trainingLevel:
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
}

struct OnboardingOption: Identifiable, Hashable {
    let id: String
    let title: String
    let subtitle: String
}
