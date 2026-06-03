import Combine
import Foundation

@MainActor
final class GenerateWorkoutViewModel: ObservableObject {
    @Published var selectedWorkoutSplit: String = "full_body"
    @Published var selectedFocusMuscle: String? = "let_ai_choose"
    @Published var availableTimeMinutes: Int = 60
    @Published var selectedEquipment: Set<String> = []
    @Published var generationMode: String = "auto"
    @Published var avoidExercisesText = ""
    @Published var userNote = ""
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var generatedWorkout: WorkoutPlanResponse?

    let workoutDate: String
    let readiness: ReadinessResponse?

    private let workoutRepository: WorkoutRepository

    init(
        workoutDate: String,
        readiness: ReadinessResponse?,
        initialEquipment: [String],
        initialWorkoutSplit: String = "full_body",
        initialFocusMuscle: String? = "let_ai_choose",
        initialAvailableTimeMinutes: Int = 60,
        initialGenerationMode: String = "auto",
        initialAvoidExercisesText: String = "",
        initialUserNote: String = "",
        workoutRepository: WorkoutRepository
    ) {
        self.workoutDate = workoutDate
        self.readiness = readiness
        self.selectedEquipment = Set(initialEquipment)
        self.selectedWorkoutSplit = initialWorkoutSplit
        self.selectedFocusMuscle = initialFocusMuscle
        self.availableTimeMinutes = initialAvailableTimeMinutes
        self.generationMode = initialGenerationMode
        self.avoidExercisesText = initialAvoidExercisesText
        self.userNote = initialUserNote
        self.workoutRepository = workoutRepository
    }

    func generateWorkout() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let request = GenerateWorkoutRequest(
                date: workoutDate,
                workoutSplit: selectedWorkoutSplit,
                focusMuscle: selectedFocusMuscle == "let_ai_choose" ? nil : selectedFocusMuscle,
                availableTimeMinutes: availableTimeMinutes,
                equipment: Array(selectedEquipment),
                avoidExercises: parseAvoidExercises(),
                userNote: userNote.nilIfBlank,
                generationMode: generationMode
            )
            generatedWorkout = try await workoutRepository.generateWorkout(request)
        } catch {
            errorMessage = mapError(error)
        }
    }

    func resetError() {
        errorMessage = nil
    }

    func parseAvoidExercises() -> [String] {
        avoidExercisesText
            .split(whereSeparator: { $0 == "," || $0 == "\n" })
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    }

    private func mapError(_ error: Error) -> String {
        guard let apiError = error as? APIError else {
            return (error as? LocalizedError)?.errorDescription ?? "Unable to generate workout."
        }

        switch apiError {
        case let .server(code, _):
            switch code {
            case "AI_LIMIT_REACHED":
                return "AI limit reached for today. Try rule-based mode or come back tomorrow."
            case "READINESS_NOT_FOUND":
                return "Please calculate today’s readiness before generating a workout."
            case "WORKOUT_UNSAFE_GENERATION_BLOCKED":
                return "Workout generation was blocked for safety reasons. Adjust your inputs and try again."
            case "WORKOUT_GENERATION_FAILED":
                return "Unable to build a workout right now. Please try again."
            default:
                return apiError.errorDescription ?? "Unable to generate workout."
            }
        default:
            return apiError.errorDescription ?? "Unable to generate workout."
        }
    }
}

private extension String {
    var nilIfBlank: String? {
        let trimmed = trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
}
