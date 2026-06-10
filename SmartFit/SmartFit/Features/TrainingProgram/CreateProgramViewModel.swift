import Foundation
import Combine

@MainActor
final class CreateProgramViewModel: ObservableObject {
    @Published var goal = "muscle_gain"
    @Published var trainingStyle = "balanced"
    @Published var durationWeeks = 6
    @Published var daysPerWeek = 4
    @Published var sessionDurationMinutes = 60
    @Published var preferredSplit = "upper_lower"
    @Published var focusAreas: Set<String> = []
    @Published var isCreating = false
    @Published var errorMessage: String?

    let repository: ProgramRepositoryProtocol
    let equipment: [String]
    let onCreated: (CreateProgramResponse) -> Void

    init(
        repository: ProgramRepositoryProtocol,
        equipment: [String],
        onCreated: @escaping (CreateProgramResponse) -> Void
    ) {
        self.repository = repository
        self.equipment = equipment
        self.onCreated = onCreated
    }

    func createProgram() async -> Bool {
        isCreating = true
        errorMessage = nil
        defer { isCreating = false }

        do {
            let request = CreateProgramRequest(
                goal: goal,
                durationWeeks: durationWeeks,
                daysPerWeek: daysPerWeek,
                sessionDurationMinutes: sessionDurationMinutes,
                preferredSplit: preferredSplit,
                trainingStyle: trainingStyle,
                focusAreas: Array(focusAreas).sorted(),
                generationMode: "auto",
                generationStrategy: "full_program"
            )
            let response = try await repository.createProgram(request)
            onCreated(response)
            return true
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "Unable to create program."
            return false
        }
    }
}
